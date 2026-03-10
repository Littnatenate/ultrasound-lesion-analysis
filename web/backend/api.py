"""
FastAPI backend for SonoClarity.
Wraps the Detectron2 analyzer, heatmap generator, and report exporters.
"""
import os
import sys
from pathlib import Path

# IMPORTANT: Force Python to recognize the current directory (web/backend) as an importable module
# This ensures Docker deployments can find `analyzer.py` and `heatmap.py` regardless of the CWD.
CURRENT_DIR = Path(__file__).parent.resolve()
if str(CURRENT_DIR) not in sys.path:
    sys.path.insert(0, str(CURRENT_DIR))

# Import core modules
# NOTE: These are imported locally inside lifespan to avoid model loading blocking startup
import io
import csv
import base64
import tempfile
import numpy as np
import cv2
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

# ── Globals ──────────────────────────────────────────────────────────────
analyzer_instance = None
last_analysis = {}  # Store the last analysis results for heatmap/export


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load the model once on startup."""
    global analyzer_instance
    print("⏳ Loading Detectron2 model...")
    from analyzer import Analyzer
    analyzer_instance = Analyzer(use_gpu=False)
    print("✅ Model loaded and ready!")
    yield
    print("🛑 Shutting down.")


app = FastAPI(title="SonoClarity API", lifespan=lifespan)

# Allow all origins so the public Vercel frontend can call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _img_to_base64(img: np.ndarray) -> str:
    """Encode a BGR numpy image as base64 JPEG."""
    _, buf = cv2.imencode(".jpg", img, [cv2.IMWRITE_JPEG_QUALITY, 92])
    return base64.b64encode(buf.tobytes()).decode("utf-8")


def _masks_to_list(masks):
    """Convert numpy masks to a serializable format (list of base64 PNGs)."""
    if masks is None:
        return []
    encoded = []
    for m in masks:
        mask_uint8 = (m.astype(np.uint8)) * 255
        _, buf = cv2.imencode(".png", mask_uint8)
        encoded.append(base64.b64encode(buf.tobytes()).decode("utf-8"))
    return encoded


# ── Endpoints ────────────────────────────────────────────────────────────

@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": analyzer_instance is not None}


@app.post("/analyze")
async def analyze(
    image: UploadFile = File(...),
    age: int = Form(...),
    site: str = Form("Breast"),
):
    """Run Detectron2 inference on the uploaded image."""
    if analyzer_instance is None:
        raise HTTPException(503, "Model not loaded yet")
    
    # Save uploaded file to temp
    contents = await image.read()
    suffix = os.path.splitext(image.filename or "upload.jpg")[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(contents)
        tmp_path = tmp.name
    
    try:
        vis_img, results_list, masks, scores = analyzer_instance.analyze_image(tmp_path, age)
        
        # Store for later heatmap/export calls
        last_analysis["vis_img"] = vis_img
        last_analysis["results_list"] = results_list
        last_analysis["masks"] = masks
        last_analysis["scores"] = scores
        last_analysis["age"] = age
        last_analysis["site"] = site
        last_analysis["image_path"] = tmp_path
        
        # Determine overall recommendation
        doctor_yes = any(r["label"] == "Yes" for r in results_list)
        
        return {
            "vis_img_b64": _img_to_base64(vis_img),
            "results": results_list,
            "see_doctor": doctor_yes,
            "num_lesions": len(results_list),
            "masks_b64": _masks_to_list(masks),
        }
    except Exception as e:
        raise HTTPException(500, f"Analysis failed: {str(e)}")


@app.post("/heatmap")
async def heatmap():
    """Generate a heatmap overlay on the last analyzed image."""
    if last_analysis.get("vis_img") is None:
        raise HTTPException(400, "No analysis results available. Run /analyze first.")
    
    from heatmap import generate_heatmap_overlay
    
    heatmap_img = generate_heatmap_overlay(
        last_analysis["vis_img"],
        last_analysis["masks"],
        last_analysis["scores"],
        results_list=last_analysis["results_list"],
    )
    
    return {"heatmap_b64": _img_to_base64(heatmap_img)}


@app.post("/export/pdf")
async def export_pdf():
    """Generate and return a PDF report."""
    if last_analysis.get("vis_img") is None:
        raise HTTPException(400, "No analysis results available.")
    
    from pdf_report import generate_pdf_report
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp_path = tmp.name
    
    meta = {
        "image_path": last_analysis.get("image_path", ""),
        "age": last_analysis.get("age", 0),
        "site": last_analysis.get("site", "Breast"),
    }
    
    success, msg = generate_pdf_report(
        last_analysis["vis_img"],
        last_analysis["results_list"],
        meta,
        tmp_path,
    )
    
    if not success:
        raise HTTPException(500, f"PDF generation failed: {msg}")
    
    return FileResponse(
        tmp_path,
        media_type="application/pdf",
        filename="ultrasound_report.pdf",
    )


@app.post("/export/csv")
async def export_csv():
    """Generate and return a CSV log."""
    if not last_analysis.get("results_list"):
        raise HTTPException(400, "No analysis results available.")
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Lump", "Height_cm", "Width_cm", "Area_cm2", "H/W_Ratio", "Circularity", "Risk_Prob", "See_Doctor"])
    
    for i, r in enumerate(last_analysis["results_list"]):
        writer.writerow([
            f"L{i+1}",
            f"{r['h_cm']:.2f}",
            f"{r['w_cm']:.2f}",
            f"{r['area_cm2']:.2f}",
            f"{r['ratio']:.2f}",
            f"{r.get('circularity', 0):.2f}",
            f"{r['prob']:.2f}" if r['prob'] is not None else "N/A",
            r['label'],
        ])
    
    csv_bytes = output.getvalue().encode("utf-8")
    return Response(
        content=csv_bytes,
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=analysis_log.csv"},
    )


@app.post("/export/png")
async def export_png():
    """Return the annotated visualization image as PNG."""
    if last_analysis.get("vis_img") is None:
        raise HTTPException(400, "No analysis results available.")
    
    _, buf = cv2.imencode(".png", last_analysis["vis_img"])
    return Response(
        content=buf.tobytes(),
        media_type="image/png",
        headers={"Content-Disposition": "attachment; filename=analysis_result.png"},
    )


# ── Serve React build in production ─────────────────────────────────────
frontend_dist = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")
if os.path.isdir(frontend_dist):
    app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")

import os
import json
import math
import cv2
import numpy as np
import torch
import projects.PointRend.point_rend as point_rend
import tkinter as tk
import ttkbootstrap as ttk
from ttkbootstrap.constants import *
import csv
import matplotlib.pyplot as plt
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk
from datetime import datetime
from detectron2.config import get_cfg
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.structures import BoxMode
from detectron2.data import DatasetCatalog, MetadataCatalog
from detectron2.utils.visualizer import Visualizer, ColorMode

# ============================================================
# CONSTANTS / PATHS
# ============================================================

PIXELS_PER_CM = 101.54

EXPORT_DIR = r"C:\Breast cancer project (new)\exports"
os.makedirs(EXPORT_DIR, exist_ok=True)

CSV_LOG_PATH = r"C:\Breast cancer project (new)\results_log.csv"

THRESHOLD = 0.40
W_RATIO = 1.717809
W_AREA = 0.109624
W_IRREG = 2.373295
W_AGE = 0.048660
B_BIAS = -4.572522

ACCENT_COLOR = "#1877f2"
ERROR_COLOR = "#d93025"
OK_COLOR = "#2e7d32"


# ============================================================
# HELPER FUNCTIONS: RISK LAYER + CSV / PNG EXPORT
# ============================================================

def predict_see_doctor_prob(ratio, area_cm2, boundary_score, age):
    if ratio is None or area_cm2 is None or boundary_score is None or age is None:
        return None, "Unknown"

    irregularity = 1.0 - boundary_score
    score = (
        W_RATIO * ratio
        + W_AREA * area_cm2
        + W_IRREG * irregularity
        + W_AGE * age
        + B_BIAS
    )
    prob = 1.0 / (1.0 + math.exp(-score))
    label = "Yes" if prob >= THRESHOLD else "No"
    return float(prob), label


def export_canvas_png(canvas, image_path):
    base = os.path.splitext(os.path.basename(image_path))[0]
    out_path = os.path.join(EXPORT_DIR, f"{base}_report.png")
    cv2.imwrite(out_path, canvas)
    print(f"[Saved] PNG report -> {out_path}", flush=True)


def append_results_to_csv(image_path, age, results_list):

    if not results_list:
        print("[Warn] No lumps to save for CSV.", flush=True)
        return

    file_exists = os.path.exists(CSV_LOG_PATH)
    headers = [
        "timestamp", "image_path", "age", "lump_id",
        "ratio", "area_cm2", "boundary_score", "irregularity",
        "prob_see_doctor", "see_doctor_label", "threshold_used"
    ]

    with open(CSV_LOG_PATH, "a", newline="") as f:
        w = csv.writer(f)
        if not file_exists:
            w.writerow(headers)

        for r in results_list:
            b = r["boundary_score"]
            irregularity = (1.0 - b) if b is not None else None
            w.writerow([
                datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                image_path,
                age,
                r["lump_id"],
                r["ratio"],
                r["area_cm2"],
                b,
                irregularity,
                r["prob"],
                r["label"],
                THRESHOLD
            ])

    print(f"[Saved] CSV row(s) -> {CSV_LOG_PATH}", flush=True)


# ============================================================
# DATASET / MODEL LOADING
# ============================================================

def get_lumps_dicts(img_dir):
    candidate_jsons = ["Training_json.json", "Validation_json.json"]
    json_file = None
    for name in candidate_jsons:
        path = os.path.join(img_dir, name)
        if os.path.exists(path):
            json_file = path
            break

    if json_file is None:
        print(f"[WARN] No JSON annotation found in {img_dir}", flush=True)
        return []

    with open(json_file) as f:
        imgs_anns = json.load(f)

    dataset_dicts = []
    for idx, v in enumerate(imgs_anns.values()):
        filename = os.path.join(img_dir, v["filename"])
        if not os.path.exists(filename):
            continue

        record = {
            "file_name": filename,
            "image_id": idx,
            "height": 0,
            "width": 0,
            "annotations": [],
        }

        regions = v.get("regions", [])
        if isinstance(regions, dict):
            regions = list(regions.values())

        for anno in regions:
            sa = anno.get("shape_attributes", {})
            if sa.get("name") != "polygon":
                continue

            px = sa.get("all_points_x", [])
            py = sa.get("all_points_y", [])
            if not px or not py:
                continue

            poly = [p for x in zip(px, py) for p in x]

            record["annotations"].append(
                {
                    "bbox": [min(px), min(py), max(px), max(py)],
                    "bbox_mode": BoxMode.XYXY_ABS,
                    "segmentation": [poly],
                    "category_id": 0,
                }
            )

        dataset_dicts.append(record)

    print(f"[INFO] Loaded {len(dataset_dicts)} records from {img_dir}", flush=True)
    return dataset_dicts


DatasetCatalog.clear()
MetadataCatalog.clear()

train_dir = r"C:\Breast cancer project (new)\Dataset\train"
DatasetCatalog.register("lumps_train", lambda: get_lumps_dicts(train_dir))
MetadataCatalog.get("lumps_train").set(thing_classes=["lump"])
lumps_metadata = MetadataCatalog.get("lumps_train")


cfg = get_cfg()
cfg.MODEL.DEVICE = "cpu"

point_rend.add_pointrend_config(cfg)
cfg.merge_from_file(
    model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml")
)
cfg.merge_from_file(r"C:\Users\524yu\Dev\Breast-Cancer-Analysis\projects\PointRend\configs\InstanceSegmentation\pointrend_rcnn_R_50_FPN_3x_coco.yaml")

cfg.DATASETS.TRAIN = ("lumps_train",)
cfg.DATASETS.TEST = ()
cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1
cfg.MODEL.POINT_HEAD.NUM_CLASSES = 1
cfg.MODEL.WEIGHTS = os.path.join("output", "2000_iterations.pth")
cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.7

predictor = DefaultPredictor(cfg)
print("[OK] Inference model ready.", flush=True)


# ============================================================
# BUILD CANVAS (Result image + clinical card)
# ============================================================

def build_canvas(base_img, rows):
    """
    Build composite result canvas:
    - Left: enlarged ultrasound image (with overlay)
    - Right: clinical text card
    """
    font = cv2.FONT_HERSHEY_SIMPLEX
    font_scale = 0.55
    thickness = 1

    # ----- enlarge only the ultrasound image -----
    h0, w0, _ = base_img.shape
    IMAGE_SCALE = 1.25   # tweak 1.1–1.3 if you want it a bit smaller/bigger

    new_w = int(w0 * IMAGE_SCALE)
    new_h = int(h0 * IMAGE_SCALE)
    base_img_big = cv2.resize(base_img, (new_w, new_h), interpolation=cv2.INTER_CUBIC)
    h_img, w_img = base_img_big.shape[:2]

    HEADER_HEIGHT = 70
    bg_color = (255, 255, 255)
    header_color = (235, 235, 235)

    # -------------------- FIRST PASS: measure text --------------------
    label_color = (40, 40, 40)
    value_color = (80, 80, 80)

    label_col_width = 0
    max_row_width = 0
    line_heights = []

    for label, value, is_header in rows:
        if label == "" and value == "":
            (w, h), _ = cv2.getTextSize("A", font, font_scale, thickness)
            line_heights.append(h)
            continue

        if is_header or value == "":
            (w, h), _ = cv2.getTextSize(label, font, font_scale, thickness)
            max_row_width = max(max_row_width, w)
            line_heights.append(h)
        else:
            label_text = label + ":"
            (w_label, h_label), _ = cv2.getTextSize(
                label_text, font, font_scale, thickness
            )
            (w_val, h_val), _ = cv2.getTextSize(
                " " + value, font, font_scale, thickness
            )
            label_col_width = max(label_col_width, w_label)
            row_width = w_label + 20 + w_val
            max_row_width = max(max_row_width, row_width)
            line_heights.append(max(h_label, h_val))

    line_h = max(line_heights) if line_heights else 22
    line_gap = int(line_h * 1.4)
    n_lines = len(rows)
    total_text_height = n_lines * line_gap

    card_pad_x, card_pad_y = 32, 24
    min_side_panel_width = 580

    card_width = max(max_row_width + 2 * card_pad_x, 420)
    card_height = total_text_height + 2 * card_pad_y

    BOTTOM_PAD = 30
    cards_h = max(h_img, card_height)
    side_panel_width = max(min_side_panel_width, card_width + 40)

    image_y = HEADER_HEIGHT + 30
    card_x = w_img + 30
    card_y = image_y

    img_bottom = image_y + cards_h + BOTTOM_PAD
    card_bottom = card_y + cards_h + BOTTOM_PAD

    canvas_h = max(img_bottom, card_bottom)
    canvas_w = w_img + side_panel_width

    canvas = np.full((canvas_h, canvas_w, 3), bg_color, dtype=np.uint8)

    # -------------------- HEADER --------------------
    cv2.rectangle(canvas, (0, 0), (canvas_w, HEADER_HEIGHT), header_color, -1)
    cv2.putText(
        canvas,
        "Ultrasound Lesion Analysis",
        (30, 45),
        cv2.FONT_HERSHEY_COMPLEX,
        1.3,
        (60, 60, 60),
        2,
        cv2.LINE_AA,
    )

    # -------------------- IMAGE --------------------
    canvas[image_y:image_y + h_img, :w_img] = base_img_big
    cv2.rectangle(
        canvas,
        (0, image_y),
        (w_img - 1, image_y + cards_h - 1),
        (210, 210, 210),
        2,
    )

    sep_x = w_img + 10
    cv2.line(
        canvas,
        (sep_x, image_y),
        (sep_x, image_y + cards_h),
        (210, 210, 210),
        1,
    )

    # -------------------- RIGHT-HAND CARD --------------------
    cv2.rectangle(
        canvas,
        (card_x, card_y),
        (card_x + card_width, card_y + cards_h),
        (245, 245, 245),
        -1,
    )
    cv2.rectangle(
        canvas,
        (card_x, card_y),
        (card_x + card_width, card_y + cards_h),
        (210, 210, 210),
        1,
    )

    base_x_label = card_x + card_pad_x
    base_x_value = card_x + card_pad_x + label_col_width + 20
    ty = card_y + card_pad_y + line_h

    for label, value, is_header in rows:
        if label == "" and value == "":
            ty += line_gap
            continue

        if is_header or value == "":
            cv2.putText(
                canvas,
                label,
                (base_x_label, ty),
                font,
                font_scale,
                label_color,
                2,
                cv2.LINE_AA,
            )
            ty += int(line_gap * 1.4)
            continue

        cv2.putText(
            canvas,
            label + ":",
            (base_x_label, ty),
            font,
            font_scale,
            label_color,
            thickness,
            cv2.LINE_AA,
        )
        cv2.putText(
            canvas,
            value,
            (base_x_value, ty),
            font,
            font_scale,
            value_color,
            thickness,
            cv2.LINE_AA,
        )
        ty += line_gap

    return canvas


# ============================================================
# CORE ANALYSIS (return canvas + results for GUI)
# ============================================================

def run_model_on_image(image_path, age):
    im = cv2.imread(image_path)
    if im is None:
        raise ValueError(f"Could not read image: {image_path}")

    outputs = predictor(im)
    instances = outputs["instances"].to("cpu")

    masks = instances.pred_masks.cpu().numpy() if len(instances) > 0 else None
    boxes = instances.pred_boxes.tensor.numpy() if len(instances) > 0 else None

    sorted_idx = []
    if masks is not None:
        sorted_idx = sorted(
            range(len(instances)),
            key=lambda i: int(masks[i].sum()),
            reverse=True,
        )[:2]  # top 2 lumps

    v = Visualizer(
        im[:, :, ::-1],
        metadata=lumps_metadata,
        scale=0.5,
        instance_mode=ColorMode.IMAGE_BW,
    )
    vis_img = v.draw_instance_predictions(instances).get_image()[:, :, ::-1].copy()

    rows = [("Age", f"{int(age)}", False), ("", "", False)]
    results_for_csv = []

    if masks is not None and len(sorted_idx) > 0:
        for rank, i in enumerate(sorted_idx):
            lump_id = f"L{rank + 1}"

            x1, y1, x2, y2 = boxes[i]
            width_px = x2 - x1
            height_px = y2 - y1
            if width_px <= 0 or height_px <= 0:
                continue

            ratio = float(height_px / width_px)

            mask_i = masks[i].astype("uint8")
            area_px = int(mask_i.sum())

            contours, _ = cv2.findContours(
                mask_i, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
            )

            boundary_score = None
            boundary_label = "N/A"
            if len(contours) > 0:
                cnt = contours[0]
                peri = cv2.arcLength(cnt, True)
                c_area = cv2.contourArea(cnt)
                if peri > 0 and c_area > 0:
                    circularity = 4.0 * math.pi * c_area / (peri ** 2)
                    boundary_score = max(0.0, min(1.0, circularity))

                    if boundary_score >= 0.8:
                        boundary_label = "Smooth"
                    elif boundary_score >= 0.6:
                        boundary_label = "Mod. irregular"
                    else:
                        boundary_label = "Irregular"

            height_cm = height_px / PIXELS_PER_CM
            width_cm = width_px / PIXELS_PER_CM
            area_cm2 = float(area_px / (PIXELS_PER_CM ** 2))

            if boundary_score is not None:
                prob, lbl = predict_see_doctor_prob(
                    ratio, area_cm2, boundary_score, age
                )
            else:
                prob, lbl = None, "Unknown"

            results_for_csv.append(
                {
                    "lump_id": lump_id,
                    "ratio": ratio,
                    "area_cm2": area_cm2,
                    "boundary_score": boundary_score,
                    "prob": prob,
                    "label": lbl,
                }
            )

            rows.append((lump_id + ":", "", True))
            rows.append(("Height/Width", f"{ratio:.2f}", False))
            rows.append(
                (
                    "Dimensions",
                    f"{height_cm:.2f} cm (H) x {width_cm:.2f} cm (W)",
                    False,
                )
            )
            rows.append(("Size", f"{area_cm2:.2f} cm^2", False))
            if boundary_score is not None:
                rows.append(
                    (
                        "Boundary",
                        f"{boundary_label} (circularity = {boundary_score:.2f})",
                        False,
                    )
                )
                rows.append(
                    (
                        "See doctor",
                        f"{lbl} (p = {prob:.2f})",
                        False,
                    )
                )
            else:
                rows.append(("Boundary", "N/A", False))
                rows.append(("See doctor", "Unknown", False))

            rows.append(("", "", False))
    else:
        rows.append(("No lump detected", "", True))

    canvas = build_canvas(vis_img, rows)
    return canvas, results_for_csv


# ============================================================
# TKINTER GUI – TWO TABS (INTAKE + RESULT)
# ============================================================

def run_gui():
    root = ttk.Window(themename="flatly")
    root.title("Ultrasound Lesion Analysis")

    # --- FULL SCREEN ---
    w = root.winfo_screenwidth()
    h = root.winfo_screenheight()
    root.geometry(f"{w}x{h}+0+0")

    # (optional) remove minsize so it doesn't fight your full-screen sizing
    # root.minsize(1200, 700)

    notebook = ttk.Notebook(root, bootstyle="info")
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    intake_tab = ttk.Frame(notebook)
    result_tab = ttk.Frame(notebook)
    notebook.add(intake_tab, text="Patient Intake")
    notebook.add(result_tab, text="Analysis Result")

    # Shared state
    image_path_var = tk.StringVar(value="")
    site_var = tk.StringVar(value="Breast")
    case_id_var = tk.StringVar(value="")
    current_canvas = {"img": None}
    current_results = {"rows": None}
    current_meta = {"image_path": None, "age": None, "site": None, "case_id": None}

    preview_state = {"pil": None, "tk": None}


    # ---------------- Patient Intake Tab ----------------
    intake_container = ttk.Frame(intake_tab)
    intake_container.pack(fill="both", expand=True, padx=20, pady=20)

    # Accent strip on intake card
    ttk.Frame(intake_container, bootstyle="primary", height=3).pack(fill="x", side="top")

    # Left panel
    left_panel = ttk.Frame(intake_container, padding=30)
    left_panel.pack(side="left", fill="both", expand=True)

    ttk.Label(
        left_panel,
        text="Patient Analysis",
        font=("Segoe UI Semibold", 20),
        bootstyle="primary"
    ).pack(anchor="w")

    ttk.Label(
        left_panel,
        text="Fill in clinical details and select an ultrasound scan to begin.",
        font=("Segoe UI", 9),
        bootstyle="secondary"
    ).pack(anchor="w", pady=(0, 18))

    def required_label(parent, text):
        row = ttk.Frame(parent)
        row.pack(fill="x", anchor="w")
        ttk.Label(
            row,
            text=text + " ",
            font=("Segoe UI Bold", 9),
            bootstyle="secondary"
        ).pack(side="left")
        ttk.Label(
            row,
            text="*",
            font=("Segoe UI Bold", 9),
            bootstyle="danger"
        ).pack(side="left")

    # Age (required)
    required_label(left_panel, "PATIENT AGE (YEARS)")
    age_entry = ttk.Entry(
        left_panel,
        font=("Segoe UI", 11),
        bootstyle="primary"
    )
    age_entry.pack(fill="x", pady=(5, 6), ipady=6)

    age_help_label = ttk.Label(
        left_panel,
        text="Enter a number (e.g., 45).",
        font=("Segoe UI", 8),
        bootstyle="secondary"
    )
    age_help_label.pack(anchor="w", pady=(0, 12))

    # Case ID (optional)
    ttk.Label(
        left_panel,
        text="CASE / STUDY ID (optional)",
        font=("Segoe UI Bold", 9),
        bootstyle="secondary"
    ).pack(anchor="w")
    case_entry = ttk.Entry(
        left_panel,
        textvariable=case_id_var,
        font=("Segoe UI", 11),
        bootstyle="primary"
    )
    case_entry.pack(fill="x", pady=(5, 14), ipady=6)

    # Examination site
    ttk.Label(
        left_panel,
        text="EXAMINATION SITE",
        font=("Segoe UI Bold", 9),
        bootstyle="secondary"
    ).pack(anchor="w")

    site_combo = ttk.Combobox(
        left_panel,
        textvariable=site_var,
        state="readonly",
        font=("Segoe UI", 10),
        values=["Breast", "Axilla"],
    )
    site_combo.pack(fill="x", pady=(5, 14), ipady=2)

    # Ultrasound scan (required)
    required_label(left_panel, "ULTRASOUND SCAN")

    file_row = ttk.Frame(left_panel)
    file_row.pack(fill="x", pady=(5, 4))

    def select_image():
        path = filedialog.askopenfilename(
            initialdir=r"C:\Breast cancer project (new)\Dataset\Val",
            filetypes=[
                ("Image files", "*.jpg *.JPG *.jpeg *.JPEG *.png *.PNG *.bmp *.BMP *.tif *.TIF *.tiff *.TIFF"),
                ("All files", "*.*"),
            ],
        )
        if not path:
            return

        image_path_var.set(path)

        try:
            img = Image.open(path)
            preview_original_img["pil"] = img  # keep original PIL image
            resize_preview_image()  # this will create the tk image and update label
        except Exception as e:
            messagebox.showerror("Image Error", f"Could not open image:\n{e}")
            preview_original_img["pil"] = None
            preview_original_img["tk"] = None
            preview_label.configure(image="")
            preview_label.configure(text="No Image Selected")
            preview_label._image_ref = None
            return

        update_run_button_state()

    file_btn = ttk.Button(
        file_row,
        text="Choose File…",
        command=select_image,
        bootstyle="secondary-outline",
        cursor="hand2"
    )
    file_btn.pack(side="left")

    ttk.Label(
        file_row,
        text="  (PNG/JPG/BMP/TIF)",
        font=("Segoe UI", 8),
        bootstyle="secondary"
    ).pack(side="left")

    file_name_lbl = ttk.Label(
        left_panel,
        textvariable=image_path_var,
        font=("Segoe UI Italic", 8),
        bootstyle="secondary",
        wraplength=420,
        anchor="w",
        justify="left",
    )
    file_name_lbl.pack(anchor="w", pady=(0, 2))

    scan_help_label = ttk.Label(
        left_panel,
        text="Supported formats: PNG, JPG, BMP, TIF.",
        font=("Segoe UI", 8),
        bootstyle="secondary"
    )
    scan_help_label.pack(anchor="w", pady=(0, 12))

    # Clinical note
    ttk.Label(
        left_panel,
        text="CLINICAL NOTE (optional)",
        font=("Segoe UI Bold", 9),
        bootstyle="secondary"
    ).pack(anchor="w")

    note_text = tk.Text(
        left_panel,
        height=3,
        font=("Segoe UI", 9),
        bg="#f5f6f7",
        bd=1,
        relief="solid",
        wrap="word"
    )
    note_text.pack(fill="x", pady=(5, 14))

    status_label = ttk.Label(
        left_panel,
        text="",
        font=("Segoe UI", 9),
        bootstyle="secondary"
    )
    status_label.pack(anchor="w", pady=(0, 2))

    # Run analysis
    def on_run_analysis():
        age_str = age_entry.get().strip()
        img_path = image_path_var.get().strip()

        # final validation
        update_run_button_state()
        if str(run_button["state"]) != "normal":
            messagebox.showerror(
                "Input Error",
                "Please correct the highlighted fields before running the analysis.",
            )
            return

        age_val = float(age_str)

        run_button.config(text="Analyzing…", state="disabled", bg="#145dbf")
        status_label.config(text="Running analysis…", fg=ACCENT_COLOR)
        root.update_idletasks()

        success = False
        try:
            canvas, results_for_csv = run_model_on_image(img_path, age_val)
            success = True
        except Exception as e:
            messagebox.showerror("Analysis Error", str(e))
            status_label.config(text="Analysis failed. Please try another image.", fg=ERROR_COLOR)
        if success:
            current_canvas["img"] = canvas
            current_results["rows"] = results_for_csv
            current_meta["image_path"] = img_path
            current_meta["age"] = age_val
            current_meta["site"] = site_var.get()
            current_meta["case_id"] = case_id_var.get().strip()

            update_result_tab_image()
            update_stats_row()
            notebook.select(result_tab)

            run_button.config(text="✓ Analysis complete", bootstyle="success")
            status_label.config(text="Analysis complete.", bootstyle="success")
            root.after(
                1500,
                lambda: (
                    run_button.config(text="Run Analysis"),
                    update_run_button_state(),
                ),
            )
        else:
            run_button.config(text="Run Analysis")
            update_run_button_state()

    # Buttons row (Run + Reset)
    btns = ttk.Frame(left_panel)
    btns.pack(fill="x", pady=(6, 6))

    run_button = ttk.Button(
        btns,
        text="Run Analysis",
        command=on_run_analysis,
        bootstyle="secondary",
        cursor="hand2",
        state="disabled"
    )
    run_button.pack(side="left", fill="x", expand=True)

    def clear_form():
        age_entry.delete(0, tk.END)
        case_id_var.set("")
        site_var.set("Breast")
        note_text.delete("1.0", tk.END)
        image_path_var.set("")

        # clear preview state so <Configure> won't redraw the old image
        preview_original_img["pil"] = None
        preview_original_img["tk"] = None

        preview_label.configure(image="")
        preview_label.configure(text="No Image Selected")
        preview_label._image_ref = None

        age_help_label.config(text="Enter a number (e.g., 45).", bootstyle="secondary")
        scan_help_label.config(text="Supported formats: PNG, JPG, BMP, TIF.", bootstyle="secondary")
        
        status_label.config(text="", bootstyle="secondary")
        update_run_button_state()

    reset_btn = ttk.Button(
        btns,
        text="Reset",
        command=clear_form,
        bootstyle="light",
        cursor="hand2"
    )
    reset_btn.pack(side="left", padx=(10, 0))

    # Secondary actions
    action_frame = ttk.Frame(left_panel)
    action_frame.pack(fill="x", pady=(2, 0))

    def open_logs():
        if os.path.exists(CSV_LOG_PATH):
            os.startfile(CSV_LOG_PATH)
        else:
            messagebox.showinfo("CSV Log", "No CSV log found yet.")

    ttk.Button(
        action_frame,
        text="View Logs",
        command=open_logs,
        bootstyle="link",
        cursor="hand2",
    ).pack(side="left")

    # Required-field validation + button enable
    def update_run_button_state(*args):
        age_str = age_entry.get().strip()
        img_path = image_path_var.get().strip()

        valid = True

        # age validation
        if not age_str:
            valid = False
            age_help_label.config(text="Age is required.", bootstyle="danger")
            
        else:
            try:
                float(age_str)
            except ValueError:
                valid = False
                age_help_label.config(text="Age must be numeric (e.g., 45).", bootstyle="danger")
                
            else:
                age_help_label.config(text="Enter a number (e.g., 45).", bootstyle="secondary")
                

        # scan validation
        if not img_path:
            valid = False
            scan_help_label.config(text="Ultrasound scan is required.", bootstyle="danger")
        else:
            scan_help_label.config(text="Supported formats: PNG, JPG, BMP, TIF.", bootstyle="secondary")

        if valid:
            run_button.config(state="normal", bootstyle="success")
            if status_label.cget("text") == "":
                status_label.config(text="Ready to analyze.", bootstyle="success")
        else:
            run_button.config(state="disabled", bootstyle="secondary")
            if "complete" not in status_label.cget("text").lower():
                status_label.config(text="", bootstyle="secondary")

    age_entry.bind("<KeyRelease>", update_run_button_state)
    image_path_var.trace_add("write", update_run_button_state)
    update_run_button_state()

    def try_enter_run(event=None):
        if str(run_button["state"]) == "normal":
            on_run_analysis()

    age_entry.bind("<Return>", try_enter_run)

    # Right panel: selected ultrasound preview (with dark frame)
    right_panel = ttk.Frame(intake_container, padding=24)
    right_panel.pack(side="right", fill="both", expand=True)

    ttk.Label(
        right_panel,
        text="Selected Ultrasound Preview",
        font=("Segoe UI Semibold", 11),
        bootstyle="primary",
        anchor="w",
    ).pack(anchor="nw", pady=(0, 8))

    preview_card = ttk.Frame(right_panel)

    preview_card.pack(fill="both", expand=True)

    # accent strip on preview card
    ttk.Frame(preview_card, bootstyle="primary", height=3).pack(fill="x", side="top")

    image_frame = ttk.Frame(preview_card, padding=10)
    image_frame.pack(fill="both", expand=True)

    preview_label = ttk.Label(
        image_frame,
        text="No Image Selected",
        font=("Segoe UI", 10),
        bootstyle="secondary",
        anchor="center"
    )
    preview_label.pack(expand=True, fill="both")

    preview_original_img = {"pil": None}

    def resize_preview_image(event=None):
        img = preview_original_img.get("pil")
        if img is None:
            return

        w = preview_label.winfo_width()
        h = preview_label.winfo_height()
        if w < 50 or h < 50:
            return

        PAD = 0  # set to 0 for biggest possible fill
        target_w = max(1, w - PAD)
        target_h = max(1, h - PAD)

        iw, ih = img.size

        # SCALE TO FILL (bigger, but will crop)
        scale = max(target_w / iw, target_h / ih)
        new_w = max(1, int(iw * scale))
        new_h = max(1, int(ih * scale))

        img_resized = img.resize((new_w, new_h), Image.LANCZOS)

        # center crop to target size
        left = (new_w - target_w) // 2
        top = (new_h - target_h) // 2
        img_cropped = img_resized.crop((left, top, left + target_w, top + target_h))

        preview_original_img["tk"] = ImageTk.PhotoImage(img_cropped)
        preview_label.configure(image=preview_original_img["tk"])
        preview_label.configure(text="")
        preview_label._image_ref = preview_original_img["tk"]

    # ---------------- Analysis Result Tab ----------------
    result_header = ttk.Frame(result_tab)
    result_header.pack(fill="x", padx=20, pady=(10, 0))

    ttk.Label(
        result_header,
        text="Analysis Result",
        font=("Segoe UI Semibold", 18),
        bootstyle="primary"
    ).pack(side="left")

    def back_to_home():
        notebook.select(intake_tab)

    ttk.Button(
        result_header,
        text="Back to Home",
        command=back_to_home,
        bootstyle="primary",
        cursor="hand2"
    ).pack(side="right", padx=(0, 10))

    # Buttons row  ✅ must be BEFORE any buttons that use btn_row
    btn_row = ttk.Frame(result_tab)
    btn_row.pack(fill="x", padx=20, pady=(10, 0))


    def save_png():
        if current_canvas["img"] is None or current_meta["image_path"] is None:
            messagebox.showinfo("Save PNG", "No analysis result to save yet.")
            return
        export_canvas_png(current_canvas["img"], current_meta["image_path"])

    def save_csv():
        if (
            current_results["rows"] is None
            or current_meta["image_path"] is None
            or current_meta["age"] is None
        ):
            messagebox.showinfo("Save CSV", "No measurements to save yet.")
            return
        append_results_to_csv(
            current_meta["image_path"],
            current_meta["age"],
            current_results["rows"],
        )

    tk.Button(
        btn_row,
        text="Save PNG",
        command=save_png,
        font=("Segoe UI", 9),
        bg="#ffffff",
        fg=ACCENT_COLOR,
        relief="solid",
        bd=1,
        cursor="hand2",
        padx=10,
        pady=4,
    ).pack(side="left", padx=(0, 6))

    tk.Button(
        btn_row,
        text="Save CSV",
        command=save_csv,
        font=("Segoe UI", 9),
        bg="#ffffff",
        fg=ACCENT_COLOR,
        relief="solid",
        bd=1,
        cursor="hand2",
        padx=10,
        pady=4,
    ).pack(side="left")

    # Key stats row
    stats_row = ttk.Frame(result_tab)
    stats_row.pack(fill="x", padx=20, pady=(8, 0))

    stats_main_label = ttk.Label(
        stats_row,
        text="No analysis run yet.",
        font=("Segoe UI", 9),
        bootstyle="secondary",
        anchor="w",
    )
    stats_main_label.pack(side="left")

    stats_size_label = ttk.Label(
        stats_row,
        text="",
        font=("Segoe UI", 9),
        bootstyle="secondary",
        anchor="w",
    )
    stats_size_label.pack(side="left", padx=(20, 0))

    stats_doctor_label = ttk.Label(
        stats_row,
        text="",
        font=("Segoe UI", 9),
        bootstyle="inverse-secondary",
        padding=(8, 2)
    )
    stats_doctor_label.pack(side="right")

    # Main result display area
    result_container = ttk.Frame(result_tab)
    result_container.pack(fill="both", expand=True, padx=20, pady=10)

    result_card = ttk.Frame(result_container)
    result_card.pack(fill="both", expand=True)

    ttk.Frame(result_card, bootstyle="primary", height=3).pack(fill="x", side="top")

    result_image_label = ttk.Label(result_card)
    result_image_label.pack(expand=True)

    # --- result image scaling ---
    def update_result_tab_image():
        if current_canvas["img"] is None:
            result_image_label.configure(text="No analysis result yet.")
            result_image_label.configure(image="")
            result_image_label._image_ref = None
            return

        canvas = current_canvas["img"]

        scale_factor = 1.4
        h, w = canvas.shape[:2]
        canvas_big = cv2.resize(
            canvas,
            (int(w * scale_factor), int(h * scale_factor)),
            interpolation=cv2.INTER_LINEAR,
        )

        canvas_rgb = cv2.cvtColor(canvas_big, cv2.COLOR_BGR2RGB)
        img_pil = Image.fromarray(canvas_rgb)
        img_tk = ImageTk.PhotoImage(img_pil)

        result_image_label.configure(image=img_tk)
        result_image_label.configure(text="")
        result_image_label._image_ref = img_tk

    # --- key stats update ---
    def update_stats_row():
        rows = current_results["rows"]
        age = current_meta["age"]
        site = current_meta["site"]
        case_id = current_meta["case_id"]

        if rows is None or age is None:
            stats_main_label.config(text="No analysis run yet.")
            stats_size_label.config(text="")
            stats_doctor_label.config(text="", bg="#f0f2f5")
            return

        info_text = f"Age: {int(age)}   |   Site: {site or 'N/A'}   |   Case ID: {case_id or 'N/A'}"
        stats_main_label.config(text=info_text)

        if not rows:
            stats_size_label.config(text="No lesion detected.")
            stats_doctor_label.config(text="See doctor: N/A", bg="#999999")
            return

        max_area = max(r["area_cm2"] for r in rows)
        max_ratio = max(r["ratio"] for r in rows)
        doctor_yes = any(r["label"] == "Yes" for r in rows)

        stats_size_label.config(
            text=f"Max lesion size: {max_area:.2f} cm²   •   Max H/W: {max_ratio:.2f}"
        )

        if doctor_yes:
            stats_doctor_label.config(
                text="See doctor: YES",
                bootstyle="inverse-danger",
            )
        else:
            stats_doctor_label.config(
                text="See doctor: NO",
                bootstyle="inverse-success",
            )

    # Footer
    ttk.Label(
        root,
        text="For Demonstration Only – Not for Clinical Decision-Making",
        font=("Segoe UI", 9),
        bootstyle="secondary",
    ).pack(side="bottom", pady=6)

    root.mainloop()

# ===================== CONFUSION MATRIX (BREAST + AXILLA) =====================

# Your two separate CSV files (with headers: Image_path, Label, Age, Site)
BREAST_CSV = r"C:\Breast cancer project (new)\Breast Excel For Confusion Matrix.csv"
AXILLA_CSV = r"C:\Breast cancer project (new)\Axilla Excel For Confusion Matrix.csv"

EVAL_THRESHOLD = THRESHOLD  # uses the same threshold as GUI (0.40)


def save_confusion_matrix_png(
    tn, fp, fn, tp,
    out_path,
    title="Confusion Matrix",
    auto_open=True
):
    cm = np.array([[tn, fp],
                   [fn, tp]], dtype=int)

    fig, ax = plt.subplots(figsize=(6, 5))
    ax.imshow(cm, interpolation="nearest", cmap="Blues")

    ax.set_title(title)  # ✅ no "(thr=0.4)"
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Actual")

    ax.set_xticks([0, 1])
    ax.set_yticks([0, 1])
    ax.set_xticklabels(["No doctor", "See doctor"])
    ax.set_yticklabels(["No doctor", "See doctor"])

    # numbers in cells
    for (i, j), val in np.ndenumerate(cm):
        ax.text(j, i, str(val), ha="center", va="center", color="black", fontsize=14)

    plt.tight_layout()
    plt.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"[Saved] Confusion matrix -> {out_path}", flush=True)

    if auto_open:
        try:
            os.startfile(out_path)
        except Exception as e:
            print(f"[Warn] Could not auto-open image: {e}", flush=True)


def evaluate_on_csv(csv_path, out_png_name, auto_open=True):
    """
    Reads a CSV (Breast/Axilla), runs the model on each image,
    saves confusion matrix PNG, prints sensitivity/specificity/accuracy.

    Expected headers: Image_path, Label, Age, Site
    Labels: see_doctor, no_doctor
    """
    y_true = []   # 1 = see_doctor, 0 = no_doctor
    y_pred = []   # 1/0

    total_rows = 0
    used_rows = 0
    skipped_rows = 0

    print(f"\n[INFO] Evaluating CSV: {csv_path}", flush=True)

    with open(csv_path, newline="", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        print("CSV headers detected:", reader.fieldnames, flush=True)

        for csv_row_num, row in enumerate(reader, start=2):
            total_rows += 1

            # Support both exact header case + lowercase fallback
            img_path = (row.get("Image_path") or row.get("image_path") or "").strip()
            label_str = (row.get("Label") or row.get("label") or "").strip().lower()
            age_raw = (row.get("Age") or row.get("age") or "").strip()

            # Validate required fields
            if not img_path:
                print(f"[SKIP] row {csv_row_num}: missing Image_path", flush=True)
                skipped_rows += 1
                continue

            if not age_raw:
                print(f"[SKIP] row {csv_row_num}: missing Age", flush=True)
                skipped_rows += 1
                continue

            try:
                age_val = float(age_raw)
            except ValueError:
                print(f"[SKIP] row {csv_row_num}: invalid Age='{age_raw}'", flush=True)
                skipped_rows += 1
                continue

            # ✅ Label mapping (see_doctor / no_doctor only)
            if label_str == "see_doctor":
                true_label = 1
            elif label_str == "no_doctor":
                true_label = 0
            else:
                print(f"[SKIP] row {csv_row_num}: unknown Label='{label_str}'", flush=True)
                skipped_rows += 1
                continue

            # Run model
            try:
                _, lesions = run_model_on_image(img_path, age_val)
            except Exception as e:
                print(f"[SKIP] row {csv_row_num}: model failed on '{img_path}' ({e})", flush=True)
                skipped_rows += 1
                continue

            # Case probability = max lesion probability
            if not lesions:
                prob = 0.0
            else:
                valid_probs = [l["prob"] for l in lesions if l.get("prob") is not None]
                prob = max(valid_probs) if valid_probs else 0.0

            pred_label = 1 if prob >= EVAL_THRESHOLD else 0

            y_true.append(true_label)
            y_pred.append(pred_label)
            used_rows += 1

            if used_rows % 5 == 0:
                print(f"Progress: evaluated {used_rows} cases...", flush=True)

    if used_rows == 0:
        print("\nNo valid rows were evaluated. Check your CSV.", flush=True)
        return

    # Confusion matrix counts
    tp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 1)
    tn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 0)
    fp = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 0 and yp == 1)
    fn = sum(1 for yt, yp in zip(y_true, y_pred) if yt == 1 and yp == 0)

    out_path = os.path.join(EXPORT_DIR, out_png_name)
    save_confusion_matrix_png(
        tn, fp, fn, tp,
        out_path,
        title="Confusion Matrix",
        auto_open=auto_open
    )

    sensitivity = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    specificity = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    accuracy = (tp + tn) / used_rows if used_rows else 0.0

    print("\n=== EVALUATION RESULTS ===")
    print(f"CSV file              : {os.path.basename(csv_path)}")
    print(f"Rows total            : {total_rows}")
    print(f"Rows evaluated        : {used_rows}")
    print(f"Rows skipped          : {skipped_rows}")
    print(f"TP = {tp}, FP = {fp}, TN = {tn}, FN = {fn}")
    print(f"Sensitivity (see_doctor recall) : {sensitivity:.3f}")
    print(f"Specificity (no_doctor recall)  : {specificity:.3f}")
    print(f"Accuracy                        : {accuracy:.3f}")


if __name__ == "__main__":
    # Run BOTH confusion matrices:
    # evaluate_on_csv(BREAST_CSV, out_png_name="confusion_matrix_breast.png", auto_open=True)
    # evaluate_on_csv(AXILLA_CSV, out_png_name="confusion_matrix_axilla.png", auto_open=True)

    # Or run GUI instead (comment the two lines above and uncomment below):
    run_gui()

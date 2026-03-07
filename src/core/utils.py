import os
import csv
import cv2
import datetime
from PIL import Image, ImageTk

# Standard Export Directories
EXPORT_DIR = "C:/Breast cancer project (new)/Testing/Predict Test"
CSV_LOG_PATH = os.path.join(EXPORT_DIR, "analysis_log.csv")

def ensure_export_dir():
    os.makedirs(EXPORT_DIR, exist_ok=True)

def append_results_to_csv(image_path, age, results_list):
    """
    Append list of prediction dictionaries to CSV log.
    If results_list is empty, writes one row indicating 'No Lesion Found'.
    """
    ensure_export_dir()
    file_exists = os.path.exists(CSV_LOG_PATH)
    
    headers = [
        "Timestamp", "Image_Path", "Age", "Lesion_Index",
        "Label", "Confidence", "Area_cm2",
        "Width_cm", "Height_cm", "Ratio", "Circularity",
        "Box_x1", "Box_y1", "Box_x2", "Box_y2", "See_Doctor"
    ]

    with open(CSV_LOG_PATH, mode="a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            writer.writeheader()

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        if not results_list:
            writer.writerow({
                "Timestamp": now_str,
                "Image_Path": image_path,
                "Age": age,
                "Lesion_Index": "N/A",
                "Label": "No Lesion Found",
                "Confidence": "", "Area_cm2": "",
                "Width_cm": "", "Height_cm": "", "Ratio": "", "Circularity": "",
                "Box_x1": "", "Box_y1": "", "Box_x2": "", "Box_y2": "",
                "See_Doctor": "No"
            })
            return

        for idx, res in enumerate(results_list, start=1):
            see_doctor = "Yes" if res["label"] == "Yes" else "No"
            writer.writerow({
                "Timestamp": now_str,
                "Image_Path": image_path,
                "Age": age,
                "Lesion_Index": idx,
                "Label": res["label"],
                "Confidence": f"{res['prob']:.4f}",
                "Area_cm2": f"{res['area_cm2']:.4f}",
                "Width_cm": f"{res['w_cm']:.4f}",
                "Height_cm": f"{res['h_cm']:.4f}",
                "Ratio": f"{res['ratio']:.4f}",
                "Circularity": f"{res['circularity']:.4f}",
                "Box_x1": int(res["box"][0]),
                "Box_y1": int(res["box"][1]),
                "Box_x2": int(res["box"][2]),
                "Box_y2": int(res["box"][3]),
                "See_Doctor": see_doctor
            })

def export_canvas_png(output_canvas, original_image_path):
    """
    Save the annotated BGR numpy array to disk alongside the script.
    """
    ensure_export_dir()
    base_name = os.path.splitext(os.path.basename(original_image_path))[0]
    out_filename = f"{base_name}_analyzed.png"
    out_path = os.path.join(EXPORT_DIR, out_filename)
    
    success = cv2.imwrite(out_path, output_canvas)
    if success:
        return True, out_path
    else:
        return False, "Failed to write image file."

def resize_image_for_tk(pil_img, max_width, max_height):
    """
    Resizes a PIL image whilst maintaining aspect ratio so it fits within max_width/max_height.
    Returns a Tkinter-compatible PhotoImage.
    """
    if pil_img is None:
        return None
        
    iw, ih = pil_img.size
    scale = min(max_width / iw, max_height / ih)
    new_w = max(1, int(iw * scale))
    new_h = max(1, int(ih * scale))
    
    img_resized = pil_img.resize((new_w, new_h), Image.LANCZOS)
    return ImageTk.PhotoImage(img_resized)

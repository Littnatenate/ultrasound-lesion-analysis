import os
import math
import cv2
import json
import torch
import detectron2
from detectron2.config import get_cfg
from detectron2 import model_zoo
from detectron2.engine import DefaultPredictor
from detectron2.structures import BoxMode
from detectron2.data import DatasetCatalog, MetadataCatalog
from detectron2.utils.visualizer import Visualizer, ColorMode

import projects.PointRend.point_rend as point_rend

# Analysis Weights and Thresholds
THRESHOLD = 0.40
W_RATIO = 1.717809
W_AREA = 0.109624
W_IRREG = 2.373295
W_AGE = 0.048660
B_BIAS = -4.572522

PIXELS_PER_CM = 101.54

class Analyzer:
    def __init__(self, use_gpu=False):
        """
        Initializes the Detectron2 Predictor and loads training metadata.
        """
        self.cfg = get_cfg()
        self.device = "cuda" if use_gpu and torch.cuda.is_available() else "cpu"
        self.cfg.MODEL.DEVICE = self.device
        
        point_rend.add_pointrend_config(self.cfg)
        
        # Merge configuration files
        self.cfg.merge_from_file(
            model_zoo.get_config_file("COCO-InstanceSegmentation/mask_rcnn_R_50_FPN_3x.yaml")
        )
        # Using abs path for PointRend configs as per original script
        self.cfg.merge_from_file(r"C:\Users\524yu\Dev\Breast-Cancer-Analysis\projects\PointRend\configs\InstanceSegmentation\pointrend_rcnn_R_50_FPN_3x_coco.yaml")
        
        self._setup_datasets()
        
        self.cfg.MODEL.ROI_HEADS.NUM_CLASSES = 1
        self.cfg.MODEL.POINT_HEAD.NUM_CLASSES = 1
        self.cfg.MODEL.WEIGHTS = os.path.join("output", "2000_iterations.pth")
        self.cfg.MODEL.ROI_HEADS.SCORE_THRESH_TEST = 0.7
        
        self.predictor = DefaultPredictor(self.cfg)

    def _get_lumps_dicts(self, img_dir):
        candidate_jsons = ["Training_json.json", "Validation_json.json"]
        json_file = None
        for name in candidate_jsons:
            path = os.path.join(img_dir, name)
            if os.path.exists(path):
                json_file = path
                break

        if json_file is None:
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
                record["annotations"].append({
                    "bbox": [min(px), min(py), max(px), max(py)],
                    "bbox_mode": BoxMode.XYXY_ABS,
                    "segmentation": [poly],
                    "category_id": 0,
                })

            dataset_dicts.append(record)

        return dataset_dicts

    def _setup_datasets(self):
        DatasetCatalog.clear()
        MetadataCatalog.clear()
        
        train_dir = r"C:\Breast cancer project (new)\Dataset\train"
        DatasetCatalog.register("lumps_train", lambda: self._get_lumps_dicts(train_dir))
        MetadataCatalog.get("lumps_train").set(thing_classes=["lump"])
        self.lumps_metadata = MetadataCatalog.get("lumps_train")

    def predict_see_doctor_prob(self, ratio, area_cm2, boundary_score, age):
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

    def analyze_image(self, image_path, age):
        """
        Runs the model on the image matching the path. 
        Calculates all clinical risk stats using the passed `age`.
        Returns the Visualizer image overlay array, and the statistics list.
        """
        im = cv2.imread(image_path)
        if im is None:
            raise ValueError(f"Could not read image: {image_path}")

        outputs = self.predictor(im)
        instances = outputs["instances"].to("cpu")

        masks = instances.pred_masks.cpu().numpy() if len(instances) > 0 else None
        boxes = instances.pred_boxes.tensor.numpy() if len(instances) > 0 else None
        scores = instances.scores.cpu().numpy() if len(instances) > 0 else None

        sorted_idx = []
        if masks is not None:
            # Get top 2 lumps sorted by area sizes
            sorted_idx = sorted(
                range(len(instances)),
                key=lambda i: int(masks[i].sum()),
                reverse=True,
            )[:2]

        v = Visualizer(
            im[:, :, ::-1],
            metadata=self.lumps_metadata,
            scale=0.5,
            instance_mode=ColorMode.IMAGE_BW,
        )
        vis_img = v.draw_instance_predictions(instances).get_image()[:, :, ::-1].copy()

        results_list = []
        if masks is not None and len(sorted_idx) > 0:
            for rank, i in enumerate(sorted_idx):
                x1, y1, x2, y2 = boxes[i]
                width_px = x2 - x1
                height_px = y2 - y1
                if width_px <= 0 or height_px <= 0:
                    continue

                ratio = float(height_px / width_px)
                # Scale mask up to 255 for safer OpenCV contour retrieval
                mask_i = (masks[i] * 255).astype("uint8")
                area_px = int(masks[i].sum())

                contours, _ = cv2.findContours(
                    mask_i, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
                )

                boundary_score = 0.0  # Default to worst circularity score (irregular)
                if len(contours) > 0:
                    # use the largest contour
                    cnt = max(contours, key=cv2.contourArea)
                    peri = cv2.arcLength(cnt, True)
                    c_area = cv2.contourArea(cnt)
                    if peri > 0 and c_area > 0:
                        circularity = 4.0 * math.pi * c_area / (peri ** 2)
                        boundary_score = max(0.0, min(1.0, circularity))

                height_cm = height_px / PIXELS_PER_CM
                width_cm = width_px / PIXELS_PER_CM
                area_cm2 = float(area_px / (PIXELS_PER_CM ** 2))

                prob, lbl = self.predict_see_doctor_prob(
                    ratio, area_cm2, boundary_score, age
                )

                results_list.append({
                    "label": lbl,
                    "prob": prob,
                    "area_cm2": area_cm2,
                    "h_cm": height_cm,
                    "w_cm": width_cm,
                    "ratio": ratio,
                    "circularity": boundary_score if boundary_score is not None else 0.0,
                    "box": (x1, y1, x2, y2)
                })

        return vis_img, results_list, masks, scores

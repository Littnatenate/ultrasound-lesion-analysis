# Ultrasound Lesion Analysis: A Deep Learning Approach for Automated Breast Cancer Risk Assessment

## Abstract
Breast cancer is a leading cause of cancer-related mortality among women worldwide, and early detection is crucial for improving patient outcomes. Ultrasound imaging is a common, non-invasive diagnostic modality, but interpreting these scans requires significant clinical expertise. This project presents an automated **Ultrasound Lesion Analysis** system that leverages instance segmentation and morphological feature extraction to assist clinicians in identifying and assessing breast lumps. By integrating a deep learning architecture (Mask R-CNN with PointRend) with a multivariate risk assessment model, the system outputs a rigorous "See Doctor" probability score. The entire pipeline is bundled into a user-friendly graphical interface (Tkinter), enabling real-time clinical use, visualization, and automated data exporting.

## 1. Introduction
The objective of this software is to provide an accessible, high-precision tool for analyzing breast ultrasound scans. By automating the extraction of key morphological features—such as lesion area, height-to-width ratio, and boundary irregularity—the system minimizes inter-observer variability and streamlines diagnostic workflows. A logistic regression-based scoring formulation is then applied to these physical attributes, alongside patient age, to estimate the probability of malignancy and suggest immediate clinical follow-up. 

## 2. Methodology

### 2.1 Deep Learning for Instance Segmentation
The core detection engine is built on **Detectron2**, utilizing a `Mask R-CNN` backbone coupled with `PointRend` for precise boundary delineation. 
- **Dataset:** The model is trained on a custom dataset of annotated breast ultrasound images with polygon masks. 
- **Inference:** Given an input scan, the model proposes bounding boxes, class labels, and high-fidelity segmentation masks for up to the top 2 candidate lumps.

### 2.2 Morphological Feature Extraction
Using OpenCV, the predicted segmentation masks are analyzed to extract essential geometric properties:
- **Pixel-to-Centimeter Conversion:** Features are resolved to physical scales using a pre-calibrated constant (`101.54 pixels/cm`).
- **Aspect Ratio:** The height-to-width ratio of the bounding box is computed. A higher ratio (taller-than-wide) is a known clinical indicator of malignancy.
- **Lesion Area:** Computed by aggregating the number of masked pixels and converted into $cm^2$.
- **Boundary Score (Circularity):** Contour analysis is performed to calculate the perimeter and area, identifying whether the boundary is *Smooth*, *Moderately Irregular*, or *Irregular*.

### 2.3 Risk Assessment Algorithm
A multivariable risk scoring algorithm evaluates the extracted metrics to output a comprehensive "See Doctor" probability. The score merges morphological variables and the patient's age:

$$ \text{Score} = (W_{ratio} \times \text{Ratio}) + (W_{area} \times \text{Area}) + (W_{irreg} \times \text{Irregularity}) + (W_{age} \times \text{Age}) + \text{Bias} $$

$$ P(\text{See Doctor}) = \frac{1}{1 + e^{-\text{Score}}} $$

Where empirically tuned constants determine the weight of each factor. A threshold of `0.40` is utilized to output a definitive binary label (*Yes / No*).

### 2.4 Graphical User Interface (GUI)
A robust Tkinter-based application was developed for patient intake and continuous workflows:
- **Input:** Clinicians can load ultrasound scans (PNG, JPG, TIF) and enter patient demographics (e.g., Age) and clinical notes.
- **Output:** An enriched visual canvas is generated detailing the clinical text card next to an upscaled ultrasound image overlaid with bounding boxes and segmentations.
- **Data Export:** The system supports saving the visual report as a PNG and appending numerical findings into a centralized CSV log (`results_log.csv`) for hospital registry or subsequent auditing.

## 3. Results & Output Generation
Upon execution, the application renders a high-resolution composite canvas. The system successfully isolates the suspicious ROI (Region of Interest) and outputs:
- **Dimensions:** Absolute width, height, and area ($cm^2$).
- **Boundary Morphology:** A statistical circularity score.
- **Recommendation:** A synthesized $P(\text{See Doctor})$.

Additionally, all inference instances and their corresponding metadata (Timestamp, Age, Metric Scores) are securely logged for long-term clinical research.

## 4. Conclusion
This project demonstrates the effective convergence of Computer Vision and Clinical Logic. By utilizing Mask R-CNN and PointRend architectures to parse ultrasound scans, paired against a deterministic mathematical risk model, the application serves as a powerful second-reader for oncologists and radiologists, facilitating earlier and more data-driven diagnosis of breast cancer.

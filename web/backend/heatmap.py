"""
Heatmap overlay generator for ultrasound lesion analysis.
Takes raw segmentation masks + confidence scores from Detectron2
and produces a color-graded overlay ONLY on detected lesion regions.
Creates an internal radial gradient within each mask for visual depth.
Includes a color legend bar.
"""
import cv2
import numpy as np


def _create_legend_bar(height, bar_width=25, margin=10):
    """Create a vertical color legend bar with labels."""
    legend_w = bar_width + margin * 2 + 50  # bar + labels
    legend = np.ones((height, legend_w, 3), dtype=np.uint8) * 30  # Dark background
    
    bar_top = margin + 30
    bar_bottom = height - margin - 10
    bar_h = bar_bottom - bar_top
    
    if bar_h <= 0:
        return legend
    
    for y in range(bar_h):
        # 0 at bottom (green/safe) → 1 at top (red/danger)
        ratio = 1.0 - (y / bar_h)
        r, g, b = _risk_color(ratio)
        legend[bar_top + y, margin:margin + bar_width] = [b, g, r]  # BGR
    
    # Border
    cv2.rectangle(legend, (margin, bar_top), (margin + bar_width, bar_bottom), (180, 180, 180), 1)
    
    # Title
    font = cv2.FONT_HERSHEY_SIMPLEX
    cv2.putText(legend, "RISK", (margin, bar_top - 10), font, 0.4, (220, 220, 220), 1)
    
    # Labels
    label_x = margin + bar_width + 5
    cv2.putText(legend, "HIGH", (label_x, bar_top + 14), font, 0.35, (100, 100, 255), 1)
    
    mid_y = (bar_top + bar_bottom) // 2
    cv2.putText(legend, "MED", (label_x, mid_y + 5), font, 0.35, (100, 220, 220), 1)
    
    cv2.putText(legend, "LOW", (label_x, bar_bottom - 4), font, 0.35, (100, 255, 100), 1)
    
    return legend


def _risk_color(intensity):
    """Map an intensity [0, 1] to a Red-Yellow-Green gradient. Returns (R, G, B)."""
    intensity = max(0.0, min(1.0, intensity))
    if intensity < 0.5:
        # Green → Yellow
        r = int(255 * (intensity * 2))
        g = 255
        b = 0
    else:
        # Yellow → Red
        r = 255
        g = int(255 * (1 - (intensity - 0.5) * 2))
        b = 0
    return r, g, b


def generate_heatmap_overlay(vis_img, masks, scores, results_list=None, alpha=0.45):
    """
    Generate a heatmap overlay on the ANNOTATED image (vis_img) so that
    bounding boxes and labels remain visible.
    
    Creates a radial gradient within each mask — center of each lesion is
    most intense, fading toward the edges — for a proper "heatmap" look.
    
    Args:
        vis_img:        BGR numpy array (the annotated visualization image)
        masks:          numpy array of shape (N, H, W) — boolean segmentation masks
        scores:         numpy array of shape (N,) — detection confidence scores
        results_list:   list of result dicts (used for risk probability coloring)
        alpha:          blend opacity for the colored overlay
    
    Returns:
        BGR numpy array with heatmap overlay and legend
    """
    if masks is None or len(masks) == 0:
        return vis_img.copy()
    
    h, w = vis_img.shape[:2]
    result = vis_img.copy()
    
    # Accumulate the heatmap intensity and color for each pixel
    heat_intensity = np.zeros((h, w), dtype=np.float32)
    heat_color = np.zeros((h, w, 3), dtype=np.float32)
    
    for i in range(len(masks)):
        mask = masks[i].astype(np.float32)
        
        # Resize mask to match image if needed
        if mask.shape != (h, w):
            mask = cv2.resize(mask, (w, h), interpolation=cv2.INTER_LINEAR)
        
        # Get risk probability
        if results_list and i < len(results_list):
            prob = results_list[i].get("prob", None)
            risk = float(prob) if prob is not None else float(scores[i])
        else:
            risk = float(scores[i])
        risk = max(0.0, min(1.0, risk))
        
        # Create a distance-from-edge gradient within the mask
        # This makes the center of the lesion brighter (more intense)
        binary_mask = (mask > 0.5).astype(np.uint8)
        if binary_mask.sum() == 0:
            continue
        
        # Distance transform: higher values = further from edge = center of lesion
        dist = cv2.distanceTransform(binary_mask, cv2.DIST_L2, 5).astype(np.float32)
        max_dist = dist.max()
        if max_dist > 0:
            dist_norm = dist / max_dist  # 0 at edge, 1 at center
        else:
            dist_norm = dist
        
        # Combine mask with distance gradient
        # Inner region is full intensity, outer region fades
        gradient = dist_norm * mask
        
        # Smooth the gradient for better visual appearance
        gradient = cv2.GaussianBlur(gradient, (21, 21), 0)
        gradient = np.clip(gradient, 0, 1)
        
        # Map the gradient to colors
        # The risk value determines the HUE (green vs yellow vs red)
        # The distance gradient determines the BRIGHTNESS within the mask
        r_base, g_base, b_base = _risk_color(risk)
        
        # Create the per-mask color contribution
        mask_contrib = gradient  # 0 at edges, 1 at center
        
        # Update the combined heat map where this mask is stronger
        update_region = mask_contrib > heat_intensity
        heat_intensity = np.where(update_region, mask_contrib, heat_intensity)
        heat_color[update_region] = [b_base, g_base, r_base]  # BGR
    
    # Blend the heatmap into the result image
    heat_alpha = heat_intensity[:, :, np.newaxis] * alpha
    result = result.astype(np.float32)
    result = result * (1 - heat_alpha) + heat_color * heat_alpha
    result = np.clip(result, 0, 255).astype(np.uint8)
    
    # Add the legend bar
    legend = _create_legend_bar(h, bar_width=20, margin=8)
    result = np.hstack([result, legend])
    
    return result

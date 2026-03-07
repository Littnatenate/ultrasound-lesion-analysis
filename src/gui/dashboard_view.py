import os
import cv2
import numpy as np
import tkinter as tk
from typing import Optional, Any
import tkinter.ttk as ttk
from tkinter import filedialog, messagebox
from PIL import Image, ImageTk

from src.core.analyzer import Analyzer
from src.core.utils import export_canvas_png, append_results_to_csv
from src.core.pdf_report import generate_pdf_report
from src.core.heatmap import generate_heatmap_overlay

# 'Soothing & Nurturing' UI palette
ACCENT_COLOR = "#C8B1E4"   # Soft Lavender (calm, elegant)
ERROR_COLOR = "#DCAE96"    # Dusty Rose (comfort, empathy)
OK_COLOR = "#9CAF88"       # Gentle Sage Green (healing, nature)
WARM_GRAY = "#FDFBF7"      # Soft Cream (cleanliness, background)
TEXT_DARK = "#4A4A4A"      # Softened charcoal text so it's not harsh black
TEXT_LIGHT = "#8C8C8C"     # Muted slate gray

class DashboardView(tk.Frame):
    def __init__(self, parent, analyzer: Analyzer, profile: dict):
        # Determine current theme from the root window's ttkbootstrap style
        try:
            current_theme = parent.winfo_toplevel().style.theme_use()
        except Exception:
            current_theme = "flatly"
        self.is_dark = "cyborg" in current_theme
        
        # 'Soothing & Nurturing' dynamic UI palette
        self.ACCENT_COLOR = "#C8B1E4"   # Soft Lavender
        self.ERROR_COLOR = "#DCAE96"    # Dusty Rose
        self.OK_COLOR = "#9CAF88"       # Gentle Sage Green
        
        # Adapt backgrounds and text for dark mode
        self.bg_color = "#2c2c2c" if self.is_dark else "#FDFBF7"        
        self.card_bg = "#3a3a3a" if self.is_dark else "white"           
        self.card_border = "#555555" if self.is_dark else "#d1d9e0"
        self.text_dark = "#E6E6FA" if self.is_dark else "#4A4A4A"        
        self.text_light = "#A0A0A0" if self.is_dark else "#8C8C8C"       
        
        super().__init__(parent, bg=self.bg_color)
        self.analyzer = analyzer
        self.profile = profile
        
        # Shared state
        self.image_path_var = tk.StringVar(value="")
        self.site_var = tk.StringVar(value="Breast")
        self.age_var = tk.StringVar(value="")
        
        self.current_canvas = {"img": None}
        self.current_results = {"rows": None}
        self.current_meta = {"image_path": None, "age": None, "site": None, "case_id": None}
        
        self.preview_original_img = {"pil": None, "tk": None}
        
        self.badge_card: Optional[tk.Frame] = None
        self.badge_label: Optional[tk.Label] = None
        self.stats_container: Optional[tk.Frame] = None
        
        # Heatmap state
        self.heatmap_active = False
        self.raw_original_img = None    # Original BGR image (for heatmap)
        self.raw_masks = None
        self.raw_scores = None
        
        # Settings toggles (all default ON)
        self.show_heatmap_var = tk.BooleanVar(value=False)
        self.show_png_var = tk.BooleanVar(value=True)
        self.show_pdf_var = tk.BooleanVar(value=True)
        self.show_csv_var = tk.BooleanVar(value=True)
        
        self._build_ui()
        
        # Initialize button states correctly
        self.update_run_button_state()

    def _build_canvas(self, base_img, rows):
        """Build composite result canvas identical to TEST FINAL.py"""
        font = cv2.FONT_HERSHEY_SIMPLEX
        font_scale = 0.55
        thickness = 1

        # ----- enlarge only the ultrasound image -----
        h0, w0, _ = base_img.shape
        IMAGE_SCALE = 1.25

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
                (w_label, h_label), _ = cv2.getTextSize(label_text, font, font_scale, thickness)
                (w_val, h_val), _ = cv2.getTextSize(" " + value, font, font_scale, thickness)
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
        cv2.rectangle(canvas, (0, image_y), (w_img - 1, image_y + cards_h - 1), (210, 210, 210), 2)
        sep_x = w_img + 10
        cv2.line(canvas, (sep_x, image_y), (sep_x, image_y + cards_h), (210, 210, 210), 1)

        # -------------------- RIGHT-HAND CARD --------------------
        cv2.rectangle(canvas, (card_x, card_y), (card_x + card_width, card_y + cards_h), (245, 245, 245), -1)
        cv2.rectangle(canvas, (card_x, card_y), (card_x + card_width, card_y + cards_h), (210, 210, 210), 1)

        base_x_label = card_x + card_pad_x
        base_x_value = card_x + card_pad_x + label_col_width + 20
        ty = card_y + card_pad_y + line_h

        for label, value, is_header in rows:
            if label == "" and value == "":
                ty += line_gap
                continue

            if is_header or value == "":
                cv2.putText(canvas, label, (base_x_label, ty), font, font_scale, label_color, 2, cv2.LINE_AA)
                ty += int(line_gap * 1.4)
                continue

            cv2.putText(canvas, label + ":", (base_x_label, ty), font, font_scale, label_color, thickness, cv2.LINE_AA)
            cv2.putText(canvas, value, (base_x_value, ty), font, font_scale, value_color, thickness, cv2.LINE_AA)
            ty += line_gap

        return canvas

    def _build_ui(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=10, pady=10)

        self.intake_tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.result_tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.settings_tab = tk.Frame(self.notebook, bg=self.bg_color)
        self.notebook.add(self.intake_tab, text="  Patient Intake  ")
        self.notebook.add(self.result_tab, text="  Analysis Result  ")
        self.notebook.add(self.settings_tab, text="  ⚙ Settings  ")

        self._build_intake_tab()
        self._build_result_tab()
        self._build_settings_tab()

    def _build_intake_tab(self):
        intake_container = tk.Frame(self.intake_tab, bg=self.card_bg, bd=0, highlightthickness=1, highlightbackground=self.card_border)
        intake_container.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Frame(intake_container, bg=self.ACCENT_COLOR, height=3).pack(fill="x", side="top")
        
        # Use a content frame with grid layout so we can control column widths
        content_frame = tk.Frame(intake_container, bg=self.card_bg)
        content_frame.pack(fill="both", expand=True)
        content_frame.grid_rowconfigure(0, weight=1)
        content_frame.grid_columnconfigure(0, weight=0, minsize=350)  # Form column — shrinks to 350 minimum
        content_frame.grid_columnconfigure(1, weight=1)               # Preview expands

        # Left panel — proportional form (adapts to window width)
        left_panel = tk.Frame(content_frame, bg=self.card_bg, padx=30, pady=30)
        left_panel.grid(row=0, column=0, sticky="nsew")

        tk.Label(left_panel, text="Patient Analysis", font=("Segoe UI Semibold", 20), bg=self.card_bg, fg=self.text_dark).pack(anchor="w")
        tk.Label(left_panel, text="Fill in clinical details and select an ultrasound scan to begin.", font=("Segoe UI", 9), bg=self.card_bg, fg=self.text_light).pack(anchor="w", pady=(0, 18))

        def required_label(parent, text):
            row = tk.Frame(parent, bg=self.card_bg)
            row.pack(fill="x", anchor="w")
            tk.Label(row, text=text + " ", font=("Segoe UI Bold", 9), bg=self.card_bg, fg=self.text_dark).pack(side="left")
            tk.Label(row, text="*", font=("Segoe UI Bold", 9), bg=self.card_bg, fg=self.ERROR_COLOR).pack(side="left")

        # Site
        tk.Label(left_panel, text="EXAMINATION SITE", font=("Segoe UI Bold", 9), bg=self.card_bg, fg=self.text_dark).pack(anchor="w")
        site_combo = ttk.Combobox(left_panel, textvariable=self.site_var, state="readonly", font=("Segoe UI", 10), values=["Breast", "Axilla"])
        site_combo.pack(fill="x", pady=(5, 14), ipady=2)

        # Age
        required_label(left_panel, "PATIENT AGE (YEARS)")
        self.age_entry = tk.Entry(left_panel, textvariable=self.age_var, font=("Segoe UI", 11), bd=1, relief="solid", bg="#f5f6f7", highlightthickness=1, highlightbackground=self.card_border)
        self.age_entry.pack(fill="x", pady=(5, 4), ipady=6)
        self.age_help_label = tk.Label(left_panel, text="Enter a number (e.g., 45).", font=("Segoe UI", 8), bg=self.card_bg, fg=self.text_light)
        self.age_help_label.pack(anchor="w", pady=(0, 14))
        self.age_var.trace_add("write", lambda *a: self.update_run_button_state())

        # Upload
        required_label(left_panel, "ULTRASOUND SCAN")
        file_row = tk.Frame(left_panel, bg=self.card_bg)
        file_row.pack(fill="x", pady=(5, 4))
        
        file_btn = ttk.Button(file_row, text="Choose File…", command=self.select_image_dialog, bootstyle="secondary-outline")
        file_btn.pack(side="left")
        tk.Label(file_row, text="  (PNG/JPG/BMP/TIF)", font=("Segoe UI", 8), bg=self.card_bg, fg=self.text_light).pack(side="left")
        
        tk.Label(left_panel, textvariable=self.image_path_var, font=("Segoe UI Italic", 8), bg=self.card_bg, fg=self.text_light, wraplength=420, anchor="w", justify="left").pack(anchor="w", pady=(0, 2))
        self.scan_help_label = tk.Label(left_panel, text="Supported formats: PNG, JPG, BMP, TIF.", font=("Segoe UI", 8), bg=self.card_bg, fg=self.text_light)
        self.scan_help_label.pack(anchor="w", pady=(0, 20))
        
        self.status_label = tk.Label(left_panel, text="", font=("Segoe UI", 9), bg=self.card_bg, fg=self.text_light)
        self.status_label.pack(anchor="w", pady=(0, 2))

        # Buttons
        btns = tk.Frame(left_panel, bg=self.card_bg)
        btns.pack(fill="x", pady=(6, 6))

        self.run_button = ttk.Button(btns, text="Run Analysis", command=self.on_run_analysis, bootstyle="info")
        self.run_button.pack(side="left", fill="x", expand=True, ipady=8, padx=(0, 10))

        ttk.Button(btns, text="Reset", command=self.clear_form, bootstyle="secondary-outline").pack(side="left", ipady=8)

        # Right panel — takes all remaining space via grid
        right_panel = tk.Frame(content_frame, bg=self.bg_color, padx=24, pady=24)
        right_panel.grid(row=0, column=1, sticky="nsew")
        tk.Label(right_panel, text="Selected Ultrasound Preview", font=("Segoe UI Semibold", 11), bg=self.bg_color, fg=self.text_dark, anchor="w").pack(anchor="nw", pady=(0, 8))
        
        preview_card = tk.Frame(right_panel, bg=self.card_bg, bd=0, highlightthickness=1, highlightbackground=self.card_border)
        preview_card.pack(fill="both", expand=True)
        tk.Frame(preview_card, bg=self.ACCENT_COLOR, height=3).pack(fill="x", side="top")
        
        image_frame = tk.Frame(preview_card, bg=self.card_bg, padx=10, pady=10)
        image_frame.pack(fill="both", expand=True)
        self.preview_label = tk.Label(image_frame, text="No Image Selected", font=("Segoe UI", 10), bg=self.card_bg, fg=self.text_light)
        self.preview_label.pack(expand=True, fill="both")
        
        # Auto-resize preview image when the container is resized (e.g., full-screen toggle)
        self.preview_label.bind("<Configure>", self.resize_preview_image)

        self.image_path_var.trace_add("write", lambda *a: self.update_run_button_state())
        
    def _build_result_tab(self):
        result_header = tk.Frame(self.result_tab, bg=self.bg_color)
        result_header.pack(fill="x", padx=20, pady=(10, 0))
        tk.Label(result_header, text="Analysis Result", font=("Segoe UI Semibold", 18), bg=self.bg_color, fg=self.text_dark).pack(side="left")

        btn_row = tk.Frame(self.result_tab, bg=self.bg_color)
        btn_row.pack(fill="x", padx=20, pady=(10, 0))
        
        self.png_btn = ttk.Button(btn_row, text="Save PNG Report", command=self.save_png, bootstyle="success")
        self.png_btn.pack(side="left", padx=(0, 6))
        self.pdf_btn = ttk.Button(btn_row, text="Save PDF Report", command=self.save_pdf, bootstyle="primary")
        self.pdf_btn.pack(side="left", padx=(0, 6))
        self.csv_btn = ttk.Button(btn_row, text="Save CSV Log", command=self.save_csv, bootstyle="info")
        self.csv_btn.pack(side="left", padx=(0, 6))
        self.heatmap_btn = ttk.Button(btn_row, text="🔥 Toggle Heatmap", command=self.toggle_heatmap, bootstyle="warning")
        # Not packed by default — user enables via Settings tab

        # Two-pane grid layout for Results (responsive to window resizing)
        result_container = tk.Frame(self.result_tab, bg=self.bg_color)
        result_container.pack(fill="both", expand=True, padx=20, pady=15)
        result_container.grid_rowconfigure(0, weight=1)
        result_container.grid_columnconfigure(0, weight=3)                  # Image: takes more space
        result_container.grid_columnconfigure(1, weight=1, minsize=300)     # Stats: proportional, min 300px
        
        # Left side: Annotated Image Container
        left_col = tk.Frame(result_container, bg=self.card_bg, bd=0, highlightthickness=1, highlightbackground=self.card_border)
        left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        tk.Frame(left_col, bg=self.ACCENT_COLOR, height=3).pack(fill="x", side="top")
        
        self.result_image_label = tk.Label(left_col, bg=self.card_bg)
        self.result_image_label.pack(expand=True, fill="both", padx=10, pady=10)

        # Right side: Native UI Cards for Stats (proportional width)
        right_col = tk.Frame(result_container, bg=self.bg_color)
        right_col.grid(row=0, column=1, sticky="nsew")
        self._stats_right_col = right_col  # Save reference for dynamic wraplength
        
        # Dynamically adjust text wraplength when the stats panel is resized
        def _on_stats_resize(event):
            new_wrap = max(120, event.width - 130)  # Leave room for label column
            self._stats_wraplength = new_wrap
        right_col.bind("<Configure>", _on_stats_resize)
        self._stats_wraplength = 280  # Default
        
        # Back to Home button — full width, prominent, above the See Doctor badge
        back_btn = ttk.Button(right_col, text="← Back to Home", command=lambda: self.notebook.select(self.intake_tab), bootstyle="primary")
        back_btn.pack(fill="x", ipady=10, pady=(0, 15))
        
        # See Doctor Badge Card
        self.badge_card = tk.Frame(right_col, bg=self.card_bg, bd=0, highlightthickness=1, highlightbackground=self.card_border)
        self.badge_card.pack(fill="x", pady=(0, 15))
        self.badge_label = tk.Label(self.badge_card, text="See Doctor: \nUNKNOWN", font=("Segoe UI Black", 14), bg=self.card_bg, fg=self.text_dark, pady=20)
        self.badge_label.pack(fill="x", expand=True)
        
        # Clinical Details Card
        details_card = tk.Frame(right_col, bg=self.card_bg, bd=0, highlightthickness=1, highlightbackground=self.card_border, padx=15, pady=20)
        details_card.pack(fill="both", expand=True)
        
        tk.Label(details_card, text="Clinical Statistics", font=("Segoe UI Semibold", 13), bg=self.card_bg, fg=self.text_dark).pack(anchor="w", pady=(0, 15))
        
        self.stats_container = tk.Frame(details_card, bg=self.card_bg)
        self.stats_container.pack(fill="both", expand=True)

    def _build_settings_tab(self):
        """Build the Settings tab with feature toggles."""
        container = tk.Frame(self.settings_tab, bg=self.card_bg, bd=0, highlightthickness=1, highlightbackground=self.card_border)
        container.pack(fill="both", expand=True, padx=20, pady=20)
        tk.Frame(container, bg=self.ACCENT_COLOR, height=3).pack(fill="x", side="top")
        
        inner = tk.Frame(container, bg=self.card_bg, padx=40, pady=30)
        inner.pack(fill="both", expand=True)
        
        tk.Label(inner, text="Feature Toggles", font=("Segoe UI Semibold", 20), bg=self.card_bg, fg=self.text_dark).pack(anchor="w")
        tk.Label(inner, text="Enable or disable features visible on the Analysis Result tab.", font=("Segoe UI", 9), bg=self.card_bg, fg=self.text_light).pack(anchor="w", pady=(0, 25))
        
        toggles = [
            (self.show_heatmap_var, "🔥 Heatmap Overlay", "Show the Toggle Heatmap button on the results tab"),
            (self.show_png_var, "📷 PNG Export", "Show the Save PNG Report button"),
            (self.show_pdf_var, "📄 PDF Export", "Show the Save PDF Report button"),
            (self.show_csv_var, "📊 CSV Export", "Show the Save CSV Log button"),
        ]
        
        for var, label, desc in toggles:
            row = tk.Frame(inner, bg=self.card_bg)
            row.pack(fill="x", pady=(0, 12))
            
            cb = ttk.Checkbutton(row, text=label, variable=var, command=self._apply_settings, bootstyle="round-toggle")
            cb.pack(side="left")
            
            tk.Label(row, text=f"  —  {desc}", font=("Segoe UI", 8), bg=self.card_bg, fg=self.text_light).pack(side="left")

    def _apply_settings(self):
        """Show/hide buttons based on settings toggles."""
        if self.show_png_var.get():
            self.png_btn.pack(side="left", padx=(0, 6))
        else:
            self.png_btn.pack_forget()
        
        if self.show_pdf_var.get():
            self.pdf_btn.pack(side="left", padx=(0, 6))
        else:
            self.pdf_btn.pack_forget()
        
        if self.show_csv_var.get():
            self.csv_btn.pack(side="left", padx=(0, 6))
        else:
            self.csv_btn.pack_forget()
        
        if self.show_heatmap_var.get():
            self.heatmap_btn.pack(side="left")
        else:
            self.heatmap_btn.pack_forget()

    def toggle_heatmap(self):
        """Toggle between normal annotated image and heatmap overlay."""
        vis_img = self.current_results.get("vis_img")
        if vis_img is None:
            messagebox.showwarning("No Data", "Run an analysis first.")
            return
        
        if not self.heatmap_active:
            # Generate heatmap overlay on the annotated image
            if self.raw_masks is not None:
                heatmap_img = generate_heatmap_overlay(
                    vis_img,
                    self.raw_masks,
                    self.raw_scores,
                    self.current_results.get("rows")
                )
                self.current_results["heatmap_img"] = heatmap_img
                self.current_results["vis_img_backup"] = vis_img
                self.current_results["vis_img"] = heatmap_img
                self.heatmap_active = True
                self.heatmap_btn.configure(text="📊 Normal View")
            else:
                messagebox.showinfo("Heatmap", "No mask data available for heatmap.")
                return
        else:
            # Restore normal view
            backup = self.current_results.get("vis_img_backup")
            if backup is not None:
                self.current_results["vis_img"] = backup
            self.heatmap_active = False
            self.heatmap_btn.configure(text="🔥 Toggle Heatmap")
        
        self.update_result_tab_image()

    def select_image_dialog(self):
        path = filedialog.askopenfilename(
            filetypes=[("Image files", "*.jpg *.JPG *.jpeg *.JPEG *.png *.PNG *.bmp *.BMP *.tif *.TIF *.tiff *.TIFF"), ("All files", "*.*")],
        )
        if not path: return
        self.image_path_var.set(path)
        try:
            img = Image.open(path)
            self.preview_original_img["pil"] = img
            self.update_idletasks()  # Force layout so container dimensions are accurate
            self.resize_preview_image()
        except Exception as e:
            messagebox.showerror("Image Error", f"Could not open image:\n{e}")
            self.preview_original_img["pil"] = None
            self.preview_label.config(image="", text="No Image Selected")
            self.preview_label.image = None
            return
        self.update_run_button_state()

    def resize_preview_image(self, event=None):
        img = self.preview_original_img.get("pil")
        if img is None: return
        
        # Dynamic scaling: use the container's actual dimensions, just like the result image
        max_w = self.preview_label.winfo_width()
        max_h = self.preview_label.winfo_height()
        
        # If the window hasn't drawn yet, fallback to reasonable defaults
        if max_w <= 10 or max_h <= 10:
            max_w, max_h = 600, 600
        
        # Subtract padding
        max_w -= 20
        max_h -= 20
        
        w, h = img.size
        scale = min(max_w / w, max_h / h)
        scale = min(scale, 4.0)
        
        new_w, new_h = int(w * scale), int(h * scale)
        if new_w <= 0 or new_h <= 0: return
        
        display_img = img.resize((new_w, new_h), Image.LANCZOS)
        
        tk_img = ImageTk.PhotoImage(display_img)
        self.preview_original_img["tk"] = tk_img
        self.preview_label.config(image=tk_img, text="")
        self.preview_label.image = tk_img

    def update_run_button_state(self, *args):
        img_path = self.image_path_var.get().strip()
        age_str = self.age_var.get().strip()
        valid = True

        if not img_path:
            valid = False
            self.scan_help_label.config(text="Ultrasound scan is required.", fg=self.ERROR_COLOR)
        else:
            self.scan_help_label.config(text="Supported formats: PNG, JPG, BMP, TIF.", fg=self.text_light)
        
        # Validate age
        if not age_str:
            valid = False
            self.age_help_label.config(text="Age is required.", fg=self.ERROR_COLOR)
        else:
            try:
                float(age_str)
                self.age_help_label.config(text="Enter a number (e.g., 45).", fg=self.text_light)
            except ValueError:
                valid = False
                self.age_help_label.config(text="Please enter a valid number.", fg=self.ERROR_COLOR)
        
        if valid:
            self.run_button.configure(state="normal")
            if self.status_label.cget("text") == "":
                self.status_label.config(text="Ready to analyze.", fg=self.OK_COLOR)
        else:
            self.run_button.configure(state="disabled")
            if "complete" not in self.status_label.cget("text").lower():
                self.status_label.config(text="", fg=self.text_light)

    def on_run_analysis(self):
        # Read age from the input field
        age_str = self.age_var.get().strip()
        try:
            age_val = float(age_str)
        except (ValueError, TypeError):
            messagebox.showerror("Input Error", "Please enter a valid age.")
            return
        img_path = self.image_path_var.get().strip()

        self.update_run_button_state()
        if str(self.run_button.cget("state")) != "normal": return

        self.run_button.configure(text="Analyzing…", state="disabled")
        self.status_label.config(text="Running analysis…", fg=self.ACCENT_COLOR)
        self.update_idletasks()

        try:
            vis_img, results_for_csv, raw_masks, raw_scores = self.analyzer.analyze_image(img_path, age_val)
            
            # Store raw data for heatmap
            self.raw_original_img = cv2.imread(img_path)
            self.raw_masks = raw_masks
            self.raw_scores = raw_scores
            self.heatmap_active = False
            
            # Construct rows for build_canvas
            rows = [("Age", f"{int(age_val)}", False), ("", "", False)]
            if not results_for_csv:
                rows.append(("No lump detected", "", True))
            else:
                for rank, res in enumerate(results_for_csv):
                    lid = f"L{rank + 1}"
                    rows.append((lid + ":", "", True))
                    rows.append(("Height/Width", f"{res['ratio']:.2f}", False))
                    rows.append(("Dimensions", f"{res['h_cm']:.2f} cm (H) x {res['w_cm']:.2f} cm (W)", False))
                    rows.append(("Size", f"{res['area_cm2']:.2f} cm^2", False))
                    circularity = res.get('circularity', 0.0)
                    circ_lbl = "Smooth" if circularity >= 0.8 else ("Mod. irregular" if circularity >= 0.6 else "Irregular")
                    rows.append(("Boundary", f"{circ_lbl} (circularity = {circularity:.2f})", False))
                    
                    if res['prob'] is not None:
                        rows.append(("See doctor", f"{res['label']} (p = {res['prob']:.2f})", False))
                    else:
                        rows.append(("See doctor", "Unknown", False))
                        
                    rows.append(("", "", False))
                    
            # Build the static export canvas for the Save PNG feature ONLY
            canvas = self._build_canvas(vis_img, rows)
            
            self.current_canvas["img"] = canvas
            self.current_results["vis_img"] = vis_img  # Store raw vis_img for dynamic UI rendering
            self.current_results["rows"] = results_for_csv
            self.current_meta["image_path"] = img_path
            self.current_meta["age"] = age_val
            self.current_meta["site"] = self.site_var.get()
            self.current_meta["case_id"] = ""

            self.notebook.select(self.result_tab)
            self.update_idletasks()  # Force Tkinter to draw the tab so we can check the true dimensions

            self.update_result_tab_image()
            self.update_stats_row()

            self.run_button.configure(text="✓ Analysis complete")
            self.status_label.config(text="Analysis complete.", fg=self.OK_COLOR)
            self.after(1500, lambda: (self.run_button.configure(text="Run Analysis"), self.update_run_button_state()))
        except Exception as e:
            messagebox.showerror("Analysis Error", str(e))
            self.status_label.config(text="Analysis failed.", fg=self.ERROR_COLOR)
            self.run_button.configure(text="Run Analysis")
            self.update_run_button_state()

    def update_result_tab_image(self, event=None):
        vis_img = self.current_results.get("vis_img")
        if vis_img is None: return
        
        h, w = vis_img.shape[:2]
        
        # Determine target bounding box based on the dynamically drawn full-screen container
        max_w = self.result_image_label.winfo_width()
        max_h = self.result_image_label.winfo_height()
        
        # If the window hasn't properly drawn yet (width is 1), fallback to a large size
        if max_w <= 10 or max_h <= 10:
            max_w, max_h = 800, 800
            
        # Add a little internal padding
        max_w -= 20
        max_h -= 20
        
        # Scale to max bounds preserving aspect ratio
        scale = min(max_w / w, max_h / h)
        scale = min(scale, 4.0)  # Stop before it gets comically large and blurry
        
        new_w, new_h = int(w * scale), int(h * scale)
        if new_w <= 0 or new_h <= 0: return
        
        vis_big = cv2.resize(vis_img, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        vis_rgb = cv2.cvtColor(vis_big, cv2.COLOR_BGR2RGB)
        
        img_pil = Image.fromarray(vis_rgb)
        img_tk = ImageTk.PhotoImage(img_pil)
        
        self.result_image_label.config(image=img_tk, text="")
        self.result_image_label.image = img_tk

    def _add_stat_row(self, label_text, value_text):
        row = tk.Frame(self.stats_container, bg=self.card_bg)
        row.pack(fill="x", pady=(0, 10))
        wrap = getattr(self, '_stats_wraplength', 280)
        tk.Label(row, text=label_text, font=("Segoe UI Semibold", 10), bg=self.card_bg, fg=self.text_light, width=12, anchor="w").pack(side="left")
        tk.Label(row, text=value_text, font=("Segoe UI", 10), bg=self.card_bg, fg=self.text_dark, anchor="w", wraplength=wrap).pack(side="left", fill="x", expand=True)

    def update_stats_row(self):
        # Clear existing native stats
        for widget in self.stats_container.winfo_children():
            widget.destroy()
            
        rows = self.current_results.get("rows")
        age = self.current_meta["age"]
        site = self.current_meta["site"]
        case_id = self.current_meta["case_id"]

        self._add_stat_row("Patient Age:", f"{int(age)} years")
        self._add_stat_row("Exam Site:", site or "N/A")
        if case_id:
            self._add_stat_row("Case ID:", case_id)

        # Draw line separator
        tk.Frame(self.stats_container, bg="#e0e0e0", height=1).pack(fill="x", pady=(10, 15))

        if not rows:
            self.badge_card.config(highlightbackground=self.OK_COLOR)
            self.badge_label.config(text="See Doctor:\nNO (Clear)", fg=self.OK_COLOR)
            tk.Label(self.stats_container, text="No lesions were detected.", font=("Segoe UI Italic", 10), bg=self.card_bg, fg=self.text_light).pack(anchor="w")
            return

        # Use the highest probability lump to drive the badge
        doctor_yes = any(r["label"] == "Yes" for r in rows)
        
        if doctor_yes:
            self.badge_card.config(highlightbackground=self.ERROR_COLOR)
            self.badge_label.config(text="See Doctor:\nYES", fg=self.ERROR_COLOR)
        else:
            self.badge_card.config(highlightbackground=self.OK_COLOR)
            self.badge_label.config(text="See Doctor:\nNO", fg=self.OK_COLOR)

        for rank, res in enumerate(rows):
            lid = f"Lump #{rank + 1}:"
            tk.Label(self.stats_container, text=lid, font=("Segoe UI Bold", 11), bg=self.card_bg, fg=self.text_dark).pack(anchor="w", pady=(5, 5))
            
            self._add_stat_row("Dimensions:", f"{res['h_cm']:.2f} cm x {res['w_cm']:.2f} cm")
            self._add_stat_row("Max Area:", f"{res['area_cm2']:.2f} cm²")
            
            circularity = res.get('circularity', 0.0)
            circ_lbl = "Smooth" if circularity >= 0.8 else ("Mod. irregular" if circularity >= 0.6 else "Irregular")
            self._add_stat_row("Boundary:", f"{circ_lbl} ({circularity:.2f})")
            
            p_val = f"{res['prob']:.2f}" if res['prob'] is not None else "Unknown"
            self._add_stat_row("Risk:", f"{res['label']} (p={p_val})")
            
            tk.Frame(self.stats_container, bg=self.card_border, height=1).pack(fill="x", pady=(10, 10))

    def clear_form(self):
        self.site_var.set("Breast")
        self.age_var.set("")
        self.image_path_var.set("")

        self.preview_original_img["pil"] = None
        self.preview_label.config(image="", text="No Image Selected")
        self.preview_label.image = None

        self.status_label.config(text="", fg=self.text_light)
        self.heatmap_active = False
        self.raw_original_img = None
        self.raw_masks = None
        self.raw_scores = None
        self.heatmap_btn.configure(text="🔥 Toggle Heatmap")
        self.update_run_button_state()
        
    def save_png(self):
        if self.current_canvas["img"] is None: return
        success, msg = export_canvas_png(self.current_canvas["img"], self.current_meta["image_path"])
        if success: messagebox.showinfo("Export Successful", f"Image saved: {msg}")
        else: messagebox.showerror("Export Failed", msg)

    def save_csv(self):
        if self.current_results["rows"] is None: return
        try:
            append_results_to_csv(self.current_meta["image_path"], self.current_meta["age"], self.current_results["rows"])
            messagebox.showinfo("Export Successful", "Data exported to CSV log.")
        except Exception as e:
            messagebox.showerror("Export Failed", str(e))

    def save_pdf(self):
        vis_img = self.current_results.get("vis_img")
        rows = self.current_results.get("rows")
        if vis_img is None:
            messagebox.showwarning("No Data", "Run an analysis first.")
            return
        
        # Default filename based on original image
        base = os.path.splitext(os.path.basename(self.current_meta.get("image_path", "report")))[0]
        default_name = f"{base}_report.pdf"
        
        path = filedialog.asksaveasfilename(
            defaultextension=".pdf",
            filetypes=[("PDF files", "*.pdf"), ("All files", "*.*")],
            initialfile=default_name,
            title="Save PDF Report"
        )
        if not path:
            return
        
        success, msg = generate_pdf_report(
            vis_img=vis_img,
            results_list=rows if rows else [],
            meta=self.current_meta,
            output_path=path
        )
        
        if success:
            messagebox.showinfo("Export Successful", f"PDF report saved:\n{msg}")
        else:
            messagebox.showerror("Export Failed", msg)

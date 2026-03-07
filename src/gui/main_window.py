import ttkbootstrap as ttk
from src.core.analyzer import Analyzer
from src.gui.dashboard_view import DashboardView


class AppWindow(ttk.Window):
    def __init__(self):
        super().__init__(themename="flatly")
        self.title("Ultrasound Lesion Analysis")
        
        # Make full screen
        w = self.winfo_screenwidth()
        h = self.winfo_screenheight()
        self.geometry(f"{w}x{h}+0+0")
        
        # Core Singletons
        self.analyzer = None  # Lazy loaded to speed up UI launch
        self.current_theme = "flatly"
        
        # Inject custom 'Soothing & Nurturing' palette overrides
        self._apply_custom_palette()
        
        # Global Header
        self._build_global_header()

        # Container for viewing
        self.container = ttk.Frame(self)
        self.container.pack(fill="both", expand=True)
        
        # Load initially — go straight to dashboard (no login)
        self.show_dashboard_view()

    def _build_global_header(self):
        import tkinter as tk
        # Subtle header: cream/white bar with lavender text instead of a bold colored strip
        self.header_frame = tk.Frame(self, bg="#F5F0FA", highlightthickness=0)
        self.header_frame.pack(fill="x", side="top")
        # Thin lavender accent line at the bottom of the header
        tk.Frame(self.header_frame, bg="#C8B1E4", height=2).pack(fill="x", side="bottom")
        
        self.title_lbl = tk.Label(self.header_frame, text="Ultrasound Lesion Analysis", font=("Segoe UI Semibold", 16), bg="#F5F0FA", fg="#7B5EA7")
        self.title_lbl.pack(side="left", padx=20, pady=10)
        
        # Right aligned controls
        self.controls_frame = tk.Frame(self.header_frame, bg="#F5F0FA")
        self.controls_frame.pack(side="right", padx=10)
        
        self.theme_btn = ttk.Button(self.controls_frame, text="🌙 Dark Mode", command=self.toggle_theme, bootstyle="secondary-outline")
        self.theme_btn.pack(side="left", padx=(0, 10))
        
    def _apply_custom_palette(self):
        """Overrides the default bootstrap colors with the 'Soothing & Nurturing' custom palette."""
        style = ttk.Style()
        is_light = self.current_theme == "flatly"
        
        bg_color = "#FDFBF7" if is_light else "#2c2c2c"
        header_bg = "#F5F0FA" if is_light else "#2a2a3d"
        header_fg = "#7B5EA7" if is_light else "#D4C4F0"
        user_fg = "#4A4A4A" if is_light else "#E6E6FA"
        accent_line = "#C8B1E4" if is_light else "#7B5EA7"
        
        # Info: Rich purple for main action buttons (strong contrast with white text)
        style.configure("info.TButton", background="#7B5EA7", bordercolor="#7B5EA7", foreground="white")
        style.map("info.TButton", background=[("active", "#6A4F96")])
        
        # Primary: Rich purple for navigation buttons
        style.configure("primary.TButton", background="#7B5EA7", bordercolor="#7B5EA7", foreground="white")
        style.map("primary.TButton", background=[("active", "#6A4F96")])
        
        # Success (OK): Gentle Sage Green
        style.configure("success.TButton", background="#9CAF88", bordercolor="#9CAF88", foreground="white")
        style.map("success.TButton", background=[("active", "#8A9F76")])
        
        # Danger/Error: Dusty Rose
        style.configure("danger.TButton", background="#DCAE96", bordercolor="#DCAE96", foreground="white")
        style.map("danger.TButton", background=[("active", "#CE9E85")])
        style.configure("danger.Outline.TButton", foreground="#DCAE96")
        
        # Warning: Warm Amber (for heatmap toggle — complements the palette)
        style.configure("warning.TButton", background="#D4A76A", bordercolor="#D4A76A", foreground="white")
        style.map("warning.TButton", background=[("active", "#C49A5E")])
        
        # Notebook tab styling
        tab_bg = "#F5F0FA" if is_light else "#3a3a3d"
        tab_fg = "#7B5EA7" if is_light else "#D4C4F0"
        tab_sel_bg = "#FDFBF7" if is_light else "#2c2c2c"
        style.configure("TNotebook", background=bg_color, borderwidth=0)
        style.configure("TNotebook.Tab", background=tab_bg, foreground=tab_fg, padding=[12, 6])
        style.map("TNotebook.Tab",
            background=[("selected", tab_sel_bg)],
            foreground=[("selected", tab_fg)]
        )
        
        # Round-toggle styling (lavender accent)
        style.configure("Roundtoggle.Toolbutton", background="#C8B1E4")
        
        # App background
        self.configure(bg=bg_color)
        
        # Update header bar colors if it exists
        if hasattr(self, 'header_frame'):
            self.header_frame.configure(bg=header_bg)
            for child in self.header_frame.winfo_children():
                try:
                    if isinstance(child, self.header_frame.__class__):
                        child.configure(bg=header_bg if child.winfo_height() > 3 else accent_line)
                except: pass
            if hasattr(self, 'controls_frame'):
                self.controls_frame.configure(bg=header_bg)
            if hasattr(self, 'title_lbl'):
                self.title_lbl.configure(bg=header_bg, fg=header_fg)
        
    def toggle_theme(self):
        if self.current_theme == "flatly":
            self.current_theme = "cyborg"
            self.theme_btn.configure(text="☀️ Light Mode")
        else:
            self.current_theme = "flatly"
            self.theme_btn.configure(text="🌙 Dark Mode")
        
        self.style.theme_use(self.current_theme)
        self._apply_custom_palette()
        
        # Reload the dashboard so it picks up the new dynamic variables
        self.show_dashboard_view()

    def _clear_container(self):
        for widget in self.container.winfo_children():
            widget.destroy()

    def show_dashboard_view(self):
        """
        Builds and displays the main dashboard.
        Loads the deep learning models on first call.
        """
        self._clear_container()
        
        # Start initial loading state by showing a clean full-screen loading message
        if self.analyzer is None:
            load_frame = ttk.Frame(self.container)
            load_frame.pack(fill="both", expand=True)
            
            lbl = ttk.Label(load_frame, text="Loading Deep Learning Environment...", font=("Segoe UI Semibold", 20))
            lbl.pack(expand=True)
            sub_lbl = ttk.Label(load_frame, text="This may take a moment on the first launch.", font=("Segoe UI", 12), bootstyle="secondary")
            sub_lbl.pack(pady=(0, 40))
            self.update_idletasks()
            
            try:
                self.analyzer = Analyzer(use_gpu=False)
            except Exception as e:
                lbl.configure(text=f"Failed to load AI Models: {e}", bootstyle="danger")
                sub_lbl.destroy()
                return
            
            load_frame.destroy()

        self.current_view = DashboardView(
            parent=self.container,
            analyzer=self.analyzer,
            profile={}
        )
        self.current_view.pack(fill="both", expand=True)

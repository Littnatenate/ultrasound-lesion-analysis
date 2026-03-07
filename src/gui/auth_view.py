import ttkbootstrap as ttk
from tkinter import messagebox
from src.core.firebase_db import FirebaseManager

class AuthView(ttk.Frame):
    def __init__(self, parent, firebase: FirebaseManager, on_login_success):
        super().__init__(parent)
        self.firebase = firebase
        self.on_login_success = on_login_success
        
        # Container background to contrast with the card
        self.configure(padding=50, bootstyle="dark")
        # Center the container
        self.columnconfigure(0, weight=1)
        self.rowconfigure(0, weight=1)

        # Card Container (elevated look)
        self.card = ttk.Frame(self, padding=50, bootstyle="default")
        self.card.grid(row=0, column=0, sticky="")
        
        self.title_lbl = ttk.Label(self.card, text="Welcome Back", font=("Segoe UI Semibold", 28))
        self.title_lbl.pack(pady=(0, 5))
        
        self.subtitle_lbl = ttk.Label(self.card, text="Sign in to access lesion analysis tools", font=("Segoe UI", 11), foreground="gray")
        self.subtitle_lbl.pack(pady=(0, 30))
        
        # Mode Tracker (login | register)
        self.mode = "login"
        
        self._build_fields()
        
    def _clear_fields(self):
        if hasattr(self, "fields_frame"):
            for widget in self.fields_frame.winfo_children():
                widget.destroy()
            self.fields_frame.destroy()
            del self.fields_frame

    def _build_fields(self):
        self._clear_fields()
        
        self.fields_frame = ttk.Frame(self.card)
        self.fields_frame.pack(fill="x", expand=True)

        # Common Fields
        ttk.Label(self.fields_frame, text="Email Address", font=("Segoe UI Semibold", 10)).pack(anchor="w", pady=(0, 5))
        self.email_ent = ttk.Entry(self.fields_frame, width=45)
        self.email_ent.pack(fill="x", pady=(0, 20), ipady=8)

        ttk.Label(self.fields_frame, text="Password", font=("Segoe UI Semibold", 10)).pack(anchor="w", pady=(0, 5))
        self.password_ent = ttk.Entry(self.fields_frame, width=45, show="*")
        self.password_ent.pack(fill="x", pady=(0, 20), ipady=8)

        # Register Specific Fields
        if self.mode == "register":
            self.title_lbl.configure(text="Create an Account")
            self.subtitle_lbl.configure(text="Join to start tracking and analyzing ultrasound scans")
            
            ttk.Label(self.fields_frame, text="Full Name", font=("Segoe UI Semibold", 10)).pack(anchor="w", pady=(0, 5))
            self.name_ent = ttk.Entry(self.fields_frame, width=45)
            self.name_ent.pack(fill="x", pady=(0, 20), ipady=8)
            
            ttk.Label(self.fields_frame, text="Date of Birth", font=("Segoe UI Semibold", 10)).pack(anchor="w", pady=(0, 5))
            self.dob_ent = ttk.DateEntry(self.fields_frame, width=42, bootstyle="info", startdate=None)
            self.dob_ent.pack(fill="x", pady=(0, 20))
            
            action_text = "Sign Up"
            toggle_text = "Already have an account? Log In"
            self.submit_btn = ttk.Button(self.fields_frame, text=action_text, command=self.handle_register, bootstyle="info")
        else:
            self.title_lbl.configure(text="Welcome Back")
            self.subtitle_lbl.configure(text="Sign in to access lesion analysis tools")
            action_text = "Log In"
            toggle_text = "Don't have an account? Sign Up"
            self.submit_btn = ttk.Button(self.fields_frame, text=action_text, command=self.handle_login, bootstyle="info")
            
        self.submit_btn.pack(fill="x", pady=(10, 15), ipady=8)
        
        self.toggle_btn = ttk.Button(self.fields_frame, text=toggle_text, command=self.toggle_mode, bootstyle="link")
        self.toggle_btn.pack(fill="x")

    def toggle_mode(self):
        self.mode = "register" if self.mode == "login" else "login"
        self._build_fields()

    def handle_login(self):
        email = self.email_ent.get().strip()
        password = self.password_ent.get()
        
        if not email or not password:
            messagebox.showerror("Error", "Please fill in all fields.")
            return

        self.submit_btn.configure(state="disabled", text="Logging in...")
        self.update_idletasks()
        
        success, result = self.firebase.login(email, password)
        if success:
            self.on_login_success(result)  # Pass profile to main window
        else:
            messagebox.showerror("Login Failed", result)
            self.submit_btn.configure(state="normal", text="Log In")

    def handle_register(self):
        email = self.email_ent.get().strip()
        password = self.password_ent.get()
        name = self.name_ent.get().strip()
        
        # Get the selected date from the DateEntry widget
        dob_date = self.dob_ent.entry.get() if hasattr(self.dob_ent, "entry") else ""
        
        if not all([email, password, name, dob_date]):
            messagebox.showerror("Error", "Please fill in all fields.")
            return
            
        self.submit_btn.configure(state="disabled", text="Creating Account...")
        self.update_idletasks()
        
        # Pass the dob string correctly
        success, result = self.firebase.sign_up(name, dob_date, email, password)
        if success:
            messagebox.showinfo("Success", "Account created! Please log in.")
            self.toggle_mode()
        else:
            messagebox.showerror("Registration Failed", result)
            self.submit_btn.configure(state="normal", text="Sign Up")

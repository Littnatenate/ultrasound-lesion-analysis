import os
import sys

# Add the project root to sys.path so that "from src.*" imports work when running this file directly
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.gui.main_window import AppWindow

def main():
    import traceback
    try:
        app = AppWindow()
        app.mainloop()
    except Exception:
        traceback.print_exc()
        input("Press Enter to exit...")

if __name__ == "__main__":
    main()

"""
Desktop launcher: starts FastAPI backend + opens pywebview window.
Run this to launch the app as a native desktop window.

Usage: python web/backend/launcher.py
"""
import os
import sys
import threading
import time

# Ensure web/backend is on the path
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)


def start_server():
    """Run the FastAPI server in a background thread."""
    import uvicorn
    uvicorn.run("api:app", host="127.0.0.1", port=8000, log_level="info")


def main():
    # Start FastAPI in background
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()
    
    # Wait for the server to be ready
    import urllib.request
    for _ in range(30):
        try:
            urllib.request.urlopen("http://127.0.0.1:8000/health")
            break
        except Exception:
            time.sleep(1)
    
    # Open native window
    import webview
    
    # In production, serve from FastAPI (which mounts the React build)
    # In development, point to the Vite dev server
    frontend_dist = os.path.join(backend_dir, "..", "frontend", "dist")
    if os.path.isdir(frontend_dist):
        url = "http://127.0.0.1:8000"  # FastAPI serves the built React app
    else:
        url = "http://127.0.0.1:5173"  # Vite dev server
    
    webview.create_window(
        "Ultrasound Lesion Analysis",
        url,
        width=1400,
        height=900,
        min_size=(900, 600),
    )
    webview.start()


if __name__ == "__main__":
    main()

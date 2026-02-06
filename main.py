import uvicorn
import os
import sys
import subprocess
import webbrowser
import threading
import time

def install_package(package):
    print(f"Installing {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

# Check if running as exe
def is_frozen():
    return getattr(sys, 'frozen', False) and hasattr(sys, '_MEIPASS')

# Only try to install packages if not running as exe
if not is_frozen():
    try:
        import reportlab
    except ImportError:
        install_package("reportlab")

def open_browser():
    """Open browser after a short delay"""
    time.sleep(2)
    webbrowser.open("http://127.0.0.1:8000")

if __name__ == "__main__":
    # Add the current directory to sys.path to ensure backend package is found
    if is_frozen():
        # When running as exe, use the temporary folder created by PyInstaller
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    
    sys.path.insert(0, base_path)
    
    # Start browser in a separate thread
    threading.Thread(target=open_browser, daemon=True).start()
    
    # Run the server
    # reload should be disabled when running as exe
    reload = not is_frozen()
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=reload, log_level="info")

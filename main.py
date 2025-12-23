import uvicorn
import os
import sys
import subprocess

def install_package(package):
    print(f"Installing {package}...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import reportlab
except ImportError:
    install_package("reportlab")

if __name__ == "__main__":
    # Add the current directory to sys.path to ensure backend package is found
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    
    # Run the server
    # reload=True enabled as requested
    uvicorn.run("backend.app.main:app", host="127.0.0.1", port=8000, reload=True, log_level="info")

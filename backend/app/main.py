import hashlib
import sys

# Compatibility patch for ReportLab on various Python versions/environments
# Some versions of ReportLab 4.x use 'usedforsecurity=False' which is not supported
# in Python < 3.9 or certain OpenSSL builds.
_original_md5 = hashlib.md5
def _patched_md5(*args, **kwargs):
    kwargs.pop('usedforsecurity', None)
    return _original_md5(*args, **kwargs)
hashlib.md5 = _patched_md5

from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List
import uvicorn
import webbrowser
import threading
import time
import os
import shutil
import tempfile
import io
import zipfile
from datetime import datetime
from .services.parser import parse_fcs
from .services.pdf_renderer import generate_pdf_report
from .models import FCSMetadata

app = FastAPI(title="FCS Export Tool")

# CORS setup for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- NEW: Serve Frontend Static Files ---
# Get the absolute path to the frontend directory
base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
frontend_dir = os.path.join(base_dir, "frontend")

# Mount the frontend directory to the root "/"
# We mount index.html specifically or use StaticFiles with html=True
app.mount("/assets", StaticFiles(directory=os.path.join(frontend_dir, "assets")), name="assets")

@app.get("/")
def read_index():
    from fastapi.responses import FileResponse
    return FileResponse(os.path.join(frontend_dir, "index.html"))

@app.post("/api/parse", response_model=List[FCSMetadata])
async def parse_files(files: List[UploadFile] = File(...)):
    results = []
    
    # Create a temporary directory to store uploaded files for processing
    # We do this because flowio typically expects a file path or a seekable stream,
    # and saving to disk ensures robust handling of potentially large files.
    with tempfile.TemporaryDirectory() as temp_dir:
        for file in files:
            temp_path = os.path.join(temp_dir, file.filename)
            try:
                # Save uploaded file to temp path
                with open(temp_path, "wb") as buffer:
                    shutil.copyfileobj(file.file, buffer)
                
                # Parse the file
                metadata = parse_fcs(temp_path, file.filename)
                results.append(metadata)
                
            except Exception as e:
                # Return error entry if one fails, rather than crashing whole batch
                results.append(FCSMetadata(
                    filename=file.filename,
                    channels=[],
                    error=f"Upload/Parse failed: {str(e)}"
                ))
                
    return results

@app.post("/api/export/pdf")
async def export_pdf(metadata: FCSMetadata):
    try:
        pdf_bytes = generate_pdf_report(metadata)
        # Set filename for download
        filename = f"{metadata.filename.replace('.fcs', '').replace('.FCS', '')}_report.pdf"
        return Response(
            content=pdf_bytes, 
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/pdf/zip")
async def export_pdf_zip(metadata_list: List[FCSMetadata]):
    try:
        print(f"DEBUG: Starting batch export for {len(metadata_list)} files")
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for i, meta in enumerate(metadata_list):
                print(f"DEBUG: Generating PDF {i+1}/{len(metadata_list)} for {meta.filename}")
                try:
                    pdf_bytes = generate_pdf_report(meta)
                    clean_name = meta.filename.replace('.fcs', '').replace('.FCS', '')
                    # Ensure unique filename in zip
                    zip_file.writestr(f"{clean_name}_report.pdf", pdf_bytes)
                except Exception as inner_e:
                    print(f"ERROR generating PDF for {meta.filename}: {inner_e}")
                    # Continue with other files instead of failing whole batch
                    continue
                
        zip_buffer.seek(0)
        return Response(
            content=zip_buffer.getvalue(), 
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=FCS_Reports_Batch.zip"}
        )
    except Exception as e:
        print(f"CRITICAL ERROR in batch export: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")

if __name__ == "__main__":
    # Open browser after a slight delay
    def open_browser():
        time.sleep(1.5)
        webbrowser.open("http://127.0.0.1:8000") # This will eventually point to the served frontend

    # threading.Thread(target=open_browser).start()
    # For dev mode, we just run uvicorn directly
    start_server()

from fastapi import FastAPI, UploadFile, File, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from typing import List, Dict, Any
import csv
import uuid
import flowio
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
from .services.pdf_renderer import generate_pdf_report, generate_panel_summary_pdf
from .models import FCSMetadata

app = FastAPI(title="FCS Export Tool")

CACHE_DIR = os.path.join(tempfile.gettempdir(), "fastvolt_cache")
os.makedirs(CACHE_DIR, exist_ok=True)
FILE_CACHE: Dict[str, Dict[str, str]] = {}

def cache_upload(file: UploadFile) -> Dict[str, str]:
    file_id = str(uuid.uuid4())
    original_name = file.filename or f"{file_id}.fcs"
    suffix = os.path.splitext(original_name)[1] or ".fcs"
    cached_path = os.path.join(CACHE_DIR, f"{file_id}{suffix}")

    with open(cached_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    FILE_CACHE[file_id] = {
        "path": cached_path,
        "filename": original_name,
    }

    return {
        "file_id": file_id,
        "path": cached_path,
        "filename": original_name,
    }

def pop_cached_file(file_id: str) -> Dict[str, str]:
    entry = FILE_CACHE.pop(file_id, None)
    if not entry:
        return {}
    try:
        os.remove(entry["path"])
    except OSError:
        pass
    return entry

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

    # Cache uploaded files for later FCS export
    for file in files:
        file_id = None
        cached_path = None
        filename = file.filename or "uploaded.fcs"
        try:
            cached = cache_upload(file)
            file_id = cached["file_id"]
            cached_path = cached["path"]
            filename = cached["filename"]

            metadata = parse_fcs(cached_path, filename)
            metadata.file_id = file_id
            results.append(metadata)

        except Exception as e:
            if file_id:
                pop_cached_file(file_id)
            results.append(FCSMetadata(
                filename=filename,
                file_id=file_id,
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

@app.post("/api/export/fcs")
async def export_fcs(metadata: FCSMetadata):
    if not metadata.file_id:
        raise HTTPException(status_code=400, detail="Missing file_id for export")

    cache_entry = FILE_CACHE.get(metadata.file_id)
    if not cache_entry:
        raise HTTPException(status_code=404, detail="Cached file not found")

    try:
        fd = flowio.FlowData(cache_entry["path"])
        text = dict(fd.text)

        channel_map = {ch.name: ch for ch in metadata.channels}
        for idx, channel_name in enumerate(fd.pnn_labels, start=1):
            channel = channel_map.get(channel_name)
            if not channel:
                continue

            if not channel.label:
                continue

            text[f"p{idx}s"] = channel.label

        output_name = os.path.splitext(cache_entry["filename"])[0]
        output_filename = f"{output_name}_mapped.fcs"
        output_path = os.path.join(tempfile.gettempdir(), f"{metadata.file_id}_mapped.fcs")

        fd.write_fcs(output_path, metadata=text)
        with open(output_path, "rb") as output_file:
            fcs_bytes = output_file.read()

        try:
            os.remove(output_path)
        except OSError:
            pass

        pop_cached_file(metadata.file_id)

        return Response(
            content=fcs_bytes,
            media_type="application/octet-stream",
            headers={"Content-Disposition": f"attachment; filename={output_filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/summary")
async def export_summary(payload: Dict[str, Any]):
    try:
        experiment_name = payload.get("experiment_name", "experiment")
        panels = payload.get("panels", [])

        def normalize_channel_name(name: str) -> str:
            return name.replace("-A", "").replace("-H", "") if name else ""

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "experiment_name",
            "panel_name",
            "sample_filename",
            "channel_name",
            "label",
            "voltage",
            "compensation_id",
        ])

        for panel in panels:
            panel_name = panel.get("name", "")
            compensation_id = panel.get("compensation_id", "")
            channel_map_default = panel.get("channel_map_default", {})
            samples = panel.get("samples", [])

            for sample in samples:
                filename = sample.get("filename", "")
                channels = sample.get("channels", [])
                override_map = sample.get("channel_map_override", {})

                merged = {}
                for ch in channels:
                    channel_name = ch.get("name", "")
                    base_name = normalize_channel_name(channel_name)
                    default_entry = channel_map_default.get(base_name, {})
                    override_entry = override_map.get(base_name, {})

                    label = (
                        override_entry.get("label")
                        or default_entry.get("label")
                        or ch.get("label")
                        or ""
                    )
                    voltage = ch.get("voltage")

                    if base_name not in merged:
                        merged[base_name] = {
                            "label": label,
                            "voltage": voltage,
                        }
                    else:
                        if not merged[base_name]["label"] and label:
                            merged[base_name]["label"] = label
                        if merged[base_name]["voltage"] is None and voltage is not None:
                            merged[base_name]["voltage"] = voltage

                for base_name, values in merged.items():
                    writer.writerow([
                        experiment_name,
                        panel_name,
                        filename,
                        base_name,
                        values.get("label", ""),
                        "" if values.get("voltage") is None else values.get("voltage"),
                        compensation_id,
                    ])

        csv_bytes = output.getvalue().encode("utf-8")
        safe_name = experiment_name.replace(" ", "_") or "experiment"
        filename = f"{safe_name}_summary.csv"

        return Response(
            content=csv_bytes,
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/fcs/zip")
async def export_fcs_zip(metadata_list: List[FCSMetadata]):
    try:
        zip_buffer = io.BytesIO()
        with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
            for metadata in metadata_list:
                if not metadata.file_id:
                    continue

                cache_entry = FILE_CACHE.get(metadata.file_id)
                if not cache_entry:
                    continue

                try:
                    fd = flowio.FlowData(cache_entry["path"])
                    text = dict(fd.text)

                    channel_map = {ch.name: ch for ch in metadata.channels}
                    for idx, channel_name in enumerate(fd.pnn_labels, start=1):
                        channel = channel_map.get(channel_name)
                        if not channel or not channel.label:
                            continue
                        text[f"p{idx}s"] = channel.label

                    output_path = os.path.join(tempfile.gettempdir(), f"{metadata.file_id}_mapped.fcs")
                    fd.write_fcs(output_path, metadata=text)
                    with open(output_path, "rb") as output_file:
                        fcs_bytes = output_file.read()

                    try:
                        os.remove(output_path)
                    except OSError:
                        pass

                    clean_name = metadata.filename.replace(".fcs", "").replace(".FCS", "")
                    zip_file.writestr(f"{clean_name}_mapped.fcs", fcs_bytes)

                    pop_cached_file(metadata.file_id)
                except Exception:
                    continue

        zip_buffer.seek(0)
        return Response(
            content=zip_buffer.getvalue(),
            media_type="application/zip",
            headers={"Content-Disposition": "attachment; filename=FCS_Mapped_Batch.zip"}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/export/panel/pdf")
async def export_panel_pdf(payload: Dict[str, Any]):
    try:
        panel_name = payload.get("panel_name", "Panel")
        channel_map_default = payload.get("channel_map_default", {})
        samples = payload.get("samples", [])
        compensation = payload.get("compensation")

        pdf_bytes = generate_panel_summary_pdf(panel_name, samples, channel_map_default, compensation)
        safe_name = panel_name.replace(" ", "_") or "panel"
        filename = f"{safe_name}_summary.pdf"
        return Response(
            content=pdf_bytes,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    except Exception as e:
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

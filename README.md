# FASTVOLT

FASTVOLT is a lightweight local web application designed for researchers to quickly extract voltage and compensation data from Flow Cytometry Standard (FCS) files and generate professional, lab-ready A4 PDF reports.

## Features

- **Fast Parsing**: Extract metadata from FCS files in seconds using `flowio`.
- **Instrument Awareness**: Automatically detects instrument model and serial numbers (optimized for CytoFLEX).
- **A4 PDF Reports**: Generates professional PDF records with institutional headers and space for manual entry.
- **Batch Export**: Process multiple files at once and download them as a ZIP archive.
- **Intuitive UI**: Simple drag-and-drop web interface.

## Prerequisites

- Python 3.10 or higher
- Chrome, Edge, or Safari browser

## Installation

1. **Clone the repository**:
   ```bash
   git clone https://github.com/PanCodeInventory/FASTVOLT.git
   cd FASTVOLT
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

Run the application using the following command:

```bash
python main.py
```

The application will automatically open your default browser to `http://127.0.0.1:10598`.

1. **Upload**: Drag and drop your `.fcs` files into the blue drop zone.
2. **Review**: Check the extracted instrument info and data tables on the screen.
3. **Export**: 
   - Click **Export PDF** on a specific file card for an individual report.
   - Click **Export All (PDF ZIP)** at the top to download reports for all loaded files.

### Running in Background

To run the application in the background, use `nohup`:

```bash
nohup python3 main.py > nohup.out 2>&1 &
```

View the logs:

```bash
tail -f nohup.out
```

### Troubleshooting: Port Already in Use

If you cannot access the application, the port `10598` may be occupied by a previous process.

**Check port usage:**

```bash
lsof -i :10598
```

**Kill the process occupying the port:**

```bash
fuser -k 10598/tcp
```

Or manually kill by PID:

```bash
kill -9 <PID>
```

Then restart the application.

## Tech Stack

- **Backend**: FastAPI (Python)
- **PDF Engine**: ReportLab
- **Parsing**: flowio
- **Frontend**: Vue.js (CDN), Tailwind CSS

## License

This project is developed for laboratory record enhancement.

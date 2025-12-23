# Quickstart: FCS Export Tool

## Prerequisites

- Python 3.10+
- (Optional) Node.js if you plan to heavily modify the frontend assets manually.

## Installation

1. **Clone the repository**:
   ```bash
   git clone <repo-url>
   cd FASTVOLT
   ```

2. **Create Virtual Environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *(Key packages: `fastapi`, `uvicorn`, `python-multipart`, `flowio`, `matplotlib`)*

## Running the Application

1. **Start the Server**:
   ```bash
   # From the project root
   python main.py
   ```
   *This script will launch the FastAPI backend and automatically open `http://localhost:8000` in your default browser.*

## Usage

1. **Drag & Drop**: Drag your `.fcs` files onto the drop zone.
2. **Review**: Check the extracted metadata (Instrument info, Voltages, Compensation) on the cards.
3. **Export**:
   - Click "Export PNG" on individual cards for a single report.
   - Click "Export All (ZIP)" in the top right to download everything at once.

## Development

- **Backend**: Located in `backend/`. 
  - `backend/app/main.py`: API Routes
  - `backend/app/services/parser.py`: FCS Parsing Logic
  - `backend/app/services/renderer.py`: PNG Generation Logic
- **Frontend**: Located in `frontend/`. 
  - `frontend/index.html`: Vue.js Application
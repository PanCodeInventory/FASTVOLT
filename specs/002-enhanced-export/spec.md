# Feature Specification: Enhanced FCS Export for Lab Records

**Feature Branch**: `002-enhanced-export`
**Created**: 2025-12-22
**Status**: Draft
**Input**: User description: "I want to improve the export part so that it can be directly used in experimental records; The changes I want are: 1. Add table header (you can ask me specifically later) 2. Add experiment information (experiment name, experimenter) 3. Add FCS metadata display (instrument brand and model, test date) 4. Export format only PDF, ratio A4 5. Content arrangement from top to bottom: header - experiment info - FCS metadata - voltage/compensation"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prepare Report for Manual Entry (Priority: P1)

As a researcher, I want the generated report to include dedicated blank sections for "Experiment Name" and "Experimenter" so that I can fill them in by hand after printing, as per our lab's physical record protocols.

**Why this priority**: Aligning with the specific lab requirement for manual documentation.

**Independent Test**: Generate a PDF and verify it contains clear, labeled blank lines or underlines for Experiment Name and Experimenter.

**Acceptance Scenarios**:

1. **Given** a generated PDF report, **When** I look at the Experiment Info section, **Then** I see "Experiment Name: ________________" and "Experimenter: ________________".

---

### User Story 2 - Generate A4 PDF Report (Priority: P2)

As a researcher, I want to export the FCS data as a standardized A4 PDF document with a specific layout (Header -> Exp Info -> FCS Metadata -> Data) so that I can print it or attach it digitally to my formal lab records.

**Why this priority**: Core deliverable of this feature request; replaces the previous PNG export.

**Independent Test**: Load an FCS file, click "Export PDF", and verify the file is a valid PDF with A4 dimensions and the correct vertical layout.

**Acceptance Scenarios**:

1. **Given** a loaded FCS file, **When** I click "Export PDF", **Then** a file save dialog appears for a `.pdf` file.
2. **Given** the exported PDF, **When** I open it, **Then** it has A4 page size and follows the vertical layout: Header ("Institute of Immunology, USTC, Flow Cytometry Form") -> Experiment Info (Blank lines) -> Instrument Metadata (Auto-extracted) -> Voltage Table -> Compensation Matrix.

---

### User Story 3 - Automatic Metadata Extraction (Priority: P3)

As a researcher, I want the system to automatically extract instrument brand, model, and test date from the FCS file so that I don't have to type them manually.

**Why this priority**: Improves efficiency and accuracy of the record.

**Independent Test**: Load a known FCS file with metadata, verify the UI or export displays the correct Instrument Model and Date.

**Acceptance Scenarios**:

1. **Given** an FCS file with `$CYT` (Cytometer) and `$DATE` keywords, **When** I load it, **Then** the export preview shows the correct Instrument Brand/Model and Date.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST include labeled blank lines (placeholders) for "Experiment Name" and "Experimenter" in the PDF for manual handwriting.
- **FR-002**: System MUST extract and display Instrument Brand/Model (from `$CYT` or `$MODEL` keywords) and Test Date (from `$DATE`).
- **FR-003**: System MUST generate reports in **PDF format only** (replacing or hiding previous PNG/CSV options).
- **FR-004**: The PDF page size MUST be **A4** (210 x 297 mm) in Portrait orientation.
- **FR-005**: The PDF content MUST follow this vertical order:
    1.  **Header**: Fixed text "Institute of Immunology, USTC, Flow Cytometry Form".
    2.  **Experiment Info**: Labeled blank lines for handwriting.
    3.  **FCS Metadata**: Instrument Brand/Model, Test Date (Extracted).
    4.  **Voltage Table**: Channel/Voltage data.
    5.  **Compensation Matrix**: The matrix values.
- **FR-006**: The report SHOULD accommodate multi-page content if the tables are too long for one A4 page.

### Key Entities

- **PDF Report**: The generated A4 artifact with a structured lab-form layout.
- **FCS Metadata**: Expanded set of extracted fields including Instrument info.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Generated PDF strictly adheres to A4 dimensions (within 1mm tolerance).
- **SC-002**: Placeholder lines for Experiment Name/Person are clearly visible and provide enough space for standard handwriting.
- **SC-003**: Instrument Model and Date are correctly extracted for >95% of standard FCS 3.0/3.1 files.
- **SC-004**: "Export PDF" action completes in under 3 seconds for a typical single file.
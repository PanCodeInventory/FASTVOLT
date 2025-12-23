# Feature Specification: FCS Data Export Tool

**Feature Branch**: `001-fcs-export-tool`
**Created**: 2025-12-22
**Status**: Draft
**Input**: User description: "The project is designed to quickly read FCS files and export voltage and compensation as PNG format (with timestamps and instrument info), and have a very intuitive user interface. Focus on PNG perfection and include instrument details to replace manual handwriting."

## Clarifications

### Session 2025-12-22
- Q: 仪器信息内容 → A: 包含型号 ($MODEL)、序列号 ($CYTSN) 和仪器名称 ($CYT)。
- Q: PNG 导出布局 → A: 页眉布局：顶部显示文件名、日期及仪器信息；下方为数据表。
- Q: 批量导出格式 → A: ZIP 压缩包：所有 PNG 打包下载。
- Q: 界面中的仪器信息展示 → A: 预览卡片展示：UI 界面每个文件卡片顶部直接显示仪器关键信息。

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Load and View FCS Data (Priority: P1)

As a lab researcher, I want to load an FCS file and immediately see its instrument metadata, voltage settings, and compensation matrix so that I can verify the experimental conditions without opening complex analysis software like FlowJo.

**Why this priority**: Core functionality; without reading and displaying the file, no export is possible.

**Independent Test**: Can be tested by providing a sample FCS file and verifying the UI displays the correct instrument info, voltage and compensation values.

**Acceptance Scenarios**:

1. **Given** the application is open, **When** I drag and drop an FCS file onto the interface, **Then** the file parses successfully and displays the Instrument Info, Voltage table, and Compensation matrix.
2. **Given** an invalid or corrupted file, **When** I attempt to load it, **Then** an error message clearly explains the format is unsupported.

---

### User Story 2 - Export Data to Image (PNG) (Priority: P2)

As a researcher, I want to export the displayed data as a high-quality PNG image with a structured header (file name, timestamp, instrument SN/Model) so that I can directly attach it to my lab notebook.

**Why this priority**: Solves the primary pain point of "handwriting" records.

**Independent Test**: Load a file, click export PNG, and verify the resulting image contains the header, data tables, and a visible timestamp.

**Acceptance Scenarios**:

1. **Given** loaded FCS data, **When** I click "Export to PNG", **Then** a PNG image is generated with a dedicated header section.
2. **Given** multiple files are loaded, **When** I select "Export All", **Then** a single ZIP file containing all PNGs is downloaded.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST accept standard FCS format files (Flow Cytometry Standard) as input.
- **FR-002**: System MUST parse and extract the "Spillover" matrix, Channel Voltage settings, and Instrument Metadata ($MODEL, $CYTSN, $CYT).
- **FR-003**: System MUST provide a Graphical User Interface (GUI) as a locally-running Web App.
- **FR-004**: System MUST display results in a card-based layout, showing instrument info in the card header.
- **FR-005**: System MUST allow exporting data to a PNG image file with a formal header layout.
- **FR-006**: The exported PNG MUST include a visible timestamp of when the export occurred.
- **FR-007**: System MUST support batch processing, providing multiple PNG exports via a single ZIP archive download.
- **FR-008**: System MUST focus on data accuracy and visual clarity for publication/notebook ready output.

### Key Entities

- **FCS File**: The source binary file containing flow cytometry data and text metadata.
- **Instrument Metadata**: Set containing Model, Serial Number, and Instrument Name.
- **Voltage Table**: A list mapping channel names to their voltage/gain settings.
- **Compensation Matrix**: A 2D matrix describing spectral overlap between channels.
- **Export ZIP**: A compressed archive containing individual PNG reports for batch exports.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Time from "File Selected" to "Data Displayed" is under 2 seconds for a standard 10MB FCS file.
- **SC-002**: Time from "Opening App" to "Exported PNG ready" is under 1 minute.
- **SC-003**: Exported values match reference values with 100% accuracy.
- **SC-004**: 95% of instrument metadata fields are correctly mapped for CytoFLEX standard files.
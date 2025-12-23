# Feature Specification: Conditional A4 Export Pagination

**Feature Branch**: `001-export-pagination`  
**Created**: 2025-12-23  
**Status**: Draft  
**Input**: User description: "更新最后导出的展示效果：增加判断标准，如果一张 A4 可以容纳则单页展示，否则将 Compensation Matrix (%) 移至第二页。"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Single Page Export (Priority: P1)

As a researcher, I want the system to automatically fit the entire report on a single A4 page when the content (Header, Exp Info, Metadata, Voltage, and Compensation) is small enough, so that I can save paper and view all settings at once.

**Why this priority**: Core optimization to ensure compact reports remain efficient and readable on one page.

**Independent Test**: Load an FCS file with few channels (small voltage table and matrix), export to PDF, and verify it is exactly 1 page.

**Acceptance Scenarios**:

1. **Given** an FCS file where total content height < A4 page height, **When** I click "Export PDF", **Then** the resulting PDF has 1 page containing all sections including the Compensation Matrix.

---

### User Story 2 - Split Page Export (Priority: P2)

As a researcher, I want the system to intelligently move the Compensation Matrix to a second page if the Voltage table or other sections are too long to fit on the first A4 page, so that the document remains professional and content is not clipped.

**Why this priority**: Prevents layout corruption and ensures all data is presented clearly even when the instrument configuration is complex.

**Independent Test**: Load an FCS file with many channels (long voltage table), export to PDF, and verify the Compensation Matrix starts on page 2.

**Acceptance Scenarios**:

1. **Given** an FCS file where the combined height of Header, Exp Info, Metadata, and Voltage Table leaves insufficient room for the Compensation Matrix on page 1, **When** I click "Export PDF", **Then** the PDF contains 2 pages.
2. **Given** the 2-page PDF, **When** I open it, **Then** the Compensation Matrix (%) is displayed entirely on the second page.

---

### Edge Cases

- **Large Compensation Matrix**: What happens if the Compensation Matrix itself is larger than a single A4 page? (Assumption: It will span multiple pages from page 2 onwards).
- **Voltage Table Overflow**: What if the Voltage Table alone exceeds page 1? (Assumption: Voltage table continues to page 2, and Compensation Matrix follows it).

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST calculate the total height of rendered sections (Header, Exp Info, Metadata, Voltage Table, and Compensation Matrix) before final PDF generation.
- **FR-002**: System MUST use A4 (210 x 297 mm) as the standard reference for layout height.
- **FR-003**: System MUST provide a "Single Page" layout if all sections fit within the A4 height boundary.
- **FR-004**: System MUST trigger a page break BEFORE the "Compensation Matrix (%)" section if the matrix cannot fit on the remainder of page 1.
- **FR-005**: If a page break is triggered, the Compensation Matrix MUST start at the top of page 2.
- **FR-006**: The system MUST preserve the vertical order defined in the previous specification (Header -> Exp Info -> FCS Metadata -> Voltage Table -> Compensation Matrix).

### Key Entities

- **PDF Layout Manager**: The logic responsible for calculating component heights and deciding page breaks.
- **A4 Page**: The standardized output format constraint.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of reports where content height fits A4 are generated as single-page PDFs.
- **SC-002**: 100% of reports where content exceeds A4 move the Compensation Matrix to the start of a new page rather than clipping it at the bottom of page 1.
- **SC-003**: Layout calculation adds less than 500ms to the total PDF generation time.
- **SC-004**: Resulting PDF file size remains optimized (under 2MB for typical reports).
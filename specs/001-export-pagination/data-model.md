# Data Model: Conditional A4 Export Pagination

**Feature**: `001-export-pagination`

## Logical Entities

### PDF Report Layout
This entity represents the structure of the generated artifact. It is not persisted to the database but is constructed dynamically during export.

| Field | Type | Description |
|-------|------|-------------|
| **Header** | Section | Fixed text "Institute of Immunology..." |
| **Experiment Info** | Section | Labeled blank lines for handwriting. |
| **FCS Metadata** | Section | Key-value pairs (Model, Date, Filename). |
| **Voltage Table** | Table | List of channels and voltages. |
| **Compensation Matrix** | Table | NxN matrix of spillover values. |

### Layout Rules
1.  **Page Size**: A4 (210mm x 297mm).
2.  **Margins**: 1cm all around.
3.  **Break Condition**: If `Sum(Height(Header...Voltage)) + Height(Matrix) > Printable_Height`, the Matrix is moved to Page 2.

## Database Changes
*None.* This feature uses existing `FCSMetadata` and `Channel`/`Compensation` structures.

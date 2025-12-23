# Data Model: Enhanced FCS Export

**Feature**: `002-enhanced-export`
**Date**: 2025-12-22

## Entities

### PDFReportConfig
*Configuration for generating the lab report.*

| Field | Type | Description |
|-------|------|-------------|
| `institution_name` | `string` | Fixed: "Institute of Immunology, USTC, Flow Cytometry Form" |
| `page_size` | `string` | Fixed: "A4" |
| `include_handwriting_lines` | `boolean` | Default: True (Experiment Name, Experimenter) |

### FCSMetadata (Refinement)
*Metadata fields extracted for the report.*

| Field | Type | Description |
|-------|------|-------------|
| `instrument_model` | `string` | From `$MODEL` or `$CYT` |
| `test_date` | `string` | From `$DATE` |
| `filename` | `string` | Name of the source file |

## Relationships

1. **One PDF Report** represents **One FCS File**.
2. **One Batch Export** combines **Many PDF Reports** into **One ZIP Archive**.

## State Transitions

1. **Extraction**: Parse FCS → `FCSMetadata` populated.
2. **Rendering**: `FCSMetadata` + `PDFReportConfig` → `PDF Stream`.
3. **Delivery**: Stream PDF to user OR Zip multiple streams.

# Data Model: FCS Export Tool

**Feature**: `001-fcs-export-tool`
**Date**: 2025-12-22

## Entities

### FCSMetadata
*Represents the extracted metadata from a single FCS file.*

| Field | Type | Description |
|-------|------|-------------|
| `filename` | `string` | Original name of the uploaded file. |
| `timestamp` | `string` (ISO8601) | The `$DATE` + `$BTIM` (time) from FCS header. |
| `instrument` | `InstrumentInfo` | Device details (Model, SN, Name). |
| `channels` | `List[ChannelInfo]` | List of channel configurations. |
| `compensation` | `CompensationMatrix` (Optional) | The spillover matrix if present. |
| `error` | `string` (Optional) | If parsing failed, the reason why. |

### InstrumentInfo
*Details about the flow cytometer device.*

| Field | Type | Description |
|-------|------|-------------|
| `model` | `string` | Instrument Model (from `$MODEL`). |
| `serial_number` | `string` | Serial Number (from `$CYTSN`). |
| `name` | `string` | Instrument Name (from `$CYT`). |

### ChannelInfo
*Details for a specific flow cytometry channel.*

| Field | Type | Description |
|-------|------|-------------|
| `name` | `string` | Short name (e.g., "FITC-A"). |
| `label` | `string` (Optional) | Long label/marker name (e.g., "CD4"). |
| `voltage` | `float` (Optional) | The gain/voltage setting (from `$PnV`). |

### CompensationMatrix
*The spectral overlap correction matrix.*

| Field | Type | Description |
|-------|------|-------------|
| `fluorochromes` | `List[string]` | Names of the fluorochromes in the matrix (columns/rows). |
| `values` | `List[List[float]]` | The N x N matrix values. |

## Relationships

1. **One FCS File** contains **One InstrumentInfo**.
2. **One FCS File** contains **Many Channels**.
3. **One FCS File** contains **Zero or One Compensation Matrix**.
4. **One Batch Export** processes **Many FCS Files** into **One ZIP**.

## State Transitions

1. **Upload**: File received → `Parsing`
2. **Parsing**: 
   - Success → `Ready` (Metadata stored in memory)
   - Failure → `Error`
3. **Export**: `Ready` → `Generating PNG` → `Zipping` → `Complete`
# Research: Conditional A4 Export Pagination

**Feature**: `001-export-pagination`
**Status**: Completed

## 1. Technical Context

The current system uses `reportlab` to generate PDF reports. The existing logic forces all content onto a single page by dynamically reducing font sizes and row heights based on the row count.

**Current limitation**:
- Aggressive scaling makes large tables hard to read.
- No support for multi-page layouts; content might be clipped if scaling isn't sufficient or if it looks terrible.

**Goal**:
- Maintain single-page layout for small/medium datasets.
- Move "Compensation Matrix" to Page 2 for large datasets instead of shrinking to illegibility.

## 2. Decision Record

### Decision 1: Height Calculation Strategy
**Decision**: Use `reportlab`'s `flowable.wrap(availWidth, availHeight)` method to pre-calculate the height of generated tables before adding them to the document story.

**Rationale**:
- `reportlab` builds documents linearly. We cannot easily "undo" a table once added to the `SimpleDocTemplate` story.
- By instantiating the `Table` objects first and calling `.wrap()`, we get the exact vertical space they will consume.
- This allows us to perform the logic: `if (current_y + comp_matrix_height) > page_height: insert PageBreak`.

**Alternatives Considered**:
- *KeepTogether*: Wrap the matrix in `KeepTogether`. This forces a page break if the *entire* matrix doesn't fit.
    - *Pros*: Built-in.
    - *Cons*: Doesn't explicitly separate "Voltage Table" from "Comp Matrix" if the Voltage table *itself* is near the bottom. We specifically want to break *between* sections if needed, not just prevent splitting the matrix (though preventing matrix splitting is also good). The requirement is specific: "move... to the second page". `KeepTogether` on the matrix achieves this if the matrix is what causes the overflow.
- *Two-Pass Generation*: Build once, check page count, rebuild if needed.
    - *Cons*: Inefficient (slows down export).

**Refined Approach**:
- Combine `KeepTogether` logic with explicit height checks if we want to enforce the break specifically *before* the matrix when things get tight.
- However, simply using `KeepTogether(compensation_table)` might be sufficient: if it fits, it stays; if not, it jumps to next page.
- **Constraint**: The spec implies a binary state: "If A4 can accommodate -> Single Page; If not -> Matrix on Page 2".
- **Proposed Logic**:
    1. Define a "printable height" (A4 height - margins).
    2. Calculate height of Header + Exp Info + Metadata + Voltage Table.
    3. If `(Height_Above + Height_Matrix) > Printable_Height`:
        - Insert `PageBreak()` before Matrix.
    4. Else:
        - Add Matrix directly.

### Decision 2: Scaling Logic Adjustment
**Decision**: Relax the current aggressive scaling factors.

**Rationale**:
- Since we now have a "Page 2" fallback, we don't need to shrink fonts to 6pt to force fit.
- We will retain *mild* scaling (e.g., down to 8pt) to optimize for single-page when close, but default to splitting pages for readability if it requires <8pt.

## 3. Implementation Plan

1.  **Modify `backend/app/services/pdf_renderer.py`**:
    - Update `generate_pdf_report`.
    - Extract Table creation into separate steps (do not append to `elements` immediately).
    - Use `table.wrap(doc.width, doc.height)[1]` to get heights.
    - Implement the conditional `PageBreak`.
    - Tweak `scale_factor` logic.

## 4. Dependencies
- No new dependencies. `reportlab` is already installed.

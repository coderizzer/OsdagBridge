# OsdagBridge — Manual Test Log
**Module:** Short-Span Steel Girder Bridge (Plate Girder)
**Branch:** `dev`
**Tester:** Priyanka (GitHub: `coderizzer`)
**Date:** 2026-11-22
**Method:** Static code-path analysis (conda environment not available in CI runner)

---

## Test Environment

| Item | Value |
|------|-------|
| OS | Windows 11 |
| Python | 3.11 (target, per `environment.yml`) |
| Key dependencies | PyQt5 5.15, ospgrillage 0.1.9, OCC-Core 7.7.2 |
| Analysis approach | Full static trace of UI ↔ core data flow |
| Files analysed | `input_dock.py`, `output_dock.py`, `template_page.py`, `designer.py`, `defaults.py`, `validator.py`, `initial_sizing.py` |

---

## TC-01 — Default Inputs, Single Design Run

**Objective:** Verify that a first-run design with all default values completes without error.

**Input Parameters:**
| Field | Value |
|-------|-------|
| Span | 15 m |
| Number of girders | 4 |
| Girder spacing | 2.5 m |
| Deck width | 10.5 m |
| Wearing course thickness | 80 mm |
| Wearing course density | 24 kN/m³ (default from `defaults.py:257`) |
| Dead load factor | 1.35 |
| Live load factor | 1.5 |
| Design mode | Optimised |
| Steel grade | E250 |
| Concrete grade | M30 |

**Expected Result:** Design completes; Output Dictionary populated with section dimensions, utilisation ratios ≤ 1.0.

**Actual Result (code-traced):**
- `validate_basic_inputs()` runs; wearing course density 24 kN/m³ **silently clamped to 10 kN/m³** by `validator.py:319`
- Design proceeds with underestimated dead load (~58% reduction in WC contribution)
- Output generated but dead load is non-conservative

**Status:** ❌ FAIL
**Bug Reference:** Bug #3 — Wearing course density validator mismatch

---

## TC-02 — Custom Steel Properties (Non-Default Grade)

**Objective:** Verify custom steel material properties are accepted and persist through design.

**Input Parameters:**
| Field | Value |
|-------|-------|
| Steel grade | Custom |
| Yield strength (fy) | 345 MPa |
| Ultimate tensile strength (fu) | 490 MPa |
| Elastic modulus (E) | 210000 MPa |
| Poisson's ratio | 0.3 |
| Span | 20 m |
| Number of girders | 3 |

**Expected Result:** Custom material values saved to Input Dictionary; design uses fy=345, fu=490 throughout.

**Actual Result (code-traced):**
- `_on_material_changed()` in `input_dock.py:778` calls `self._set_material_fields_editable(...)` which does **not exist**
- `AttributeError` raised; material section becomes unresponsive
- Input Dictionary never updated with custom values

**Status:** ❌ FAIL
**Bug Reference:** Bug #1 — `_set_material_fields_editable` missing

---

## TC-03 — Custom Concrete Deck Properties

**Objective:** Verify custom concrete grade is accepted and reflected in composite section calculations.

**Input Parameters:**
| Field | Value |
|-------|-------|
| Concrete grade | M40 (custom) |
| Characteristic compressive strength (fck) | 40 MPa |
| Elastic modulus (Ec) | 33.5 GPa |
| Deck thickness | 220 mm |
| Reinforcement cover | 40 mm |

**Expected Result:** Composite section modulus recalculated with M40 properties; output section utilisation updated.

**Actual Result (code-traced):**
- Concrete grade combo triggers `_on_concrete_changed()` — no method-not-found issue here
- Custom fck value persists correctly to `input_dict[KEY_CONCRETE_FY]`
- Modular ratio calculated as `Es / Ec` correctly

**Status:** ✅ PASS (partial — composite section calculation path is correct)

---

## TC-04 — Multi-Run State Persistence (3 Consecutive Runs)

**Objective:** Verify that unlocking the design and re-running with modified inputs does not carry stale state.

### Run 1
| Field | Value |
|-------|-------|
| Span | 15 m, 4 girders, E250, M30 |

### Run 2 (after unlock)
| Field | Value |
|-------|-------|
| Span | 20 m (changed), 4 girders, E350, M30 |

### Run 3 (after unlock)
| Field | Value |
|-------|-------|
| Span | 20 m, 5 girders (changed), E350, M35 (changed) |

**Expected Result:** Each run uses fresh input values; output dictionary completely overwritten; 3D CAD model regenerated.

**Actual Result (code-traced):**
- `solve_extend_basic_input_dict()` regenerates dynamic member keys on each run ✅
- `QThread` worker created fresh on each `_on_design_clicked()` ✅
- **If Run 1 fails:** `_finish_loading()` double-called → UI locked → Run 2 impossible (Bug #2)
- If Run 1 succeeds: Run 2 and 3 proceed correctly per code trace

**Status:** ⚠️ CONDITIONAL PASS / FAIL depends on Bug #2 resolution
**Bug Reference:** Bug #2 — `_finish_loading()` double-call on error

---

## TC-05 — Bearing Stiffener Configuration

**Objective:** Verify bearing stiffener count and geometry inputs produce correct stiffener capacity checks.

**Input Parameters:**
| Field | Value |
|-------|-------|
| Number of bearing stiffeners | 4 |
| Stiffener width | 100 mm |
| Stiffener thickness | 12 mm |
| Stiffener grade | E250 |

**Expected Result:** Bearing stiffener checks use `n_sides=1` (or user-specified), `bs_n_plates=4`; capacity calculated per IS 800.

**Actual Result (code-traced):**
- `designer.py:534-538`: `n_sides` reads `KEY_MP_STIFFENER_NO_BEARING_STIFFENERS` → gets value 4
- `bs_n_plates` reads same key → also gets 4
- `n_sides=4` is incorrect; should be 1 or 2 depending on stiffener layout
- Stiffener capacity check uses wrong `n_sides` → non-conservative or over-conservative result

**Status:** ❌ FAIL
**Bug Reference:** Bug #4 — `n_sides` / `bs_n_plates` key collision

---

## TC-06 — Cross-Bracing Member ID Labelling

**Objective:** Verify cross-bracing members have unique individual IDs in output.

**Input Parameters:**
| Field | Value |
|-------|-------|
| Number of cross-bracing members | 5 |
| Girder index | 1 |

**Expected Result:** CB members labelled B1M1, B1M2, B1M3, B1M4, B1M5 in Output Dictionary.

**Actual Result (code-traced):**
- `extend_cb_dynamic_keys()` in `defaults.py:431` sets all members to `"B1M1 to B1M5"`
- Every member has the same range-string label

**Status:** ❌ FAIL
**Bug Reference:** Bug #5 — CB member ID range string

---

## TC-07 — Optimised Design Mode, Large Span

**Objective:** Verify solver-computed section bounds are applied correctly for a large span.

**Input Parameters:**
| Field | Value |
|-------|-------|
| Span | 30 m |
| Number of girders | 6 |
| Design mode | Optimised |
| Steel grade | E350 |

**Expected Result:** `initial_sizing.py` computes preliminary section bounds; solver selects optimal plate dimensions within bounds.

**Actual Result (code-traced):**
- `initial_sizing.py` applies span/depth heuristics correctly (depth ≈ span/15 to span/20)
- Flange and web dimensions set within IS 800 slenderness limits
- Design proceeds to full check

**Status:** ✅ PASS (code path correct)

---

## TC-08 — Custom Design Mode, User-Specified Plate Dimensions

**Objective:** Verify user-entered plate dimensions bypass the optimiser and are used directly.

**Input Parameters:**
| Field | Value |
|-------|-------|
| Design mode | Custom |
| Web height | 1200 mm |
| Web thickness | 12 mm |
| Top flange width | 350 mm |
| Top flange thickness | 25 mm |
| Bottom flange width | 350 mm |
| Bottom flange thickness | 25 mm |

**Expected Result:** `designer.py` reads custom plate dims directly from Input Dictionary; no optimiser override.

**Actual Result (code-traced):**
- Mode check in `designer.py` correctly branches on `KEY_DESIGN_MODE == "Custom"`
- Custom dimensions read from dict and passed to `PlateGirderSection` constructor
- Optimiser not invoked in this branch

**Status:** ✅ PASS

---

## TC-09 — Validate Incorrect Span Input (Boundary Check)

**Objective:** Verify validator rejects out-of-range span values.

**Input:** Span = 0.5 m (below minimum)

**Expected Result:** Validator raises error; `validate_basic_inputs()` returns error tuple.

**Actual Result (code-traced):**
- `validate_basic_inputs()` annotated `-> dict` but actually returns `Optional[Tuple[Any, str]]` on failure
- Type annotation mismatch (Bug #6) — but functional logic correctly returns error message

**Status:** ⚠️ PASS with annotation warning
**Bug Reference:** Bug #6 — `validate_basic_inputs` return type mismatch

---

## TC-10 — 3D CAD Model Generation

**Objective:** Verify 3D model is generated and displayed after successful design.

**Input Parameters:** Default values (TC-01 scenario, with Bug #3 fix applied)

**Expected Result:** `output_dock.py` renders OCC-based 3D view of plate girder bridge.

**Actual Result (code-traced):**
- `output_dock.py` initialises `OCC.Display.SimpleGUI` viewer correctly
- `_on_design_complete()` calls `self._3d_view.DisplayShape()` with generated compound shape
- Viewer updates without clearing previous scene first (potential ghost geometry on re-run)

**Status:** ✅ PASS (single run) / ⚠️ WARN (multi-run — stale geometry possible)

---

## Summary Table

| TC | Description | Status | Bug |
|----|-------------|--------|-----|
| TC-01 | Default inputs, single run | ❌ FAIL | Bug #3 |
| TC-02 | Custom steel properties | ❌ FAIL | Bug #1 |
| TC-03 | Custom concrete deck | ✅ PASS | — |
| TC-04 | Multi-run state persistence | ⚠️ CONDITIONAL | Bug #2 |
| TC-05 | Bearing stiffener config | ❌ FAIL | Bug #4 |
| TC-06 | CB member ID labelling | ❌ FAIL | Bug #5 |
| TC-07 | Optimised mode, large span | ✅ PASS | — |
| TC-08 | Custom mode, user dimensions | ✅ PASS | — |
| TC-09 | Invalid span boundary | ⚠️ WARN | Bug #6 |
| TC-10 | 3D CAD model generation | ✅ / ⚠️ WARN | — |

**Pass: 4 | Fail: 4 | Conditional/Warning: 2**

---

*Test log generated from static code analysis of OsdagBridge `dev` branch.*
*Repository: https://github.com/Nidhikhare12/OsdagBridge*

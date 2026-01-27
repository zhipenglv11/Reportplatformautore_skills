# Brick Strength Fields (Rebound Method, Raw Record Table)
This schema is for structured extraction only (no calculation).

## Table-Level Fields
1. `table_id`
   - Description: table control code / table ID (top-left of the table)
   - Example: `KJQR-056-223`
   - Use: table type identification and de-duplication

2. `test_date`
   - Description: test date from header label "检测日期"
   - Example: `2023-02-26`
   - If unclear or missing, output `null`

3. `instrument_id`
   - Description: instrument ID from header label "仪器编号"
   - Example: `BTPL-***` (use as seen in the table)
   - If unclear or missing, output `null`

4. `brick_type`
   - Description: brick type from header label "砖的种类"
   - Example: `烧结砖`
   - If unclear or missing, output `null`

5. `strength_grade`
   - Description: strength grade from header label "强度等级"
   - Example: `MU15`
   - If unclear or missing, output `null`

## Row-Level Fields
6. `rows[].seq`
   - Description: row sequence number (first column)
   - Example: `1`
   - Use: ordering and completeness checking

7. `rows[].test_location`
   - Description: test location (first column or left-side handwritten note)
   - Example: `一层墙 19×D-F 轴`
   - If unclear or missing, output `null`

8. `rows[].estimated_strength_mpa`
   - Description: estimated strength value (MPa) from the last column "强度推定值"
   - Example: `15.0`
   - Keep 1 decimal place as shown; do not calculate in this skill

## Normalization Rules
- Extract only; do not compute or convert any strength values.
- If a value is uncertain or illegible, output `null` (no guessing).
- Table type identification uses `table_id` as highest priority.
- Output is for downstream reporting and rule-based calculations.

## Field-Specific Rules
### `test_date`
- Preferred format: `YYYY-MM-DD`.
- If the date is complete and clear, normalize to `YYYY-MM-DD`.
- If incomplete or unclear (e.g., only year-month or handwritten), keep the original string.
- Do not infer or fill missing parts.

### `estimated_strength_mpa`
- Type: `number | null`.
- If the cell is blank or a placeholder like `—`, `/`, output `null`.
- If a clear number exists, parse as number and keep 1 decimal place (as shown).
- Do not compute or infer from other columns (e.g., rebound values).

### `rows[].seq`
- Type: integer.
- Extract as shown in the table; do not renumber or fill gaps.
- If the sequence is illegible, keep the row but set `seq` to `null`.

### `rows[].test_location`
- Type: `string | null`.
- Preserve meaning; do not restructure into subfields.
- Light normalization only: trim leading/trailing spaces and compress consecutive spaces.

## Preserve-Exactly Fields
The following fields must be extracted as-is (no semantic edits), except missing becomes `null`:
- `table_id`
- `instrument_id`
- `brick_type`
- `strength_grade`
- `rows[].test_location`

## Output Examples
See example files under `examples/`:
- `examples/output_example.json`
- `examples/output_example.csv`
- `examples/output_example.md` (Excel layout notes)

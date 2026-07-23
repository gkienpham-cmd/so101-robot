"""Sealed-draw runner: appends one draw_mapping.csv row per bean as it is drawn.

Usage: .venv/bin/python3 <this file>  (run from repo root)

Reads the predeclared plan, prompts once per cup, appends
bean_id,lot_id,source_bag,drawn_at to private/sourcing/draw_mapping.csv.
Resumes automatically if some rows already exist. Never rewrites rows.
"""
import csv
from datetime import datetime, timezone, timedelta
from pathlib import Path

PLAN = Path("private/sourcing/draw_plan_20260722.csv")
MAPPING = Path("private/sourcing/draw_mapping.csv")
LOT = "LOT_A"
TZ = timezone(timedelta(hours=7))

plan = list(csv.DictReader(open(PLAN)))

done = set()
if MAPPING.exists():
    done = {r["bean_id"] for r in csv.DictReader(open(MAPPING))}
else:
    MAPPING.write_text("bean_id,lot_id,source_bag,drawn_at\n")

todo = [r for r in plan if r["bean_id"] not in done]
if not todo:
    print("All 20 rows already recorded. Mapping is sealed — nothing to do.")
    raise SystemExit(0)

print(f"{len(done)} rows already recorded; {len(todo)} to draw.")
print("For each prompt: take ONE bean from the named supplier bag, place it in the")
print("labeled zip bag, then press Enter. Ctrl-C to stop (safe to resume later).\n")

for r in todo:
    input(f"P{r['cup']}: draw one bean from the *{r['source_bag'].upper()}* supplier bag "
          f"-> zip bag P{r['cup']}. Enter when placed... ")
    ts = datetime.now(TZ).isoformat(timespec="seconds")
    with open(MAPPING, "a", newline="") as f:
        csv.writer(f).writerow([r["bean_id"], LOT, r["source_bag"], ts])
    print(f"   recorded {r['bean_id']},{LOT},{r['source_bag']},{ts}")

print("\nDraw complete. draw_mapping.csv is now SEALED — do not reopen it during grading or capture.")

"""Blind grading runner: walks the sealed shuffled order, appends blind_labels.csv rows.

Run from repo root:  .venv/bin/python3 src/pilot_grading_runner.py

Grade the PHYSICAL BEAN in hand against docs/data_and_labeling.md only. This script
never reads or shows the draw mapping/plan. Resume-safe: already-graded beans are
skipped. One bean out of its bag at a time; back in the same bag after grading.

Input per bean:
  a        -> acceptable
  1..8     -> visible_reject with that defect type
  ?a, ?1-8 -> same, but ambiguous=true (uncertain/rushed; excluded from scored set)
Then an optional one-line note (Enter to skip).
"""
import csv, sys
from pathlib import Path

ORDER = Path("private/sourcing/grading_order_20260723.txt")
LABELS = Path("private/sourcing/blind_labels.csv")
LOT = "LOT_A"
REVIEWED_AT = "2026-07-23"
TYPES = ["black", "broken", "insect_damage", "dried_cherry",
         "shell_husk", "immature_faded", "moldy", "foreign_matter"]

order = [ln.strip() for ln in ORDER.read_text().splitlines()
         if ln.strip() and not ln.startswith("#")]

done = set()
with open(LABELS) as f:
    for row in csv.DictReader(f):
        done.add(row["bean_id"])

todo = [p for p in order if f"PILOT_B{int(p[1:]):03d}" not in done]
if not todo:
    print("All 20 beans already graded. Nothing to do.")
    sys.exit(0)

print(f"{len(done)} graded; {len(todo)} to go. Defect types:")
for i, t in enumerate(TYPES, 1):
    print(f"  {i} = {t}")
print("  a = acceptable | prefix ? = ambiguous (e.g. ?a, ?3)\n")

for p in todo:
    bid = f"PILOT_B{int(p[1:]):03d}"
    while True:
        raw = input(f"Bag {p}: take the bean out, inspect top+bottom. Grade [a/1-8/?a/?1-8]: ").strip().lower()
        amb = raw.startswith("?")
        code = raw[1:] if amb else raw
        if code == "a":
            label, dtype = "acceptable", ""
        elif code.isdigit() and 1 <= int(code) <= 8:
            label, dtype = "visible_reject", TYPES[int(code) - 1]
        else:
            print("  invalid — a, 1-8, ?a, or ?1-8"); continue
        break
    note = input("  note (Enter to skip): ").strip()
    with open(LABELS, "a", newline="") as f:
        csv.writer(f).writerow([bid, LOT, label, dtype,
                                "true" if amb else "false", note, REVIEWED_AT])
    print(f"  recorded {bid}: {label}{'/' + dtype if dtype else ''}"
          f"{' (AMBIGUOUS)' if amb else ''} — bean back in bag {p}\n")

print("Grading complete. blind_labels.csv written. Do not reopen the draw mapping.")

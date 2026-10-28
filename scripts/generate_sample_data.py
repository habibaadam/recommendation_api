import csv
import random
from datetime import date, timedelta
from pathlib import Path

random.seed(42)

#print(random.randint(1, 100))
users = [f"u{i}" for i in range(1, 31)]
items = [f"item{i}" for i in range(1, 31)]
weights = [1 / (n + 1) for n in range(len(items))]
start = date(2026, 7, 1) # starting date

rows = []
for _ in range(3000):
    rows.append((
        random.choice(users),
        random.choices(items, weights=weights)[0],
        (start + timedelta(days=random.randint(0, 89))).isoformat()
    ))


rows += [rows[0], ("", "item1", "2026-08-01"), ("u1", "item2", "not-a-date")]

output = Path("data/purchases.csv")
output.parent.mkdir(exist_ok=True)

with output.open("w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["user_id", "item_id", "date"])
    w.writerows(rows)

print(f"wrote {len(rows)} rows to {output}")
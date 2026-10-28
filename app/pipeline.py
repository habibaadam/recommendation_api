import json, sys
import pandas as pd
from pathlib import Path


def clean(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["date"] = pd.to_datetime(df["date"], errors="coerce") # change strings to date time
    df["user_id"] = df["user_id"].fillna("").astype(str).str.strip() # normalizing every userid into a string and removes trailing whitespace
    df = df[df["user_id"] != ""] # only acknowledging non empty rows of user ids
    df = df.dropna(subset=["item_id", "date"]) # drop rows with empty item_id or date
    return df.drop_duplicates().reset_index(drop=True)



def build_snapshot(df: pd.DataFrame, as_of: str) -> dict:
    cutoff = pd.Timestamp(as_of)
    df = df[df["date"] <= cutoff]

    baskets = df.groupby("user_id")["item_id"].agg(lambda s: sorted(set(s)))
    co: dict[str, dict[str, int]] = {}
    for basket in baskets:
        for a in basket:
            for b in basket:
                if a != b:
                    co.setdefault(a, {})
                    co[a][b] = co[a].get(b, 0) + 1

    recent = df[df["date"] > cutoff - pd.Timedelta(days=30)]
    features = {}
    for user, g in df.groupby("user_id"):
        features[user] = {
            "purchases_30d": int((recent["user_id"] == user).sum()),
            "distinct_items": int(g["item_id"].nunique()),
            "days_since_last": int((cutoff - g["date"].max()).days),
        }

    return {
            "as_of": as_of,
            "rows_used": int(len(df)),
            "popular": df["item_id"].value_counts().index.tolist(),
            "user_items": baskets.to_dict(),
            "co_purchase": co,
            "features": features,
        }


def main(as_of: str) -> None:
    raw_data = pd.read_csv("data/purchases.csv")
    cleaned_data = clean(raw_data)
    print(f"raw rows: {len(raw_data)}, after cleaning: {len(cleaned_data)}")

    snapshot = build_snapshot(cleaned_data, as_of)
    output = Path("artifacts") / f"snapshot_{as_of}.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(snapshot))
    print(f"wrote {output} using {snapshot['rows_used']} rows")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "2026-09-15")
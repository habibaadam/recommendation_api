import json, os, time
from pathlib import Path


class Recommender:
    def __init__(self, snapshot:dict):
        self.s = snapshot

    @classmethod
    def load(cls, path: str) -> "Recommender":
        return cls(json.loads(Path(path).read_text()))

    def recommend(self, user_id: str, k: int = 5) -> tuple[list[str], str]:
        # simulate a delay with time.sleep

        time.sleep(int(os.getenv("MODEL_DELAY_MS", "0"))/ 1000)

        owned_items = set(self.s["user_items"].get(user_id, []))

        scores: dict[str, int] = {}

        for item in owned_items:
            for other, n in self.s["co_purchase"].get(item, {}).items():
                if other not in owned_items:
                    scores[other] = scores.get(other, 0) + n

        if scores:
            ranked = sorted(scores, key=scores.get, reverse=True)
            return ranked[:k], "model"

        popular = [i for i in self.s["popular"] if i not in owned_items]
        return popular[:k], "fallback_popular"


    def features(self, user_id: str) -> dict | None:
        return self.s["features"].get(user_id)
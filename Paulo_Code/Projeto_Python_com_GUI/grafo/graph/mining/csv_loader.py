import csv
import random
from typing import List
from .interaction import Interaction, InteractionType

class CsvLoader:
    @staticmethod
    def load(path: str) -> List[Interaction]:
        interactions = []
        with open(path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                actor = row.get('actor')
                target = row.get('target')
                if not actor or not target or actor == target:
                    continue
                
                type_str = row.get('type', 'COMMENT_ON_ISSUE_OR_PR')
                try:
                    itype = InteractionType[type_str]
                except KeyError:
                    itype = InteractionType.COMMENT_ON_ISSUE_OR_PR
                
                interactions.append(Interaction(actor, target, itype))
        return interactions

    @staticmethod
    def generate_sample_csv(path: str):
        users = [f"user{i}" for i in range(10)]
        types = list(InteractionType)
        random.seed(42)
        with open(path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(['actor', 'target', 'type'])
            for _ in range(120):
                actor = random.choice(users)
                target = random.choice(users)
                if actor != target:
                    itype = random.choice(types)
                    writer.writerow([actor, target, itype.name])

from enum import Enum

class InteractionType(Enum):
    COMMENT_ON_ISSUE_OR_PR = 2
    ISSUE_CLOSED_BY_OTHER = 3
    PR_REVIEW_OR_APPROVAL = 4
    PR_MERGE = 5

    @property
    def weight(self) -> int:
        return self.value

class Interaction:
    def __init__(self, actor: str, target: str, interaction_type: InteractionType):
        self.actor = actor
        self.target = target
        self.type = interaction_type

    def __str__(self):
        return f"{self.actor} --[{self.type.name}]--> {self.target}"

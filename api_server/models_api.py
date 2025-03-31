"""
Datamodels used to validate and serialize API server responses.
"""

__all__ = ['APIRatingSummary', 'APICredibilityScore', 'APIUserVote', 'VoteVal']

from typing import TypeAlias

from pydantic import BaseModel, conint, Field
from pydantic.types import NonNegativeInt as NnI, NonNegativeFloat as NnF

# VoteVal: TypeAlias = Annotated[int, Field(strict=True, ge=-1, le=1)]
VoteVal: TypeAlias = conint(ge=-1, le=1)  # type: ignore


class APIRatingSummary(BaseModel):
    """Model of a pair of aggregate vote counts"""
    site_domain: str = Field(serialization_alias='site')
    up_votes: NnI = 0
    down_votes: NnI = 0


class APICredibilityScore(BaseModel):
    """Model of a centralized rating"""
    site_domain: str = Field(serialization_alias='site')
    score: NnF | None = None


class APIUserVote(BaseModel):
    """Model of a singular user-casted vote"""
    site_domain: str = Field(serialization_alias='site')
    value: VoteVal

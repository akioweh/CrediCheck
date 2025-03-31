"""
API endpoints that are not exactly necessary for public use.
"""

from typing import Final

from fastapi import APIRouter
from sqlmodel import select

from .models_api import APIRatingSummary
from .models_sql import RatingSummary
from .sql import AutoSession

testing_router: Final[APIRouter] = APIRouter()


@testing_router.get('/ratings/all', response_model=list[APIRatingSummary])
async def get_all_ratings(session: AutoSession) -> list[RatingSummary]:
    """Returns all ratings in the database."""
    return list(await session.exec(select(RatingSummary)))

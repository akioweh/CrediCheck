"""
Direct SQL operations and utilities.

These functions should be preferred over direct SQLModel operations,
especially as they manage relational and cumulative state.
"""

__all__ = ['ENGINE', 'get_session', 'AutoSession', 'db_connect', 'db_construct_models', 'get_or_create_user',
           'get_or_create_site', 'cast_vote']

import asyncio
import random
from typing import Annotated, TypeAlias, AsyncGenerator

from fastapi import Depends
from pydantic import ValidationError
from pydantic.v1 import NonNegativeFloat
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlmodel import SQLModel, select
from sqlmodel.ext.asyncio.session import AsyncSession

from .models_sql import User, Vote, RatingSummary, Site, CredibilityScore
from .params import DEMO_MODE

# global singleton database engine
ENGINE: AsyncEngine | None = None


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provides a (new) database session (i.e. transaction) every time."""
    if ENGINE is None:
        raise RuntimeError('Database engine not initialized')
    async with AsyncSession(ENGINE, expire_on_commit=False) as session:
        yield session


# type alias used for dependency injection with FastAPI
AutoSession: TypeAlias = Annotated[AsyncSession, Depends(get_session)]


def db_connect(uri: str, args: dict, **kwargs) -> AsyncEngine:
    global ENGINE
    if ENGINE is not None:
        raise RuntimeError('Database engine already initialized')
    ENGINE = create_async_engine(uri, connect_args=args, **kwargs)
    return ENGINE


async def db_construct_models(engine: AsyncEngine):
    # zero idea why we gotta do it like this; incomplete async interface in SQLModel
    async with engine.begin() as conn:
        await conn.run_sync(SQLModel.metadata.create_all)


async def get_or_create_user(session: AsyncSession, user_ip: str) -> User:
    """Gets or creates a user object for the given IP address."""
    if (user := await session.get(User, user_ip)) is None:
        user = User(ip=user_ip)
        session.add(user)
        await session.commit()
        await session.refresh(user)
    return user


async def _generate_random_votes(session: AsyncSession, domain: str, num_votes: int) -> None:
    """Generate random votes for a domain in demo mode."""
    tasks = []
    for i in range(num_votes):
        user_ip = f"192.168.1.{random.randint(1, 254)}"
        vote_value = random.choice([-1, 1])
        tasks.append(cast_vote(session, user_ip, domain, vote_value))

    await asyncio.gather(*tasks)


async def get_or_create_site(session: AsyncSession, domain: str) -> tuple[Site, RatingSummary]:
    """Gets or creates a Domain and its associated RatingSummary for the given domain."""
    site = await session.get(Site, domain)
    summary = await session.get(RatingSummary, domain)
    if site is None or summary is None:
        if site or summary:
            raise ValueError(f'Inconsistent state between the existence of a Site and its RatingSummary')
        site = Site(domain=domain)
        summary = RatingSummary(site_domain=domain)
        session.add(site)
        session.add(summary)
        await session.commit()
        await session.refresh(site)
        await session.refresh(summary)

        # bad place to put this, but whatever
        # (this should be somewhere that is called on GET ratings instead of PUT vote,
        # but the prior doesn't have a nice, pre-existing injection point)
        if DEMO_MODE:
            num_votes = random.randint(5, 20)
            await _generate_random_votes(session, domain, num_votes)
            score = round(random.uniform(0, 10), 1)  # Round to 1 decimal place
            await create_credibility_score(session, domain, score)

    return site, summary


async def create_credibility_score(session: AsyncSession, domain: str, score: NonNegativeFloat) -> CredibilityScore:
    if await session.get(CredibilityScore, domain):
        raise ValueError(f'Credibility score already exists for domain: {domain}')
    site = (await get_or_create_site(session, domain))[0]
    score_obj = CredibilityScore(site_domain=site.domain, score=score)
    session.add(score_obj)
    await session.commit()
    await session.refresh(score_obj)
    return score_obj


# noinspection Pydantic
async def cast_vote(session: AsyncSession, user_ip: str, domain: str, vote: int) -> bool:
    """Casts a vote for a given user and domain.
    Returns whether state changed.
    """
    if vote not in (-1, 0, 1):
        raise ValidationError(f'Invalid vote value: {vote}')
    if vote == 0 and await session.get(Vote, (user_ip, domain)) is None:
        return False
    user = await get_or_create_user(session, user_ip)
    site = (await get_or_create_site(session, domain))[0]
    statement = select(Vote).where(Vote.user_ip == user_ip, Vote.site_domain == site.domain)
    if (vote_obj := (await session.exec(statement)).one_or_none()) is not None:
        if vote_obj.value == vote:
            return False  # No change
        old_vote = vote_obj.value
        if vote == 0:
            await session.delete(vote_obj)
            vote_obj = None
        else:
            vote_obj.value = vote
    else:
        if vote == 0:
            return False  # No change
        old_vote = 0
        vote_obj = Vote(site_domain=site.domain, user_ip=user.ip, value=vote)
    await _update_vote_count(session, domain, vote, old_vote)
    if vote_obj:
        session.add(vote_obj)
        await session.commit()
    return True


# noinspection Pydantic
async def _update_vote_count(session: AsyncSession, domain: str, new_vote: int, old_vote: int = 0):
    """Given a previous vote and a new vote,
    update the cumulative count state variables appropriately.
    Votes are aggregated by domain.
    """
    if new_vote == old_vote:
        return

    rating_summary = await session.get(RatingSummary, domain)
    if rating_summary is None:
        raise ValueError(f'RatingSummary not found for domain: {domain}')

    if old_vote:
        if old_vote > 0:
            rating_summary.up_votes -= 1
        elif old_vote < 0:
            rating_summary.down_votes -= 1
    if new_vote:
        if new_vote > 0:
            rating_summary.up_votes += 1
        elif new_vote < 0:
            rating_summary.down_votes += 1
    session.add(rating_summary)
    await session.commit()

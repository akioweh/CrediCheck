"""
ORM datamodels.
"""

__all__ = ['User', 'Site', 'Vote', 'RatingSummary', 'CredibilityScore', 'init_datamodels']

from datetime import datetime
from typing import Optional

from sqlmodel import SQLModel, Field, Relationship

from .models_api import APIRatingSummary, APICredibilityScore, APIUserVote


class User(SQLModel, table=True):
    ip: str = Field(primary_key=True, max_length=45, allow_mutation=False)
    votes: list['Vote'] = Relationship(back_populates='user', sa_relationship_kwargs={'lazy': 'selectin'})


class Site(SQLModel, table=True):
    domain: str = Field(primary_key=True, allow_mutation=False)
    vote_summary: 'RatingSummary' = Relationship(back_populates='site', sa_relationship_kwargs={'lazy': 'selectin'})
    votes: list['Vote'] = Relationship(back_populates='site', sa_relationship_kwargs={'lazy': 'selectin'})
    credibility_score: Optional['CredibilityScore'] = Relationship(back_populates='site',
                                                                   sa_relationship_kwargs={'lazy': 'selectin'})


class Vote(SQLModel, APIUserVote, table=True):
    timestamp: datetime = Field(default_factory=datetime.now)

    user_ip: str = Field(foreign_key='user.ip', primary_key=True, max_length=45, allow_mutation=False)
    user: User = Relationship(back_populates='votes', sa_relationship_kwargs={'lazy': 'selectin'})

    site_domain: str = Field(foreign_key='site.domain', primary_key=True, allow_mutation=False)
    site: Site = Relationship(back_populates='votes', sa_relationship_kwargs={'lazy': 'selectin'})


class RatingSummary(SQLModel, APIRatingSummary, table=True):
    site_domain: str = Field(foreign_key='site.domain', primary_key=True, allow_mutation=False)
    site: Site = Relationship(back_populates='vote_summary', sa_relationship_kwargs={'lazy': 'selectin'})


class CredibilityScore(SQLModel, APICredibilityScore, table=True):
    site_domain: str = Field(foreign_key='site.domain', primary_key=True, allow_mutation=False)
    site: Site = Relationship(back_populates='credibility_score', sa_relationship_kwargs={'lazy': 'selectin'})


def init_datamodels():
    # nothing actually needs to be done here
    # we're just making sure that this module gets imported
    # since it needs to be (before SQLModel metadata is constructed)
    pass

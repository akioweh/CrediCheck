"""
HTTP API path operations.
"""

from typing import Final

from fastapi import APIRouter, status, Response, Request, HTTPException
from pydantic.networks import HttpUrl

from .models_api import APIUserVote, APIRatingSummary, APICredibilityScore, VoteVal
from .models_sql import CredibilityScore, RatingSummary, Vote, User
from .sql import cast_vote, AutoSession

main_router: Final[APIRouter] = APIRouter()


@main_router.get('/score', response_model=APICredibilityScore)
async def get_credibility_rating(site: HttpUrl, session: AutoSession) -> CredibilityScore:
    """Returns the central credibility rating for a given domain"""
    if (domain_name := site.host) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid domain in URL')

    return await session.get(CredibilityScore, domain_name) or CredibilityScore(site_domain=domain_name)


@main_router.get('/ratings', response_model=APIRatingSummary)
async def get_community_rating(site: HttpUrl, session: AutoSession) -> RatingSummary:
    """Returns the aggregate community rating for a given domain."""
    if (domain_name := site.host) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid domain in URL')

    return await session.get(RatingSummary, domain_name) or RatingSummary(site_domain=domain_name)


@main_router.put('/ratings', response_model=None, responses={
    status.HTTP_200_OK: {'description': 'New vote recorded', 'content': None},
    status.HTTP_204_NO_CONTENT: {'description': 'Already voted; no changes made'}
})
async def cast_user_vote(site: HttpUrl, vote: VoteVal, *,
                         request: Request, response: Response, session: AutoSession) -> None:
    """Casts a personal vote on a given domain.
    A value of 0 removes any existing vote.
    """
    if (client := request.client) is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Unauthorized')
    if (domain_name := site.host) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid domain in URL')

    if not await cast_vote(session, client.host, domain_name, vote):
        response.status_code = status.HTTP_204_NO_CONTENT
        return


@main_router.delete('/ratings', response_model=None, responses={
    status.HTTP_200_OK: {'description': 'Vote removed', 'content': None},
    status.HTTP_204_NO_CONTENT: {'description': 'No vote to remove'}
})
async def remove_user_vote(site: HttpUrl, request: Request, response: Response, session: AutoSession) -> None:
    """Removes a personal vote on a given domain."""
    if (client := request.client) is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Unauthorized')
    if await session.get(User, client.host) is None:
        response.status_code = status.HTTP_204_NO_CONTENT
        return  # if user doesn't exist, then definitely no vote to remove
    if (domain_name := site.host) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid domain in URL')

    if not await cast_vote(session, client.host, domain_name, 0):
        response.status_code = status.HTTP_204_NO_CONTENT


@main_router.get('/ratings/my/all', response_model=list[APIUserVote])
async def get_user_votes(request: Request, session: AutoSession) -> list[Vote]:
    """Returns all votes cast by request sender."""
    if (client := request.client) is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Unauthorized')

    if (user := await session.get(User, client.host)) is None:
        return []
    return list(user.votes)


@main_router.get('/ratings/my', response_model=VoteVal)
async def get_user_vote_for(site: HttpUrl, request: Request, session: AutoSession) -> VoteVal:
    """Returns the vote cast by request sender for a given domain."""
    if (client := request.client) is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Unauthorized')
    if (domain_name := site.host) is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail='Invalid domain in URL')

    if (vote_obj := await session.get(Vote, (client.host, domain_name))) is None:
        return 0
    return vote_obj.value

from contextlib import asynccontextmanager
from typing import Final

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import main_router
from .api_testing import testing_router
from .models_sql import init_datamodels
from .params import DB_URI, DB_ARGS
from .sql import db_construct_models, db_connect


# noinspection PyUnusedLocal
@asynccontextmanager
async def lifespan_manager(app: FastAPI):
    # on startup
    init_datamodels()
    engine = db_connect(DB_URI, DB_ARGS)
    await db_construct_models(engine)
    yield
    # on shutdown
    pass


api: Final[FastAPI] = FastAPI(lifespan=lifespan_manager, title='CrediCheck')

# some CORS stuff that I don't understand
api.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

api.include_router(main_router, tags=['Public API'])
api.include_router(testing_router, tags=['Testing API'])

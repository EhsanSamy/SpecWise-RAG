import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import documents as documents_routes
from app.api.routes import projects as projects_routes
from app.api.routes import query as query_routes
from app.api.routes import search as search_routes
from app.core.config import get_settings
from app.services import retrieval
from app.utils.logging_config import configure_logging

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    configure_logging(settings.log_level)

    logger.info("Starting up SpecWise backend...")
    retrieval.init_retrieval(settings)
    logger.info("Startup complete.")

    yield

    logger.info("Shutting down SpecWise backend.")


app = FastAPI(title="SpecWise API", version="0.1.0", lifespan=lifespan)

_settings = get_settings()
app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(query_routes.router)
app.include_router(projects_routes.router)
app.include_router(documents_routes.router)
app.include_router(search_routes.router)
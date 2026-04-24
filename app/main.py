from fastapi import FastAPI
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.db.database import engine, Base, SessionLocal

from app.models import user, expense, category

from app.api.routes.user_routes import router as user_router
from app.api.routes.expense_routes import router as expense_router
from app.api.routes.category_routes import router as category_router

from app.services.category_service import init_default_categories


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("DB ready")
    Base.metadata.create_all(bind=engine)
    
    logger.info("Initializing default categories")
    db = SessionLocal()
    try:
        init_default_categories(db)
        logger.info("Default categories initialized")
    finally:
        db.close()
    
    logger.info("Startup complete")
    yield


app = FastAPI(
    title=settings.APP_NAME,
    lifespan=lifespan
)


app.include_router(user_router, prefix="/users", tags=["Users"])
app.include_router(expense_router, prefix="/expenses", tags=["Expenses"])
app.include_router(category_router, prefix="/categories", tags=["Categories"])


@app.get("/")
def root():
    logger.info("Health check called")
    return {"status": "ok"}
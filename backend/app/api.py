from fastapi import APIRouter

from app.routes.accounts import router as accounts_router
from app.routes.creators import router as creators_router
from app.routes.offers import router as offers_router

router = APIRouter()


@router.get("/health", tags=["system"])
def health() -> dict[str, str]:
    return {"status": "ok", "service": "pickbyme-api"}


router.include_router(accounts_router)
router.include_router(offers_router)
router.include_router(creators_router)

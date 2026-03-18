"""API v1 router. Aggregates all module routers under /api/v1 prefix."""

from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.auth.wallet_router import router as wallet_router
from app.modules.invoices.router import router as invoices_router
from app.modules.dashboard.router import router as dashboard_router
from app.modules.rules.router import router as rules_router

api_router = APIRouter(prefix="/api/v1")

api_router.include_router(auth_router)
api_router.include_router(wallet_router)
api_router.include_router(invoices_router)
api_router.include_router(dashboard_router)
api_router.include_router(rules_router)

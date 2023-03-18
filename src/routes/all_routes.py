from fastapi import APIRouter
from src.routes.showtemp import router as showtemp


router = APIRouter()

router.include_router(showtemp)


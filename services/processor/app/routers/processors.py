from fastapi import APIRouter

from app.processors.registry import list_processors

router = APIRouter(prefix="/processors", tags=["processors"])


@router.get("")
async def get_processors():
    return list_processors()

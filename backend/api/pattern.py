from fastapi import APIRouter, UploadFile, File
from services.pattern_service import detect_pattern

router = APIRouter()

@router.post("/")
async def pattern(file: UploadFile = File(...)):
    return await detect_pattern(file)
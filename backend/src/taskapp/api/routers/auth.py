from fastapi import APIRouter

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", status_code=201)
async def register() -> None:
    raise NotImplementedError


@router.post("/login")
async def login() -> None:
    raise NotImplementedError


@router.get("/me")
async def me() -> None:
    raise NotImplementedError

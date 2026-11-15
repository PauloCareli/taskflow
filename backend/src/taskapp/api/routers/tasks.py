from fastapi import APIRouter

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("")
async def list_tasks() -> None:
    raise NotImplementedError


@router.post("", status_code=201)
async def create_task() -> None:
    raise NotImplementedError


@router.get("/{task_id}")
async def get_task(task_id: str) -> None:
    raise NotImplementedError


@router.patch("/{task_id}")
async def update_task(task_id: str) -> None:
    raise NotImplementedError


@router.delete("/{task_id}", status_code=204)
async def delete_task(task_id: str) -> None:
    raise NotImplementedError


@router.post("/{task_id}/assign")
async def assign_task(task_id: str) -> None:
    raise NotImplementedError


@router.post("/{task_id}/complete")
async def complete_task(task_id: str) -> None:
    raise NotImplementedError

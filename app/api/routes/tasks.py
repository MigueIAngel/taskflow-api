import math
from typing import Literal

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.api.routes.projects import get_owned_project
from app.models import Task, TaskPriority, TaskStatus
from app.schemas.common import Page
from app.schemas.task import TaskCreate, TaskRead, TaskUpdate

router = APIRouter(prefix="/projects/{project_id}/tasks", tags=["tasks"])

SORT_FIELDS = {
    "created_at": Task.created_at,
    "due_date": Task.due_date,
    "priority": Task.priority,
    "title": Task.title,
}


def get_task(db: DbSession, project_id: int, task_id: int) -> Task:
    task = db.get(Task, task_id)
    if task is None or task.project_id != project_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Task not found")
    return task


@router.get("", response_model=Page[TaskRead])
def list_tasks(
    project_id: int,
    db: DbSession,
    user: CurrentUser,
    status_: TaskStatus | None = Query(default=None, alias="status"),
    priority: TaskPriority | None = None,
    search: str | None = None,
    sort: Literal["created_at", "due_date", "priority", "title"] = "created_at",
    order: Literal["asc", "desc"] = "desc",
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> Page[TaskRead]:
    get_owned_project(db, project_id, user)
    query = select(Task).where(Task.project_id == project_id)
    if status_:
        query = query.where(Task.status == status_)
    if priority:
        query = query.where(Task.priority == priority)
    if search:
        query = query.where(Task.title.ilike(f"%{search}%"))

    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    column = SORT_FIELDS[sort]
    query = query.order_by(column.asc() if order == "asc" else column.desc())
    items = db.scalars(query.offset((page - 1) * size).limit(size)).all()
    return Page(
        items=[TaskRead.model_validate(t) for t in items],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


@router.post("", response_model=TaskRead, status_code=status.HTTP_201_CREATED)
def create_task(project_id: int, payload: TaskCreate, db: DbSession, user: CurrentUser) -> Task:
    get_owned_project(db, project_id, user)
    task = Task(**payload.model_dump(), project_id=project_id)
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


@router.get("/{task_id}", response_model=TaskRead)
def read_task(project_id: int, task_id: int, db: DbSession, user: CurrentUser) -> Task:
    get_owned_project(db, project_id, user)
    return get_task(db, project_id, task_id)


@router.patch("/{task_id}", response_model=TaskRead)
def update_task(
    project_id: int, task_id: int, payload: TaskUpdate, db: DbSession, user: CurrentUser
) -> Task:
    get_owned_project(db, project_id, user)
    task = get_task(db, project_id, task_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(task, field, value)
    db.commit()
    db.refresh(task)
    return task


@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(project_id: int, task_id: int, db: DbSession, user: CurrentUser) -> None:
    get_owned_project(db, project_id, user)
    db.delete(get_task(db, project_id, task_id))
    db.commit()

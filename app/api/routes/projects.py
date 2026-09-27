import math
from datetime import date

from fastapi import APIRouter, HTTPException, Query, status
from sqlalchemy import func, select

from app.api.deps import CurrentUser, DbSession
from app.models import Project, Task, TaskStatus
from app.schemas.common import Page
from app.schemas.project import ProjectCreate, ProjectRead, ProjectStats, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


def get_owned_project(db: DbSession, project_id: int, user: CurrentUser) -> Project:
    project = db.get(Project, project_id)
    if project is None or project.owner_id != user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


@router.get("", response_model=Page[ProjectRead])
def list_projects(
    db: DbSession,
    user: CurrentUser,
    search: str | None = Query(default=None, description="Filter by name"),
    page: int = Query(default=1, ge=1),
    size: int = Query(default=20, ge=1, le=100),
) -> Page[ProjectRead]:
    query = select(Project).where(Project.owner_id == user.id)
    if search:
        query = query.where(Project.name.ilike(f"%{search}%"))
    total = db.scalar(select(func.count()).select_from(query.subquery())) or 0
    items = db.scalars(
        query.order_by(Project.created_at.desc()).offset((page - 1) * size).limit(size)
    ).all()
    return Page(
        items=[ProjectRead.model_validate(p) for p in items],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if total else 0,
    )


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: DbSession, user: CurrentUser) -> Project:
    project = Project(**payload.model_dump(), owner_id=user.id)
    db.add(project)
    db.commit()
    db.refresh(project)
    return project


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: DbSession, user: CurrentUser) -> Project:
    return get_owned_project(db, project_id, user)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int, payload: ProjectUpdate, db: DbSession, user: CurrentUser
) -> Project:
    project = get_owned_project(db, project_id, user)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(project, field, value)
    db.commit()
    db.refresh(project)
    return project


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: DbSession, user: CurrentUser) -> None:
    project = get_owned_project(db, project_id, user)
    db.delete(project)
    db.commit()


@router.get("/{project_id}/stats", response_model=ProjectStats)
def project_stats(project_id: int, db: DbSession, user: CurrentUser) -> ProjectStats:
    get_owned_project(db, project_id, user)
    rows = db.execute(
        select(Task.status, func.count()).where(Task.project_id == project_id).group_by(Task.status)
    ).all()
    counts = {status_: count for status_, count in rows}
    total = sum(counts.values())
    overdue = (
        db.scalar(
            select(func.count()).where(
                Task.project_id == project_id,
                Task.status != TaskStatus.done,
                Task.due_date < date.today(),
            )
        )
        or 0
    )
    done = counts.get(TaskStatus.done, 0)
    return ProjectStats(
        total=total,
        todo=counts.get(TaskStatus.todo, 0),
        in_progress=counts.get(TaskStatus.in_progress, 0),
        done=done,
        overdue=overdue,
        completion_rate=round(done / total, 2) if total else 0.0,
    )

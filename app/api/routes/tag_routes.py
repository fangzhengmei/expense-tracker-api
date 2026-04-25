from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.schemas.tag_schema import TagCreate, TagUpdate, TagOut, TagWithStats
from app.db.database import get_db

from app.services.tag_service import (
    create_tag,
    get_tags_by_user,
    get_tag_by_user,
    update_tag_by_user,
    delete_tag_by_user,
    get_tag_stats,
    get_all_tag_stats,
    TagNotFoundError,
    TagAlreadyExistsError
)

from app.api.deps import get_current_user


router = APIRouter()


@router.post("/", response_model=TagOut)
def create_tag_endpoint(
    tag: TagCreate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return create_tag(
            db,
            name=tag.name,
            user_id=user.id,
            color=tag.color or "#6366f1"
        )
    except TagAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/", response_model=list[TagOut])
def list_tags(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_tags_by_user(db, user.id)


@router.get("/stats", response_model=list[TagWithStats])
def list_tags_with_stats(
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    return get_all_tag_stats(db, user.id)


@router.get("/{tag_id}", response_model=TagOut)
def get_tag(
    tag_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    tag = get_tag_by_user(db, tag_id, user.id)
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    return tag


@router.get("/{tag_id}/stats", response_model=TagWithStats)
def get_tag_statistics(
    tag_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        tag = get_tag_by_user(db, tag_id, user.id)
        if not tag:
            raise HTTPException(status_code=404, detail="Tag not found")
        
        stats = get_tag_stats(db, user.id, tag_id)
        return TagWithStats(
            id=tag.id,
            name=tag.name,
            color=tag.color,
            user_id=tag.user_id,
            expense_count=stats["expense_count"],
            total_amount=stats["total_amount"]
        )
    except TagNotFoundError:
        raise HTTPException(status_code=404, detail="Tag not found")


@router.put("/{tag_id}", response_model=TagOut)
def update_tag_endpoint(
    tag_id: int,
    tag: TagUpdate,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        return update_tag_by_user(
            db,
            tag_id=tag_id,
            user_id=user.id,
            name=tag.name,
            color=tag.color
        )
    except TagNotFoundError:
        raise HTTPException(status_code=404, detail="Tag not found")
    except TagAlreadyExistsError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.delete("/{tag_id}")
def delete_tag_endpoint(
    tag_id: int,
    user=Depends(get_current_user),
    db: Session = Depends(get_db)
):
    try:
        delete_tag_by_user(db, tag_id, user.id)
        return {"message": "Tag deleted successfully"}
    except TagNotFoundError:
        raise HTTPException(status_code=404, detail="Tag not found")

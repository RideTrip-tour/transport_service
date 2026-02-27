from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud.transport_type_crud import TransportTypeCrud
from app.db.database import get_async_session
from app.schemas.transport_type import (
    TransportTypeCreate,
    TransportTypeRead,
    TransportTypeUpdate,
)

router = APIRouter(prefix="/types", tags=["transport-types"])


@router.post("", response_model=TransportTypeRead, status_code=status.HTTP_201_CREATED)
async def create_type(
    payload: TransportTypeCreate,
    session: AsyncSession = Depends(get_async_session),
) -> TransportTypeRead:
    """Создать новый вид транспорта."""
    exists = await TransportTypeCrud.get_by_code(session, payload.code)
    if exists:
        raise HTTPException(
            status_code=409, detail="Transport type code already exists"
        )
    item = await TransportTypeCrud.create(session, payload)
    return TransportTypeRead.model_validate(item)


@router.get("", response_model=list[TransportTypeRead])
async def list_types(
    session: AsyncSession = Depends(get_async_session),
) -> list[TransportTypeRead]:
    """Получить список всех видов транспорта."""
    items = await TransportTypeCrud.list(session)
    return [TransportTypeRead.model_validate(item) for item in items]


@router.get("/{item_id}", response_model=TransportTypeRead)
async def get_type(
    item_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> TransportTypeRead:
    """Получить вид транспорта по идентификатору."""
    item = await TransportTypeCrud.get(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Transport type not found")
    return TransportTypeRead.model_validate(item)


@router.patch("/{item_id}", response_model=TransportTypeRead)
async def update_type(
    item_id: int,
    payload: TransportTypeUpdate,
    session: AsyncSession = Depends(get_async_session),
) -> TransportTypeRead:
    """Обновить данные вида транспорта."""
    item = await TransportTypeCrud.get(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Transport type not found")
    if payload.code:
        same_code = await TransportTypeCrud.get_by_code(session, payload.code)
        if same_code and same_code.id != item_id:
            raise HTTPException(
                status_code=409, detail="Transport type code already exists"
            )

    updated = await TransportTypeCrud.update(session, item, payload)
    return TransportTypeRead.model_validate(updated)


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_type(
    item_id: int,
    session: AsyncSession = Depends(get_async_session),
) -> None:
    """Мягко удалить вид транспорта (деактивировать запись)."""
    item = await TransportTypeCrud.get(session, item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Transport type not found")
    await TransportTypeCrud.update(
        session=session,
        item=item,
        data=TransportTypeUpdate(is_active=False),
    )

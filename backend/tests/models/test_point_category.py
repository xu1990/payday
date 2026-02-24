import pytest
from app.models.point_category import PointCategory
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_category(db_session: AsyncSession):
    """Test creating a root category"""
    category = PointCategory(
        name="实物奖励",
        description="实物商品奖励",
        level=1,
        sort_order=0,
        is_active=True
    )
    db_session.add(category)
    await db_session.flush()

    assert category.id is not None
    assert category.name == "实物奖励"
    assert category.level == 1
    assert category.parent_id is None


@pytest.mark.asyncio
async def test_create_subcategory(db_session: AsyncSession):
    """Test creating a subcategory with parent"""
    parent = PointCategory(
        name="实物奖励",
        level=1,
        sort_order=0
    )
    db_session.add(parent)
    await db_session.flush()

    child = PointCategory(
        name="数码产品",
        parent_id=parent.id,
        level=2,
        sort_order=0
    )
    db_session.add(child)
    await db_session.flush()

    assert child.parent_id == parent.id
    assert child.level == 2

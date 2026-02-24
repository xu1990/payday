"""
单元测试 - 积分分类服务 (app.services.point_category_service)
"""
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.point_category_service import (
    create_category,
    get_category,
    list_categories,
    get_category_tree,
    update_category,
    delete_category,
)
from app.core.exceptions import NotFoundException, ValidationException


@pytest.mark.asyncio
async def test_create_root_category(db_session: AsyncSession):
    """Test creating a root category"""
    category = await create_category(
        db_session,
        name="实物奖励",
        description="实物商品",
        level=1
    )

    assert category.id is not None
    assert category.name == "实物奖励"
    assert category.level == 1
    assert category.parent_id is None
    assert category.description == "实物商品"


@pytest.mark.asyncio
async def test_create_subcategory(db_session: AsyncSession):
    """Test creating a subcategory"""
    parent = await create_category(
        db_session,
        name="实物奖励",
        level=1
    )

    child = await create_category(
        db_session,
        name="数码产品",
        parent_id=parent.id,
        level=2
    )

    assert child.parent_id == parent.id
    assert child.level == 2


@pytest.mark.asyncio
async def test_get_category(db_session: AsyncSession):
    """Test getting a category by ID"""
    category = await create_category(
        db_session,
        name="测试分类",
        level=1
    )

    fetched = await get_category(db_session, category.id)

    assert fetched.id == category.id
    assert fetched.name == "测试分类"


@pytest.mark.asyncio
async def test_get_category_not_found(db_session: AsyncSession):
    """Test getting a non-existent category"""
    with pytest.raises(NotFoundException):
        await get_category(db_session, "nonexistent-id")


@pytest.mark.asyncio
async def test_list_categories(db_session: AsyncSession):
    """Test listing categories"""
    # Create root categories
    await create_category(db_session, name="实物", level=1, sort_order=2)
    await create_category(db_session, name="虚拟", level=1, sort_order=1)

    # Create a subcategory
    parent = await create_category(db_session, name="实物", level=1)
    await create_category(db_session, name="数码", parent_id=parent.id, level=2)

    # List root categories only
    categories = await list_categories(db_session, parent_id=None)

    assert len(categories) == 3  # 2 from first batch + 1 parent
    assert all(c.parent_id is None for c in categories)


@pytest.mark.asyncio
async def test_list_categories_active_only(db_session: AsyncSession):
    """Test listing only active categories"""
    await create_category(db_session, name="启用", level=1, is_active=True)
    await create_category(db_session, name="禁用", level=1, is_active=False)

    categories = await list_categories(db_session, parent_id=None, active_only=True)

    assert len(categories) == 1
    assert categories[0].name == "启用"


@pytest.mark.asyncio
async def test_get_category_tree(db_session: AsyncSession):
    """Test getting category tree"""
    parent = await create_category(db_session, name="实物", level=1)
    child1 = await create_category(db_session, name="数码", parent_id=parent.id, level=2)
    child2 = await create_category(db_session, name="日用", parent_id=parent.id, level=2)

    tree = await get_category_tree(db_session)

    assert len(tree) == 1
    assert tree[0]["name"] == "实物"
    assert len(tree[0]["children"]) == 2
    child_names = {c["name"] for c in tree[0]["children"]}
    assert "数码" in child_names
    assert "日用" in child_names


@pytest.mark.asyncio
async def test_get_category_tree_nested(db_session: AsyncSession):
    """Test getting nested category tree (3 levels)"""
    # Level 1
    root = await create_category(db_session, name="一级分类", level=1)

    # Level 2
    child = await create_category(db_session, name="二级分类", parent_id=root.id, level=2)

    # Level 3
    grandchild = await create_category(db_session, name="三级分类", parent_id=child.id, level=3)

    tree = await get_category_tree(db_session)

    assert len(tree) == 1
    assert tree[0]["name"] == "一级分类"
    assert len(tree[0]["children"]) == 1
    assert tree[0]["children"][0]["name"] == "二级分类"
    assert len(tree[0]["children"][0]["children"]) == 1
    assert tree[0]["children"][0]["children"][0]["name"] == "三级分类"


@pytest.mark.asyncio
async def test_update_category(db_session: AsyncSession):
    """Test updating a category"""
    category = await create_category(db_session, name="旧名称", level=1)

    updated = await update_category(
        db_session,
        category.id,
        name="新名称",
        description="新描述"
    )

    assert updated.name == "新名称"
    assert updated.description == "新描述"


@pytest.mark.asyncio
async def test_update_category_not_found(db_session: AsyncSession):
    """Test updating a non-existent category"""
    with pytest.raises(NotFoundException):
        await update_category(db_session, "nonexistent-id", name="新名称")


@pytest.mark.asyncio
async def test_delete_category(db_session: AsyncSession):
    """Test deleting a category"""
    category = await create_category(db_session, name="待删除", level=1)

    await delete_category(db_session, category.id)

    # Verify category is deleted
    with pytest.raises(NotFoundException):
        await get_category(db_session, category.id)


@pytest.mark.asyncio
async def test_delete_category_with_children(db_session: AsyncSession):
    """Test deleting a category with children should fail"""
    parent = await create_category(db_session, name="父分类", level=1)
    await create_category(db_session, name="子分类", parent_id=parent.id, level=2)

    with pytest.raises(ValidationException):
        await delete_category(db_session, parent.id)


@pytest.mark.asyncio
async def test_delete_category_not_found(db_session: AsyncSession):
    """Test deleting a non-existent category"""
    with pytest.raises(NotFoundException):
        await delete_category(db_session, "nonexistent-id")

"""规格模板服务"""
import json
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundException, ValidationException
from app.models.specification_template import SpecificationTemplate


async def list_templates(
    db: AsyncSession,
    active_only: bool = False,
) -> List[SpecificationTemplate]:
    """
    获取规格模板列表

    Args:
        db: 数据库会话
        active_only: 是否只返回启用的模板

    Returns:
        模板列表
    """
    query = select(SpecificationTemplate)

    if active_only:
        query = query.where(SpecificationTemplate.is_active == True)

    query = query.order_by(
        SpecificationTemplate.sort_order.desc(),
        SpecificationTemplate.created_at.desc()
    )

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_template(db: AsyncSession, template_id: str) -> SpecificationTemplate:
    """
    获取单个模板

    Args:
        db: 数据库会话
        template_id: 模板ID

    Returns:
        模板对象

    Raises:
        NotFoundException: 模板不存在
    """
    result = await db.execute(
        select(SpecificationTemplate).where(SpecificationTemplate.id == template_id)
    )
    template = result.scalar_one_or_none()

    if not template:
        raise NotFoundException("规格模板不存在")

    return template


async def create_template(
    db: AsyncSession,
    name: str,
    values: List[str],
    description: Optional[str] = None,
    sort_order: int = 0,
    is_active: bool = True,
) -> SpecificationTemplate:
    """
    创建规格模板

    Args:
        db: 数据库会话
        name: 规格名称
        values: 规格值列表
        description: 描述
        sort_order: 排序权重
        is_active: 是否启用

    Returns:
        创建的模板对象

    Raises:
        ValidationException: 参数验证失败
    """
    if not name or not name.strip():
        raise ValidationException("规格名称不能为空")

    if not values or len(values) == 0:
        raise ValidationException("规格值不能为空")

    # 过滤空值并去重
    clean_values = list(dict.fromkeys(v.strip() for v in values if v and v.strip()))

    if len(clean_values) == 0:
        raise ValidationException("规格值不能为空")

    template = SpecificationTemplate(
        name=name.strip(),
        description=description,
        values_json=json.dumps(clean_values, ensure_ascii=False),
        sort_order=sort_order,
        is_active=is_active,
    )

    db.add(template)
    await db.commit()
    await db.refresh(template)

    return template


async def update_template(
    db: AsyncSession,
    template_id: str,
    **kwargs
) -> SpecificationTemplate:
    """
    更新规格模板

    Args:
        db: 数据库会话
        template_id: 模板ID
        **kwargs: 要更新的字段

    Returns:
        更新后的模板对象

    Raises:
        NotFoundException: 模板不存在
        ValidationException: 参数验证失败
    """
    template = await get_template(db, template_id)

    # 处理 values 字段
    if 'values' in kwargs:
        values = kwargs.pop('values')
        if not values or len(values) == 0:
            raise ValidationException("规格值不能为空")

        clean_values = list(dict.fromkeys(v.strip() for v in values if v and v.strip()))
        if len(clean_values) == 0:
            raise ValidationException("规格值不能为空")

        kwargs['values_json'] = json.dumps(clean_values, ensure_ascii=False)

    # 更新字段
    for key, value in kwargs.items():
        if hasattr(template, key) and value is not None:
            setattr(template, key, value)

    await db.commit()
    await db.refresh(template)

    return template


async def delete_template(db: AsyncSession, template_id: str) -> None:
    """
    删除规格模板

    Args:
        db: 数据库会话
        template_id: 模板ID

    Raises:
        NotFoundException: 模板不存在
    """
    template = await get_template(db, template_id)

    await db.delete(template)
    await db.commit()


def template_to_dict(template: SpecificationTemplate) -> dict:
    """
    将模板对象转换为字典

    Args:
        template: 模板对象

    Returns:
        字典表示
    """
    values = []
    if template.values_json:
        try:
            values = json.loads(template.values_json)
        except:
            pass

    return {
        "id": template.id,
        "name": template.name,
        "description": template.description,
        "values": values,
        "sort_order": template.sort_order,
        "is_active": bool(template.is_active),
        "created_at": template.created_at.isoformat() if template.created_at else None,
        "updated_at": template.updated_at.isoformat() if template.updated_at else None,
    }

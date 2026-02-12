"""
敏感词服务 - 管理敏感词的增删改查
"""
from typing import List, Optional
import uuid

from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.sensitive_word import SensitiveWord
from app.core.exceptions import NotFoundException, BusinessException


async def list_words(
    db: AsyncSession,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> List[SensitiveWord]:
    """获取敏感词列表，可选按分类和状态筛选"""
    query = select(SensitiveWord)

    if category:
        query = query.where(SensitiveWord.category == category)
    if is_active is not None:
        query = query.where(SensitiveWord.is_active == is_active)

    query = query.order_by(SensitiveWord.created_at.desc())

    result = await db.execute(query)
    return list(result.scalars().all())


async def get_word_by_id(db: AsyncSession, word_id: str) -> Optional[SensitiveWord]:
    """根据 ID 获取敏感词"""
    result = await db.execute(
        select(SensitiveWord).where(SensitiveWord.id == word_id)
    )
    return result.scalar_one_or_none()


async def create_word(
    db: AsyncSession,
    word: str,
    category: str,
) -> SensitiveWord:
    """创建敏感词"""
    # 检查是否已存在
    existing = await db.execute(
        select(SensitiveWord).where(SensitiveWord.word == word)
    )
    if existing.scalar_one_or_none():
        raise BusinessException(f"敏感词「{word}」已存在")

    sensitive_word = SensitiveWord(
        id=str(uuid.uuid4()).replace("-", ""),
        word=word,
        category=category,
    )
    db.add(sensitive_word)
    await db.commit()
    await db.refresh(sensitive_word)
    return sensitive_word


async def update_word(
    db: AsyncSession,
    word_id: str,
    word: Optional[str] = None,
    category: Optional[str] = None,
    is_active: Optional[bool] = None,
) -> SensitiveWord:
    """更新敏感词"""
    sensitive_word = await get_word_by_id(db, word_id)
    if not sensitive_word:
        raise NotFoundException("敏感词不存在")

    if word is not None:
        # 检查新词是否已被其他记录使用
        existing = await db.execute(
            select(SensitiveWord).where(
                SensitiveWord.word == word,
                SensitiveWord.id != word_id
            )
        )
        if existing.scalar_one_or_none():
            raise BusinessException(f"敏感词「{word}」已存在")
        sensitive_word.word = word

    if category is not None:
        sensitive_word.category = category
    if is_active is not None:
        sensitive_word.is_active = is_active

    await db.commit()
    await db.refresh(sensitive_word)
    return sensitive_word


async def delete_word(db: AsyncSession, word_id: str) -> bool:
    """删除敏感词"""
    sensitive_word = await get_word_by_id(db, word_id)
    if not sensitive_word:
        return False

    await db.delete(sensitive_word)
    await db.commit()
    return True


async def get_active_words_dict(db: AsyncSession) -> dict:
    """
    获取所有启用的敏感词，按分类组织的字典

    Returns:
        {
            'illegal': ['毒品', '赌博', ...],
            'porn': ['色情', ...],
            ...
        }
    """
    words = await list_words(db, is_active=True)

    result = {}
    for word in words:
        category = word.category
        if category not in result:
            result[category] = []
        result[category].append(word.word)

    return result


async def get_all_active_words_list(db: AsyncSession) -> List[str]:
    """获取所有启用的敏感词（扁平列表）"""
    words = await list_words(db, is_active=True)
    return [w.word for w in words]

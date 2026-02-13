"""
风控服务 - 文本/图片评分与处置建议，与技术方案 3.2 一致
社区版：文本敏感词+联系方式+腾讯云天御集成
"""
import re
from dataclasses import dataclass
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession

from app.utils.tencent_yu import (
    tencent_yu_text_check,
    tencent_yu_image_check,
)
from app.services import sensitive_word_service

@dataclass
class RiskResult:
    score: int  # 0-100
    action: str  # approve | reject | manual
    reason: Optional[str] = None


# 备用硬编码敏感词（当数据库查询失败时使用）
FALLBACK_SENSITIVE_WORDS = [
    # 违法相关
    "毒品", "吸毒", "大麻", "海洛因", "冰毒", "摇头丸", "K粉", "鸦片",
    "卖淫", "嫖娼", "性服务", "情色服务",
    "赌博", "赌场", "博彩", "六合彩", "时时彩", "百家乐", "炸金花",
    "诈骗", "传销", "非法集资", "洗钱", "高利贷", "裸贷",
    "假钞", "假发票", "办证", "买学位", "代考", "代写论文",
    "黑客", "攻击网站", "木马", "钓鱼网站", "刷单", "刷信誉", "刷钻",
    # 违禁品
    "枪支", "弹药", "炸药", "炸弹", "雷管", "手枪", "气枪",
    "管制刀具", "匕首", "三棱刮刀",
    "迷药", "春药", "听话水", "蒙汗药",
    # 极端主义
    "恐怖", "恐怖袭击", "自杀袭击", "人体炸弹", "圣战",
    # 色情低俗
    "色情", "淫秽", "裸聊", "裸舞", "脱衣", "高潮", "做爱",
    "性交", "性虐", "SM", "调教", "肛交", "口交",
    "A片", "AV", "黄片", "黄色网站", "色情网站",
    # 违规医疗
    "流产", "堕胎", "无痛人流", "取环", "上环", "代孕",
    "卖血", "卖肾", "卖器官", "换肾",
    # 宗教/民族
    "法轮功", "邪教", "全能神", "呼喊派", "门徒会",
    # 其他违规
    "翻墙", "VPN", "梯子", "代购",
    "发票", "虚开发票", "套现", "提现",
    "内幕", "内幕消息", "稳赚", "包赚",
]
# 联系方式正则
CONTACT_PATTERNS = [
    re.compile(r"1[3-9]\d{9}"),
    re.compile(r"[\w.-]+@[\w.-]+\.\w+"),
    re.compile(r"qq[号]?[：:\s]*\d{5,12}", re.I),  # 支持QQ、QQ号格式，大小写不敏感
    re.compile(r"微信[：:\s]*[a-zA-Z0-9_-]{6,20}"),
]


def _text_contact_score(content: str) -> tuple[int, Optional[str]]:
    """文本中联系方式与诱导外联，返回 0-100 分与原因。"""
    if not (content or content.strip()):
        return 0, None
    text = content.strip()
    for p in CONTACT_PATTERNS:
        if p.search(text):
            return 80, "含联系方式或诱导外联"
    return 0, None


def _text_sensitive_score(content: str) -> tuple[int, Optional[str]]:
    """
    敏感词检测（简化版，使用硬编码列表）

    注意：此函数不查询数据库，仅使用硬编码的备用列表。
    生产环境应使用 _text_sensitive_score_from_db 以获取最新的敏感词配置。
    """
    if not (content or content.strip()):
        return 0, None

    text = content.strip().lower()

    # 使用硬编码的备用敏感词列表
    for word in FALLBACK_SENSITIVE_WORDS:
        if word.lower() in text:
            return 90, "含违规内容"

    return 0, None


async def _text_yu_score(content: str) -> tuple[int, Optional[str]]:
    """
    腾讯云天御文本审核

    Returns:
        (score, reason): 0-100分，失败原因
    """
    try:
        return await tencent_yu_text_check(content)
    except Exception as e:
        # 天御服务失败时降级到本地检测
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.warning(f"天御文本审核失败，降级到本地检测: {e}")
        return 0, None


async def _image_score(urls: Optional[List[str]]) -> tuple[int, Optional[str]]:
    """
    图片审核 - 调用腾讯云天御

    Returns:
        (score, reason): 最高分图片的评分和原因
    """
    if not urls:
        return 0, None

    max_score = 0
    worst_reason = None

    for url in urls:
        try:
            score, reason = await tencent_yu_image_check(url)
            if score > max_score:
                max_score = score
                worst_reason = reason
        except Exception as e:
            from app.utils.logger import get_logger
            logger = get_logger(__name__)
            logger.warning(f"图片审核失败: {e}")
            # 单张图片失败不影响整体，继续处理其他图片
            continue

    return max_score, worst_reason


async def evaluate_content(
    db: AsyncSession,
    content: str,
    images: Optional[List[str]] = None,
    use_yu: bool = True,
) -> RiskResult:
    """
    综合文本+图片评分，与技术方案 3.2 权重一致。
    文本权重更高；取各维度最高分并给出 action。

    Args:
        db: 数据库会话
        content: 文本内容
        images: 图片URL列表
        use_yu: 是否使用腾讯云天御（默认True）
    """
    reasons: List[str] = []
    max_score = 0

    # 文本：敏感词（从数据库获取）
    s1, r1 = await _text_sensitive_score_from_db(db, content or "")
    if s1 > max_score:
        max_score = s1
    if r1 and r1 not in reasons:
        reasons.append(r1)

    # 文本：联系方式/诱导
    s2, r2 = _text_contact_score(content or "")
    if s2 > max_score:
        max_score = s2
    if r2 and r2 not in reasons:
        reasons.append(r2)

    # 文本：腾讯云天御（可选）
    if use_yu:
        s3, r3 = await _text_yu_score(content or "")
        if s3 > max_score:
            max_score = s3
        if r3 and r3 not in reasons:
            reasons.append(r3)

    # 图片：腾讯云天御
    if images:
        s4, r4 = await _image_score(images)
        if s4 > max_score:
            max_score = s4
        if r4 and r4 not in reasons:
            reasons.append(r4)

    reason = "; ".join(reasons) if reasons else None

    if max_score >= 80:
        return RiskResult(score=max_score, action="reject", reason=reason)
    if max_score >= 50:
        return RiskResult(score=max_score, action="manual", reason=reason)
    return RiskResult(score=max_score, action="approve", reason=reason)


async def _text_sensitive_score_from_db(db: AsyncSession, content: str) -> tuple[int, Optional[str]]:
    """
    从数据库获取敏感词并检测

    Returns:
        (score, reason): 0-100分，失败原因
    """
    if not (content or content.strip()):
        return 0, None

    text = content.strip().lower()

    try:
        # 从数据库获取所有启用的敏感词
        words = await sensitive_word_service.get_all_active_words_list(db)

        for word in words:
            if word.lower() in text:
                return 90, "含违规内容"
    except Exception as e:
        # 数据库查询失败时，使用硬编码备用列表
        from app.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.warning(f"敏感词数据库查询失败，使用备用列表: {e}")

        for word in FALLBACK_SENSITIVE_WORDS:
            if word.lower() in text:
                return 90, "含违规内容"

    return 0, None

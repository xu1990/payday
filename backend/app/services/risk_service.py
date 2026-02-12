"""
风控服务 - 文本/图片评分与处置建议，与技术方案 3.2 一致
社区版：文本敏感词+联系方式；图片可 mock，后续接腾讯云天御
"""
import re
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class RiskResult:
    score: int  # 0-100
    action: str  # approve | reject | manual
    reason: Optional[str] = None


# 敏感词（社区版示例，可改为配置/数据库）
SENSITIVE_WORDS = [
    "违禁词1",
    "违禁词2",
]
# 联系方式正则
CONTACT_PATTERNS = [
    re.compile(r"1[3-9]\d{9}"),
    re.compile(r"[\w.-]+@[\w.-]+\.\w+"),
    re.compile(r"qq[：:\s]*\d{5,12}", re.I),
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
    """敏感词检测，返回 0-100 分与原因。"""
    if not (content or content.strip()):
        return 0, None
    text = content.lower().strip()
    for w in SENSITIVE_WORDS:
        if w.lower() in text:
            return 90, "含违规内容"
    return 0, None


def _image_score(urls: Optional[List[str]]) -> tuple[int, Optional[str]]:
    """图片审核，社区版 mock 通过。"""
    if not urls:
        return 0, None
    # 预留：调用腾讯云天御；当前返回 0
    return 0, None


def evaluate_content(
    content: str,
    images: Optional[List[str]] = None,
) -> RiskResult:
    """
    综合文本+图片评分，与技术方案 3.2 权重一致。
    文本权重更高；取各维度最高分并给出 action。
    """
    reasons: List[str] = []
    max_score = 0

    # 文本：敏感词
    s1, r1 = _text_sensitive_score(content or "")
    if s1 > max_score:
        max_score = s1
        if r1:
            reasons.append(r1)

    # 文本：联系方式/诱导
    s2, r2 = _text_contact_score(content or "")
    if s2 > max_score:
        max_score = s2
        if r2 and r2 not in reasons:
            reasons.append(r2)

    # 图片（社区版 mock）
    s3, r3 = _image_score(images)
    if s3 > max_score:
        max_score = s3
        if r3:
            reasons.append(r3)

    reason = "; ".join(reasons) if reasons else None

    if max_score >= 80:
        return RiskResult(score=max_score, action="reject", reason=reason)
    if max_score >= 50:
        return RiskResult(score=max_score, action="manual", reason=reason)
    return RiskResult(score=max_score, action="approve", reason=reason)

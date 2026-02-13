"""
腾讯云天御内容安全服务集成
技术方案 3.2.2 - 文本/图片审核
"""
import base64
import json
from typing import Dict, List, Optional
from tencentcloud.common import credential
from tencentcloud.common.exception.tencent_cloud_sdk_exception import TencentCloudSDKException
from tencentcloud.tms.v20200713 import tms_client, models as tms_models
from tencentcloud.ims.v20201229 import ims_client, models as ims_models
from tencentcloud.ocr.v20181119 import ocr_client, models as ocr_models

from app.core.config import settings
from app.utils.logger import get_logger

logger = get_logger(__name__)


class TencentYuService:
    """腾讯云天御内容安全服务"""

    def __init__(self):
        """初始化天御客户端"""
        if not all([settings.tencent_secret_id, settings.tencent_secret_key]):
            logger.warning("腾讯云密钥未配置，天御服务将不可用")
            self._enabled = False
            self.ims_client = None
            self.tms_client = None
            self.ocr_client = None
            return

        try:
            # 初始化认证
            cred = credential.Credential(
                settings.tencent_secret_id,
                settings.tencent_secret_key
            )

            # 图片审核客户端
            self.ims_client = ims_client.ImsClient(
                cred,
                settings.TENCENT_REGION or "ap-guangzhou",
            )

            # 文本审核客户端
            self.tms_client = tms_client.TmsClient(
                cred,
                settings.TENCENT_REGION or "ap-guangzhou",
            )

            # OCR 客户端
            self.ocr_client = ocr_client.OcrClient(
                cred,
                settings.TENCENT_REGION or "ap-guangzhou",
            )

            self._enabled = True
            logger.info("腾讯云天御服务初始化成功")

        except Exception as e:
            logger.error(f"腾讯云天御服务初始化失败: {e}")
            self._enabled = False
            self.ims_client = None
            self.tms_client = None
            self.ocr_client = None

    @property
    def enabled(self) -> bool:
        """检查服务是否可用"""
        return self._enabled

    async def image_moderation(self, image_url: str) -> Dict[str, any]:
        """
        图片审核

        Args:
            image_url: 图片URL

        Returns:
            {
                "suggestion": "pass" | "review" | "block",
                "labels": List[str],
                "details": List[dict],
                "porn": bool,      # 色情
                "violence": bool,   # 暴力
                "ad": bool,         # 广告
            }
        """
        if not self.enabled:
            logger.warning("天御服务未启用，跳过图片审核")
            return {"suggestion": "pass", "labels": [], "details": [], "porn": False, "violence": False, "ad": False}

        try:
            req = ims_models.ImageModerationRequest()
            params = {
                "ImageUrl": image_url,
                "BizType": settings.TENCENT_YU_BIZ_TYPE if hasattr(settings, 'TENCENT_YU_BIZ_TYPE') else "payday_risk_check",
            }
            req.from_json_string(json.dumps(params))

            resp = self.ims_client.ImageModeration(req)

            # 解析结果
            suggestion = resp.Suggestion  # pass/review/block
            labels = resp.Labels if hasattr(resp, 'Labels') else []

            # 分类标签
            porn = "Porn" in labels if labels else False
            violence = "Violence" in labels if labels else False
            ad = "Ad" in labels if labels else False

            return {
                "suggestion": suggestion,
                "labels": labels,
                "details": [],
                "porn": porn,
                "violence": violence,
                "ad": ad,
            }

        except TencentCloudSDKException as e:
            logger.error(f"腾讯云图片审核失败: {e}")
            # 降级：返回审核通过，交由人工审核
            return {"suggestion": "review", "labels": [], "details": [], "porn": False, "violence": False, "ad": False}
        except Exception as e:
            logger.error(f"图片审核异常: {e}")
            return {"suggestion": "review", "labels": [], "details": [], "porn": False, "violence": False, "ad": False}

    async def text_moderation(self, content: str) -> Dict[str, any]:
        """
        文本审核

        Args:
            content: 待审核文本

        Returns:
            {
                "suggestion": "pass" | "review" | "block",
                "labels": List[str],
                "details": List[dict],
            }
        """
        if not self.enabled:
            logger.warning("天御服务未启用，跳过文本审核")
            return {"suggestion": "pass", "labels": [], "details": []}

        try:
            req = tms_models.TextModerationRequest()
            # 内容需要 base64 编码
            params = {
                "Content": base64.b64encode(content.encode('utf-8')).decode('utf-8'),
                "BizType": settings.TENCENT_YU_BIZ_TYPE if hasattr(settings, 'TENCENT_YU_BIZ_TYPE') else "payday_risk_check",
            }
            req.from_json_string(json.dumps(params))

            resp = self.tms_client.TextModeration(req)

            return {
                "suggestion": resp.Suggestion,
                "labels": resp.Labels if hasattr(resp, 'Labels') else [],
                "details": resp.DetailResults if hasattr(resp, 'DetailResults') else [],
            }

        except TencentCloudSDKException as e:
            logger.error(f"腾讯云文本审核失败: {e}")
            # 降级：返回审核通过，交由人工审核
            return {"suggestion": "review", "labels": [], "details": []}
        except Exception as e:
            logger.error(f"文本审核异常: {e}")
            return {"suggestion": "review", "labels": [], "details": []}

    async def ocr_extract_text(self, image_url: str) -> Optional[str]:
        """
        OCR 提取图片文字（用于工资截图敏感信息检测）

        Args:
            image_url: 图片URL

        Returns:
            提取的文本内容，失败返回 None
        """
        if not self.enabled:
            logger.warning("天御服务未启用，跳过OCR提取")
            return None

        try:
            req = ocr_models.GeneralBasicOCRRequest()
            params = {"ImageUrl": image_url}
            req.from_json_string(json.dumps(params))

            resp = self.ocr_client.GeneralBasicOCR(req)

            # 提取所有文字
            if hasattr(resp, 'TextDetections') and resp.TextDetections:
                texts = [item.DetectedText for item in resp.TextDetections if hasattr(item, 'DetectedText')]
                return "\n".join(texts)

            return None

        except TencentCloudSDKException as e:
            logger.error(f"腾讯云OCR失败: {e}")
            return None
        except Exception as e:
            logger.error(f"OCR提取异常: {e}")
            return None

    async def batch_image_moderation(self, image_urls: List[str]) -> List[Dict[str, any]]:
        """
        批量图片审核

        Args:
            image_urls: 图片URL列表

        Returns:
            审核结果列表，与输入顺序一致
        """
        results = []
        for url in image_urls:
            result = await self.image_moderation(url)
            results.append(result)
        return results


# 单例实例
tencent_yu_service = TencentYuService()


async def tencent_yu_image_check(image_url: str) -> tuple[int, Optional[str]]:
    """
    图片审核辅助函数 - 返回评分和原因

    Returns:
        (score, reason): 0-100分，失败原因
        - 0分: 通过 (pass)
        - 50分: 人工审核 (review)
        - 80+分: 拒绝 (block)
    """
    result = await tencent_yu_service.image_moderation(image_url)
    suggestion = result.get("suggestion", "pass")

    if suggestion == "block":
        reasons = []
        if result.get("porn"):
            reasons.append("色情")
        if result.get("violence"):
            reasons.append("暴力")
        if result.get("ad"):
            reasons.append("广告")
        return 90, "图片包含违规内容: " + ", ".join(reasons)

    if suggestion == "review":
        return 50, "图片需要人工审核"

    return 0, None


async def tencent_yu_text_check(content: str) -> tuple[int, Optional[str]]:
    """
    文本审核辅助函数 - 返回评分和原因

    Returns:
        (score, reason): 0-100分，失败原因
        - 0分: 通过 (pass)
        - 50分: 人工审核 (review)
        - 80+分: 拒绝 (block)
    """
    result = await tencent_yu_service.text_moderation(content)
    suggestion = result.get("suggestion", "pass")

    if suggestion == "block":
        labels = result.get("labels", [])
        return 90, f"文本包含违规内容: {', '.join(labels)}"

    if suggestion == "review":
        return 50, "文本需要人工审核"

    return 0, None

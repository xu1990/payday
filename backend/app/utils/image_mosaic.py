"""
图片打码服务 - 技术方案 3.2.3
用于工资截图敏感信息自动脱敏（手机号、身份证、姓名等）
"""
import re
import io
from typing import List, Tuple, Optional
from PIL import Image, ImageDraw

from app.utils.logger import get_logger
from app.utils.tencent_yu import tencent_yu_service

logger = get_logger(__name__)


class ImageMosaicService:
    """图片打码服务 - 工资截图敏感信息脱敏"""

    # 手机号正则（中国大陆）
    PHONE_PATTERN = re.compile(r'1[3-9]\d{9}')

    # 身份证号正则（18位）
    ID_CARD_PATTERN = re.compile(r'\d{17}[\dXx]')

    # 姓名正则(中文)
    NAME_PATTERN = re.compile(r'[\u4e00-\u9fa5]{2,4}(?:\s|:|：|先生|女士|老师)')

    # 银行卡号正则
    BANK_CARD_PATTERN = re.compile(r'\d{16,19}')

    # 敏感关键词
    SENSITIVE_KEYWORDS = [
        '工资', '薪资', '收入', '实发', '应发',
        '基本工资', '绩效', '奖金', '扣款', '税前', '税后',
        '支付宝', '微信', '转账', '账户', '账号',
    ]

    def __init__(self):
        """初始化服务"""
        self.tencent_yu = tencent_yu_service

    async def mosaic_salary_image(
        self,
        image_url: str,
        return_image: bool = False
    ) -> str:
        """
        对工资截图进行自动打码

        Args:
            image_url: 原始图片URL
            return_image: 是否返回打码后的图片URL（True）或返回处理后的图片数据（False）

        Returns:
            如果 return_image=True: 返回打码后的图片URL
            如果 return_image=False: 返回打码后的图片二进制数据
        """
        try:
            # 1. 下载图片
            image_bytes = await self._download_image(image_url)
            image = Image.open(io.BytesIO(image_bytes))

            # 2. OCR 提取文字及位置
            text_data = await self._ocr_extract_text_with_positions(image_url)

            if not text_data:
                # OCR 失败，返回原图
                logger.warning(f"OCR提取失败，跳过打码: {image_url}")
                return image_url if return_image else image_bytes

            # 3. 识别敏感信息位置并打码
            has_mosaic = False
            for item in text_data:
                if self._is_sensitive_text(item['text']):
                    has_mosaic = True
                    position = item.get('polygon') or item.get('position')
                    if position:
                        self._apply_mosaic_at_position(image, position)

            if not has_mosaic:
                logger.info(f"图片中未检测到敏感信息，跳过打码: {image_url}")
                return image_url if return_image else image_bytes

            # 4. 上传打码后的图片
            if return_image:
                # TODO: 上传到 COS 并返回新 URL
                # 暂时：保存到临时文件并返回本地路径
                mosaic_url = await self._upload_mosaic_image(image)
                return mosaic_url
            else:
                # 返回图片二进制数据
                output = io.BytesIO()
                image.save(output, format='PNG')
                return output.getvalue()

        except Exception as e:
            logger.error(f"图片打码失败: {e}")
            # 失败时返回原图
            return image_url if return_image else image_bytes

    async def _download_image(self, url: str) -> bytes:
        """
        下载图片

        TODO: 实际项目中应该使用更健壮的 HTTP 客户端
        """
        import httpx
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.get(url)
            return response.content

    async def _ocr_extract_text_with_positions(
        self,
        image_url: str
    ) -> List[dict]:
        """
        使用腾讯云 OCR 提取文字及位置

        Returns:
            [
                {
                    "text": "文字内容",
                    "polygon": {"x": 100, "y": 200, "width": 50, "height": 20}
                },
                ...
            ]
        """
        try:
            if not self.tencent_yu.enabled:
                return []

            # 调用腾讯云通用印刷体 OCR
            text_data = await self.tencent_yu.ocr_extract_text(image_url)

            if not text_data:
                return []

            # 按行分割
            lines = text_data.split('\n')
            results = []

            # 模拟位置信息（腾讯云 OCR 返回格式需要确认）
            # 实际应该使用 GeneralBasicOCR 返回的 Polygon 信息
            # 这里简化处理，返回文字列表
            for line in lines:
                if line.strip():
                    results.append({
                        "text": line.strip(),
                        # TODO: 从 OCR 结果中提取实际位置信息
                        "position": None
                    })

            return results

        except Exception as e:
            logger.warning(f"OCR提取失败: {e}")
            return []

    def _is_sensitive_text(self, text: str) -> bool:
        """
        判断文本是否为敏感信息

        Args:
            text: 待检测文本

        Returns:
            是否为敏感信息
        """
        # 手机号检测
        if self.PHONE_PATTERN.search(text):
            return True

        # 身份证号检测
        if self.ID_CARD_PATTERN.search(text):
            return True

        # 银行卡号检测
        if self.BANK_CARD_PATTERN.search(text):
            return True

        # 姓名检测
        if self.NAME_PATTERN.search(text):
            return True

        # 敏感关键词检测
        text_lower = text.lower()
        for keyword in self.SENSITIVE_KEYWORDS:
            if keyword in text_lower:
                # 检查关键词周围是否有数字（可能是金额）
                if re.search(r'\d+', text):
                    return True

        return False

    def _apply_mosaic_at_position(
        self,
        image: Image.Image,
        position: dict
    ) -> None:
        """
        在指定位置应用马赛克

        Args:
            image: PIL Image 对象
            position: 位置信息 {"x": int, "y": int, "width": int, "height": int}
        """
        x = position.get('x', 0)
        y = position.get('y', 0)
        w = position.get('width', 0)
        h = position.get('height', 0)

        # 边界检查
        img_width, img_height = image.size
        if x >= img_width or y >= img_height:
            return

        # 调整边界
        x = max(0, min(x, img_width - 1))
        y = max(0, min(y, img_height - 1))
        w = min(w, img_width - x)
        h = min(h, img_height - y)

        if w <= 0 or h <= 0:
            return

        # 提取区域
        region = image.crop((x, y, x + w, y + h))

        # 缩小再放大实现马赛克
        mosaic_scale = 10  # 马赛克颗粒度
        small = region.resize(
            (max(1, w // mosaic_scale), max(1, h // mosaic_scale)),
            Image.Resampling.NEAREST
        )
        mosaic = small.resize((w, h), Image.Resampling.NEAREST)

        # 粘贴回原图
        image.paste(mosaic, (x, y))

    def _apply_mosaic(
        self,
        image: Image.Image,
        boxes: List[Tuple[int, int, int, int]]
    ) -> Image.Image:
        """
        批量应用马赛克

        Args:
            image: PIL Image 对象
            boxes: [(x, y, w, h), ...] 位置列表

        Returns:
            处理后的图片
        """
        draw = ImageDraw.Draw(image)

        for box in boxes:
            x, y, w, h = box

            # 提取区域
            region = image.crop((x, y, x + w, y + h))

            # 缩小再放大实现马赛克
            small = region.resize((max(1, w // 10), max(1, h // 10)), Image.BILINEAR)
            mosaic = small.resize((w, h), Image.BILINEAR)

            # 粘贴回原图
            image.paste(mosaic, (x, y))

        return image

    async def _upload_mosaic_image(self, image: Image.Image) -> str:
        """
        上传打码后的图片

        TODO: 实际项目中应该上传到 COS

        Returns:
            图片URL
        """
        # 暂时：保存到本地临时目录
        import os
        import tempfile

        temp_dir = tempfile.gettempdir()
        filename = f"mosaic_{id(image)}.png"
        filepath = os.path.join(temp_dir, filename)

        image.save(filepath)

        # 返回文件路径（实际应该是 COS URL）
        logger.info(f"打码图片已保存: {filepath}")
        return filepath


# 单例实例
image_mosaic_service = ImageMosaicService()


async def mosaic_salary_image(
    image_url: str,
    return_image: bool = True
) -> str:
    """
    对工资截图进行打码的便捷函数

    Args:
        image_url: 原始图片URL
        return_image: 是否返回打码后的图片URL

    Returns:
        打码后的图片URL或数据
    """
    return await image_mosaic_service.mosaic_salary_image(image_url, return_image)

"""
二维码生成接口 - 用于海报分享
"""
import base64
import io
from datetime import datetime
from typing import Any, Dict, Optional

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import NotFoundException, success_response
from app.services.qrcode_mapping_service import create_qrcode_mapping, get_qrcode_mapping
from app.utils.wechat import get_unlimited_qrcode
from fastapi import APIRouter, Body, Depends, Query
from fastapi.responses import Response
from pydantic import BaseModel, Field

router = APIRouter(prefix="/qrcode", tags=["qrcode"])


class CreateMappingRequest(BaseModel):
    """创建二维码映射请求"""
    page: str = Field(..., description="小程序页面路径", example="pages/poster/index")
    params: Dict[str, Any] = Field(..., description="自定义参数", example={"recordId": "xxx"})
    expires_days: Optional[int] = Field(None, description="过期天数（可选）", ge=1, le=365)


@router.get("")
async def generate_qrcode(
    url: str = Query(..., description="二维码内容URL"),
    size: int = Query(200, ge=100, le=500, description="二维码尺寸"),
    fill_color: str = Query("#333333", description="二维码颜色"),
    back_color: str = Query("#FFFFFF", description="背景颜色"),
):
    """
    生成二维码图片

    返回 PNG 格式的二维码图片
    """
    import qrcode

    # 创建 QR Code 实例
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )

    # 添加数据
    qr.add_data(url)
    qr.make(fit=True)

    # 生成图片
    img = qr.make_image(fill_color=fill_color, back_color=back_color)

    # 调整尺寸
    img = img.resize((size, size))

    # 转换为 PNG bytes
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_bytes = img_io.getvalue()

    # 返回图片
    return Response(content=img_bytes, media_type="image/png")


@router.get("/base64")
async def generate_qrcode_base64(
    url: str = Query(..., description="二维码内容URL"),
    size: int = Query(200, ge=100, le=500, description="二维码尺寸"),
    fill_color: str = Query("#333333", description="二维码颜色"),
    back_color: str = Query("#FFFFFF", description="背景颜色"),
):
    """
    生成二维码并返回 base64 编码

    返回 JSON 格式，包含 base64 编码的图片数据
    """
    import qrcode

    # 创建 QR Code 实例
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=2,
    )

    # 添加数据
    qr.add_data(url)
    qr.make(fit=True)

    # 生成图片
    img = qr.make_image(fill_color=fill_color, back_color=back_color)

    # 调整尺寸
    img = img.resize((size, size))

    # 转换为 base64
    img_io = io.BytesIO()
    img.save(img_io, format='PNG')
    img_bytes = img_io.getvalue()
    img_base64 = base64.b64encode(img_bytes).decode('utf-8')

    # 返回 base64 数据
    return success_response(
        data={
            "base64": f"data:image/png;base64,{img_base64}",
            "size": size,
        },
        message="生成二维码成功"
    )


@router.get("/wxa")
async def generate_wxa_qrcode(
    scene: str = Query(..., description="场景值，如 'recordId=xxx' 或 'postId=xxx'"),
    page: str = Query("pages/index", description="小程序页面路径"),
    width: int = Query(430, ge=80, le=4300, description="小程序码宽度"),
):
    """
    生成微信小程序码（无限制）

    返回 PNG 格式的小程序码图片
    用户扫码可直接进入小程序指定页面
    """
    qr_data = await get_unlimited_qrcode(
        scene=scene,
        page=page,
        width=width,
    )
    return Response(content=qr_data, media_type="image/png")


@router.get("/wxa/base64")
async def generate_wxa_qrcode_base64(
    scene: str = Query(..., description="场景值，如 'recordId=xxx' 或 'postId=xxx'"),
    page: str = Query("pages/index", description="小程序页面路径"),
    width: int = Query(430, ge=80, le=4300, description="小程序码宽度"),
):
    """
    生成微信小程序码并返回 base64 编码

    返回 JSON 格式，包含 base64 编码的小程序码图片数据
    """
    qr_data = await get_unlimited_qrcode(
        scene=scene,
        page=page,
        width=width,
    )

    # 转换为 base64
    img_base64 = base64.b64encode(qr_data).decode('utf-8')

    return success_response(
        data={
            "base64": f"data:image/png;base64,{img_base64}",
            "width": width,
            "scene": scene,
            "page": page,
        },
        message="生成小程序码成功"
    )


# ==================== 新方案：参数映射系统 ====================

@router.post("/wxa/mapping")
async def create_qrcode_mapping_endpoint(
    request: CreateMappingRequest,
    db=Depends(get_db)
):
    """
    创建二维码参数映射

    1. 接收前端传来的页面路径和自定义参数
    2. 生成唯一短码
    3. 保存到数据库
    4. 返回短码供后续生成小程序码使用
    """
    mapping = await create_qrcode_mapping(
        db,
        page=request.page,
        params=request.params,
        expires_days=request.expires_days
    )

    return success_response(
        data={
            "short_code": mapping.short_code,
            "id": mapping.id,
            "page": mapping.page,
            "params": mapping.params,
            "expires_at": mapping.expires_at.isoformat() if mapping.expires_at else None,
        },
        message="创建二维码映射成功"
    )


@router.get("/wxa/mapping/{short_code}")
async def get_qrcode_mapping_endpoint(
    short_code: str,
    db=Depends(get_db)
):
    """
    查询二维码参数映射

    小程序扫码后，通过短码查询原始参数
    自动增加扫描次数
    """
    mapping = await get_qrcode_mapping(db, short_code, increment_scan=True)

    if not mapping:
        raise NotFoundException("二维码不存在或已过期")

    return success_response(
        data={
            "page": mapping.page,
            "params": mapping.params,
            "scan_count": mapping.scan_count,
            "is_expired": mapping.expires_at and mapping.expires_at < datetime.utcnow(),
        },
        message="查询成功"
    )


@router.get("/wxa/mapping/{short_code}/qrcode")
async def generate_wxa_qrcode_by_mapping(
    short_code: str,
    width: int = Query(430, ge=80, le=4300, description="小程序码宽度"),
    db=Depends(get_db)
):
    """
    通过短码生成小程序码（PNG图片）

    1. 根据短码查询映射
    2. 使用短码作为 scene 参数
    3. 返回小程序码图片
    """
    mapping = await get_qrcode_mapping(db, short_code, increment_scan=False)

    if not mapping:
        raise NotFoundException("二维码不存在或已过期")

    # 使用短码作为 scene（简洁）
    scene = short_code

    qr_data = await get_unlimited_qrcode(
        scene=scene,
        page=mapping.page,
        width=width,
    )

    return Response(content=qr_data, media_type="image/png")


@router.get("/wxa/mapping/{short_code}/qrcode/base64")
async def generate_wxa_qrcode_by_mapping_base64(
    short_code: str,
    width: int = Query(430, ge=80, le=4300, description="小程序码宽度"),
    db=Depends(get_db)
):
    """
    通过短码生成小程序码（base64 JSON）

    1. 根据短码查询映射
    2. 使用短码作为 scene 参数
    3. 返回 base64 格式的小程序码
    """
    mapping = await get_qrcode_mapping(db, short_code, increment_scan=False)

    if not mapping:
        raise NotFoundException("二维码不存在或已过期")

    # 使用短码作为 scene（简洁）
    scene = short_code

    qr_data = await get_unlimited_qrcode(
        scene=scene,
        page=mapping.page,
        width=width,
    )

    # 转换为 base64
    img_base64 = base64.b64encode(qr_data).decode('utf-8')

    return success_response(
        data={
            "base64": f"data:image/png;base64,{img_base64}",
            "short_code": short_code,
            "width": width,
            "page": mapping.page,
            "params": mapping.params,
        },
        message="生成小程序码成功"
    )


@router.post("/wxa/generate")
async def create_qrcode_with_mapping(
    request: CreateMappingRequest,
    width: int = Query(430, ge=80, le=4300, description="小程序码宽度"),
    db=Depends(get_db)
):
    """
    一体化二维码生成接口（创建映射 + 生成二维码）

    1. 创建参数映射，获取短码
    2. 尝试生成微信小程序码
    3. 如果微信API失败（开发环境页面不存在），降级为普通二维码
    4. 直接返回 base64 格式的二维码图片

    前端只需调用一次此接口即可获得完整的二维码图片
    """
    from app.utils.logger import get_logger
    logger = get_logger(__name__)

    # 步骤1: 创建映射
    try:
        mapping = await create_qrcode_mapping(
            db,
            page=request.page,
            params=request.params,
            expires_days=request.expires_days
        )
        short_code = mapping.short_code
    except Exception as e:
        logger.error(f"Failed to create qrcode mapping: {e}")
        raise

    # 步骤2: 尝试生成微信小程序码
    try:
        # 生成包含完整URL的scene参数（用于普通二维码降级）
        # 小程序扫码后会通过短码查询获取原始参数
        # check_path=False 允许开发环境使用未发布的页面路径
        qr_data = await get_unlimited_qrcode(
            scene=short_code,
            page=request.page,
            width=width,
            check_path=False  # 不检查页面是否存在（开发环境友好）
        )

        # 转换为 base64
        img_base64 = base64.b64encode(qr_data).decode('utf-8')

        return success_response(
            data={
                "base64": f"data:image/png;base64,{img_base64}",
                "short_code": short_code,
                "width": width,
                "page": mapping.page,
                "params": mapping.params,
                "type": "wxa"  # 标识为小程序码
            },
            message="生成小程序码成功"
        )
    except Exception as e:
        # 微信API失败（开发环境页面不存在），降级为普通二维码
        logger.warning(f"WeChat QR code API failed, falling back to regular QR code: {e}")
        import io

        import qrcode

        try:
            # 生成包含短码查询URL的普通二维码
            # 扫码后可跳转到H5页面或显示提示
            qr_url = f"https://yourdomain.com/qrcode/{short_code}"

            # 创建 QR Code 实例
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=2,
            )
            qr.add_data(qr_url)
            qr.make(fit=True)

            # 生成图片
            img = qr.make_image(fill_color="#333333", back_color="#FFFFFF")
            img = img.resize((width, width))

            # 转换为 base64
            img_io = io.BytesIO()
            img.save(img_io, format='PNG')
            img_bytes = img_io.getvalue()
            img_base64 = base64.b64encode(img_bytes).decode('utf-8')

            return success_response(
                data={
                    "base64": f"data:image/png;base64,{img_base64}",
                    "short_code": short_code,
                    "width": width,
                    "page": mapping.page,
                    "params": mapping.params,
                    "type": "fallback"  # 标识为降级二维码
                },
                message="生成二维码成功（开发环境使用普通二维码）"
            )
        except Exception as fallback_error:
            logger.error(f"Failed to generate fallback QR code: {fallback_error}")
            raise Exception(f"Failed to generate QR code: {str(e)}")

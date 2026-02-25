"""
二维码参数映射表
用于将复杂参数映射到简短的小程序码 scene
"""
from app.models.base import Base
from sqlalchemy import JSON, Column, DateTime, Integer, String
from sqlalchemy.orm import relationship


class QRCodeMapping(Base):
    """二维码参数映射表"""
    __tablename__ = "qrcode_mappings"

    id = Column(String(36), primary_key=True, comment="主键ID")
    short_code = Column(String(16), unique=True, nullable=False, index=True, comment="唯一短码（6-8位）")

    # 小程序页面信息
    page = Column(String(200), nullable=False, comment="小程序页面路径")
    params = Column(JSON, nullable=False, comment="自定义参数（JSON格式）")

    # 元数据
    created_at = Column(DateTime, nullable=False, comment="创建时间")
    expires_at = Column(DateTime, nullable=True, comment="过期时间（可选）")
    scan_count = Column(Integer, default=0, nullable=False, comment="扫描次数")

    def __repr__(self):
        return f"<QRCodeMapping(short_code={self.short_code}, page={self.page})>"

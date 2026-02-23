"""add multiple images to point products

Revision ID: 4_7_003
Revises: 4_7_002
Create Date: 2026-02-23

"""
from alembic import op
import sqlalchemy as sa
import json


# revision identifiers, used by Alembic.
revision = '4_7_003'
down_revision = '4_7_002'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 添加新字段 image_urls
    op.add_column('point_products',
                  sa.Column('image_urls', sa.Text(), nullable=True, comment='商品图片URLs (JSON数组)'))

    # 2. 迁移现有数据：将 image_url 复制到 image_urls (作为单元素数组)
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id, image_url FROM point_products WHERE image_url IS NOT NULL"))
    for row in result:
        product_id = row[0]
        old_url = row[1]
        if old_url:
            urls_array = json.dumps([old_url])
            connection.execute(
                sa.text("UPDATE point_products SET image_urls = :urls WHERE id = :id"),
                {"urls": urls_array, "id": product_id}
            )

    # 3. 删除旧字段 image_url
    op.drop_column('point_products', 'image_url')


def downgrade():
    # 回滚：恢复 image_url 字段
    op.add_column('point_products',
                  sa.Column('image_url', sa.String(500), nullable=True, comment='商品图片URL'))

    # 从 image_urls 迁移回 image_url (取第一个图片)
    connection = op.get_bind()
    result = connection.execute(sa.text("SELECT id, image_urls FROM point_products WHERE image_urls IS NOT NULL"))
    for row in result:
        product_id = row[0]
        urls_json = row[1]
        if urls_json:
            try:
                urls = json.loads(urls_json)
                if urls and len(urls) > 0:
                    first_url = urls[0]
                    connection.execute(
                        sa.text("UPDATE point_products SET image_url = :url WHERE id = :id"),
                        {"url": first_url, "id": product_id}
                    )
            except:
                pass

    # 删除 image_urls 字段
    op.drop_column('point_products', 'image_urls')

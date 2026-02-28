"""add mixed payment support

Revision ID: 4_7_005
Revises: 00e1df65fcaf
Create Date: 2026-02-28

"""
import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision = '4_7_005'
down_revision = '00e1df65fcaf'
branch_labels = None
depends_on = None


def upgrade():
    # 1. 修改 point_products 表 - 添加支付模式和价格字段
    op.add_column('point_products',
                  sa.Column('payment_mode', sa.String(20),
                           server_default='points_only', nullable=False,
                           comment='支付模式: points_only=纯积分, cash_only=纯现金, mixed=混合支付'))
    op.add_column('point_products',
                  sa.Column('cash_price', sa.Integer(), nullable=True,
                           comment='现金价格（分）- 0表示免费，null表示不适用'))
    op.add_column('point_products',
                  sa.Column('mixed_points_cost', sa.Integer(), nullable=True,
                           comment='混合支付时的积分价格'))
    op.add_column('point_products',
                  sa.Column('mixed_cash_price', sa.Integer(), nullable=True,
                           comment='混合支付时的现金价格（分）'))

    # 2. 修改 point_product_skus 表 - 添加SKU价格字段
    op.add_column('point_product_skus',
                  sa.Column('cash_price', sa.Integer(), nullable=True,
                           comment='现金价格（分）- 覆盖商品默认'))
    op.add_column('point_product_skus',
                  sa.Column('mixed_points_cost', sa.Integer(), nullable=True,
                           comment='混合支付时的积分价格'))
    op.add_column('point_product_skus',
                  sa.Column('mixed_cash_price', sa.Integer(), nullable=True,
                           comment='混合支付时的现金价格（分）'))

    # 3. 修改 point_orders 表 - 添加支付状态字段
    op.add_column('point_orders',
                  sa.Column('payment_mode', sa.String(20), nullable=False,
                           server_default='points_only',
                           comment='支付模式: points_only, cash_only, mixed'))
    op.add_column('point_orders',
                  sa.Column('points_deducted', sa.Boolean(), nullable=False,
                           server_default='false',
                           comment='积分是否已扣除'))
    op.add_column('point_orders',
                  sa.Column('cash_amount', sa.Integer(), nullable=True,
                           comment='现金金额（分）- 0表示免费，null表示不适用'))
    op.add_column('point_orders',
                  sa.Column('payment_status',
                           sa.Enum('unpaid', 'paying', 'paid', 'refunded', 'failed',
                                  name='point_order_payment_status'),
                           nullable=False, server_default='unpaid',
                           comment='支付状态'))
    op.add_column('point_orders',
                  sa.Column('payment_method', sa.String(20), nullable=True,
                           comment='支付方式: wechat'))
    op.add_column('point_orders',
                  sa.Column('transaction_id', sa.String(100), nullable=True,
                           comment='微信支付交易ID'))
    op.add_column('point_orders',
                  sa.Column('refund_status', sa.String(20), nullable=True,
                           comment='退款状态: pending, processing, completed, failed'))
    op.add_column('point_orders',
                  sa.Column('refund_amount', sa.Integer(), nullable=True,
                           comment='退款金额（分）'))
    op.add_column('point_orders',
                  sa.Column('refund_transaction_id', sa.String(100), nullable=True,
                           comment='退款交易ID'))
    op.add_column('point_orders',
                  sa.Column('refunded_at', sa.DateTime(), nullable=True,
                           comment='退款时间'))

    # 添加索引
    op.create_index('ix_point_orders_payment_status', 'point_orders', ['payment_status'])

    # 4. 创建 point_payments 支付流水表
    op.create_table(
        'point_payments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('order_id', sa.String(36), sa.ForeignKey('point_orders.id'),
                 nullable=False, index=True, comment='订单ID'),
        sa.Column('user_id', sa.String(36), sa.ForeignKey('users.id'),
                 nullable=False, index=True, comment='用户ID'),
        sa.Column('out_trade_no', sa.String(64), unique=True, nullable=False,
                 index=True, comment='商户订单号'),
        sa.Column('transaction_id', sa.String(100), nullable=True,
                 index=True, comment='第三方交易ID（微信）'),
        sa.Column('total_amount', sa.Integer(), nullable=False, comment='支付总金额（分）'),
        sa.Column('cash_amount', sa.Integer(), nullable=False, comment='现金支付金额（分）'),
        sa.Column('points_amount', sa.Integer(), nullable=False,
                 server_default='0', comment='积分支付金额'),
        sa.Column('status',
                 sa.Enum('created', 'paying', 'success', 'failed', 'closed', 'refunded',
                        name='point_payment_status'),
                 nullable=False, server_default='created', comment='支付状态'),
        sa.Column('payment_method', sa.String(20), nullable=False, comment='支付方式: wechat'),
        sa.Column('prepay_id', sa.String(64), nullable=True, comment='预支付交易会话标识'),
        sa.Column('qr_code_url', sa.String(500), nullable=True, comment='支付二维码URL'),
        sa.Column('paid_at', sa.DateTime(), nullable=True, comment='支付成功时间'),
        sa.Column('expired_at', sa.DateTime(), nullable=True, comment='支付过期时间'),
        sa.Column('closed_at', sa.DateTime(), nullable=True, comment='支付关闭时间'),
        sa.Column('fail_code', sa.String(50), nullable=True, comment='失败错误码'),
        sa.Column('fail_message', sa.String(255), nullable=True, comment='失败错误信息'),
        sa.Column('request_snapshot', sa.Text(), nullable=True, comment='支付请求快照（JSON）'),
        sa.Column('response_snapshot', sa.Text(), nullable=True, comment='支付响应快照（JSON）'),
        sa.Column('idempotency_key', sa.String(64), nullable=True,
                 index=True, comment='幂等性键'),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                 server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False,
                 server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # 5. 创建 point_payment_notifies 支付回调表
    op.create_table(
        'point_payment_notifies',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('payment_id', sa.String(36), sa.ForeignKey('point_payments.id'),
                 nullable=True, index=True, comment='支付ID'),
        sa.Column('transaction_id', sa.String(100), nullable=True,
                 index=True, comment='第三方交易ID'),
        sa.Column('out_trade_no', sa.String(64), nullable=True,
                 index=True, comment='商户订单号'),
        sa.Column('notify_type', sa.String(20), nullable=False,
                 comment='回调类型: payment, refund, close'),
        sa.Column('raw_data', sa.Text(), nullable=False, comment='原始回调数据'),
        sa.Column('parsed_data', sa.Text(), nullable=True, comment='解析后的数据（JSON）'),
        sa.Column('process_status',
                 sa.Enum('pending', 'processing', 'success', 'failed', name='notify_process_status'),
                 nullable=False, server_default='pending', comment='处理状态'),
        sa.Column('process_message', sa.String(255), nullable=True, comment='处理信息'),
        sa.Column('process_attempts', sa.Integer(), nullable=False,
                 server_default='0', comment='处理尝试次数'),
        sa.Column('notified_at', sa.DateTime(), nullable=False, comment='回调通知时间'),
        sa.Column('processed_at', sa.DateTime(), nullable=True, comment='处理完成时间'),
        sa.Column('created_at', sa.DateTime(), nullable=False,
                 server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # 6. 数据迁移：现有订单设置默认值
    # 纯积分模式的订单，payment_status 应该是 paid，points_deducted 应该是 true
    op.execute("""
        UPDATE point_orders
        SET payment_mode = 'points_only',
            payment_status = 'paid',
            points_deducted = true,
            cash_amount = NULL
        WHERE payment_mode IS NULL OR payment_mode = 'points_only'
    """)


def downgrade():
    # 删除 point_payment_notifies 表
    op.drop_table('point_payment_notifies')

    # 删除 point_payments 表
    op.drop_table('point_payments')

    # 删除 point_orders 表新增字段
    op.drop_index('ix_point_orders_payment_status', 'point_orders')
    op.drop_column('point_orders', 'refunded_at')
    op.drop_column('point_orders', 'refund_transaction_id')
    op.drop_column('point_orders', 'refund_amount')
    op.drop_column('point_orders', 'refund_status')
    op.drop_column('point_orders', 'transaction_id')
    op.drop_column('point_orders', 'payment_method')
    op.drop_column('point_orders', 'payment_status')
    op.drop_column('point_orders', 'cash_amount')
    op.drop_column('point_orders', 'points_deducted')
    op.drop_column('point_orders', 'payment_mode')

    # 删除 point_product_skus 表新增字段
    op.drop_column('point_product_skus', 'mixed_cash_price')
    op.drop_column('point_product_skus', 'mixed_points_cost')
    op.drop_column('point_product_skus', 'cash_price')

    # 删除 point_products 表新增字段
    op.drop_column('point_products', 'mixed_cash_price')
    op.drop_column('point_products', 'mixed_points_cost')
    op.drop_column('point_products', 'cash_price')
    op.drop_column('point_products', 'payment_mode')

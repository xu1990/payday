from fastapi import APIRouter

from .auth import router as auth_router
from .user import router as user_router
from .payday import router as payday_router
from .salary import router as salary_router
from .post import router as post_router
from .comment import router as comment_router
from .like import router as like_router
from .follow import router as follow_router, follows_router as follows_collection_router
from .notification import router as notification_router
from .statistics import router as statistics_router
from .admin import router as admin_router
from .admin_topic import router as admin_topic_router
from .topic import router as topic_router
from .recommendation import router as recommendation_router
from .admin_config import router as admin_config_router
from .payment import router as payment_router
from .cache import router as cache_router
from .membership import router as membership_router
from .storage import router as storage_router
from .theme import router as theme_router
from .checkin import router as checkin_router
from .share import router as share_router
from .config import router as config_router
from .feedback import router as feedback_router
from .salary_usage import router as salary_usage_router
from .first_salary_usage import router as first_salary_usage_router
from .savings_goal import router as savings_goal_router
from .ability_points import router as ability_points_router
from .expense import router as expense_router
from .qrcode import router as qrcode_router
from .invitation import router as invitation_router
from .point_shop import router as point_shop_router
from .work_record import router as work_record_router
from .cart import router as cart_router
from .orders import router as orders_router
from .shipping import router as shipping_router
from .point_categories import router as point_categories_router
from .couriers import router as couriers_router

api_router = APIRouter(prefix="/api/v1", tags=["v1"])

api_router.include_router(auth_router)
api_router.include_router(user_router)
api_router.include_router(payday_router)
api_router.include_router(salary_router)
api_router.include_router(post_router)
api_router.include_router(comment_router)
api_router.include_router(like_router)
api_router.include_router(follow_router)
api_router.include_router(follows_collection_router)
api_router.include_router(notification_router)
api_router.include_router(statistics_router)
api_router.include_router(admin_router)
api_router.include_router(admin_topic_router)
api_router.include_router(topic_router)
api_router.include_router(recommendation_router)
api_router.include_router(admin_config_router)
api_router.include_router(payment_router)
api_router.include_router(cache_router)
api_router.include_router(membership_router)
api_router.include_router(storage_router)
api_router.include_router(theme_router)
api_router.include_router(checkin_router)
api_router.include_router(share_router)
api_router.include_router(config_router)
api_router.include_router(feedback_router)
api_router.include_router(salary_usage_router)
api_router.include_router(first_salary_usage_router)
api_router.include_router(savings_goal_router)
api_router.include_router(ability_points_router)
api_router.include_router(expense_router)
api_router.include_router(qrcode_router)
api_router.include_router(invitation_router)
api_router.include_router(point_shop_router)
api_router.include_router(work_record_router)
api_router.include_router(cart_router)
api_router.include_router(orders_router)
api_router.include_router(shipping_router)
api_router.include_router(point_categories_router)
api_router.include_router(couriers_router)


@api_router.get("/ping")
def ping():
    return {"pong": True}

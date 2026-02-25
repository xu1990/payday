"""
工作记录 API 集成测试 - 牛马日志 Module
"""
from datetime import datetime

import pytest
from app.models.user import User
from app.models.work_record import WorkRecord
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
class TestWorkRecordAPI:
    """测试工作记录API"""

    async def test_create_work_log(self, async_client, test_user: User, user_headers: dict):
        """测试创建工作记录"""
        work_data = {
            "clock_in_time": datetime.utcnow().isoformat(),
            "work_type": "regular",
            "content": "今天工作很顺利",
            "location": "办公室",
            "company_name": "测试公司",
            "mood": "happy",
            "tags": [" productive", " learning"],
            "images": []
        }

        response = await async_client.post(
            "/api/v1/work-logs",
            headers=user_headers,
            json=work_data
        )

        assert response.status_code == 200
        result = response.json()
        assert result["code"] == "SUCCESS"
        data = result["details"]
        assert data["content"] == "今天工作很顺利"
        assert data["work_type"] == "regular"
        assert "id" in data
        assert "post_id" in data

    async def test_create_work_log_without_auth(self, async_client):
        """测试未认证时创建工作记录"""
        work_data = {
            "clock_in_time": datetime.utcnow().isoformat(),
            "work_type": "regular",
            "content": "测试内容"
        }

        response = await async_client.post(
            "/api/v1/work-logs",
            json=work_data
        )

        assert response.status_code == 401

    async def test_list_work_logs(
        self,
        async_client,
        db_session: AsyncSession,
        test_user: User,
        user_headers: dict
    ):
        """测试获取工作记录列表"""
        # Create a work record directly in DB for testing
        from app.schemas.work_record import WorkRecordCreate
        from app.services.work_record_service import WorkRecordService

        service = WorkRecordService(db_session)
        work_data = WorkRecordCreate(
            clock_in_time=datetime.utcnow(),
            work_type="overtime",
            content="加班工作"
        )
        await service.create_work_record(test_user.id, work_data)

        # List work logs
        response = await async_client.get(
            "/api/v1/work-logs",
            headers=user_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["code"] == "SUCCESS"
        data = result["details"]
        assert "items" in data
        assert len(data["items"]) >= 1

    async def test_get_work_log_detail(
        self,
        async_client,
        db_session: AsyncSession,
        test_user: User,
        user_headers: dict
    ):
        """测试获取工作记录详情"""
        # Create a work record
        from app.schemas.work_record import WorkRecordCreate
        from app.services.work_record_service import WorkRecordService

        service = WorkRecordService(db_session)
        work_data = WorkRecordCreate(
            clock_in_time=datetime.utcnow(),
            work_type="weekend",
            content="周末加班"
        )
        work_record = await service.create_work_record(test_user.id, work_data)

        # Get detail
        response = await async_client.get(
            f"/api/v1/work-logs/{work_record.id}",
            headers=user_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["code"] == "SUCCESS"
        data = result["details"]
        assert data["id"] == work_record.id
        assert data["content"] == "周末加班"

    async def test_clock_out(
        self,
        async_client,
        db_session: AsyncSession,
        test_user: User,
        user_headers: dict
    ):
        """测试打卡下班"""
        # Create a work record without clock out
        from app.schemas.work_record import WorkRecordCreate
        from app.services.work_record_service import WorkRecordService

        service = WorkRecordService(db_session)
        work_data = WorkRecordCreate(
            clock_in_time=datetime.utcnow(),
            work_type="regular",
            content="开始工作"
        )
        work_record = await service.create_work_record(test_user.id, work_data)

        # Clock out
        clock_out_time = datetime.utcnow().isoformat()
        response = await async_client.put(
            f"/api/v1/work-logs/{work_record.id}/clock-out",
            headers=user_headers,
            json={"clock_out_time": clock_out_time}
        )

        assert response.status_code == 200
        result = response.json()
        assert result["code"] == "SUCCESS"
        data = result["details"]
        assert data["clock_out_time"] is not None
        assert data["work_duration_minutes"] is not None

    async def test_clock_out_already_clocked_out(
        self,
        async_client,
        db_session: AsyncSession,
        test_user: User,
        user_headers: dict
    ):
        """测试重复打卡下班应该失败"""
        # Create a work record with clock out time
        from app.schemas.work_record import WorkRecordCreate
        from app.services.work_record_service import WorkRecordService

        service = WorkRecordService(db_session)
        clock_in = datetime.utcnow()
        work_data = WorkRecordCreate(
            clock_in_time=clock_in,
            work_type="regular",
            content="完成工作",
            clock_out_time=datetime.utcnow()
        )
        work_record = await service.create_work_record(test_user.id, work_data)

        # Try to clock out again
        response = await async_client.put(
            f"/api/v1/work-logs/{work_record.id}/clock-out",
            headers=user_headers,
            json={"clock_out_time": datetime.utcnow().isoformat()}
        )

        # Should fail with validation error
        assert response.status_code in [400, 422]

    async def test_create_work_log_invalid_type(
        self,
        async_client,
        test_user: User,
        user_headers: dict
    ):
        """测试创建工作记录时使用无效的工作类型"""
        work_data = {
            "clock_in_time": datetime.utcnow().isoformat(),
            "work_type": "invalid_type",
            "content": "测试内容"
        }

        response = await async_client.post(
            "/api/v1/work-logs",
            headers=user_headers,
            json=work_data
        )

        # Should fail with validation error
        assert response.status_code == 422

    async def test_get_nonexistent_work_log(
        self,
        async_client,
        test_user: User,
        user_headers: dict
    ):
        """测试获取不存在的工作记录"""
        response = await async_client.get(
            "/api/v1/work-logs/nonexistent-id",
            headers=user_headers
        )

        assert response.status_code == 404

    async def test_get_work_feed(
        self,
        async_client,
        db_session: AsyncSession,
        test_user: User,
        user_headers: dict
    ):
        """测试获取工作动态feed"""
        from app.schemas.work_record import WorkRecordCreate
        from app.services.work_record_service import WorkRecordService

        # Create multiple work records
        service = WorkRecordService(db_session)
        for i in range(3):
            work_data = WorkRecordCreate(
                clock_in_time=datetime.utcnow(),
                work_type="regular",
                content=f"工作内容 {i+1}"
            )
            await service.create_work_record(test_user.id, work_data)

        # Get work feed
        response = await async_client.get(
            "/api/v1/work-logs/feed",
            headers=user_headers,
            params={"page": 1, "page_size": 10}
        )

        assert response.status_code == 200
        result = response.json()
        assert result["code"] == "SUCCESS"
        data = result["details"]
        assert "items" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["items"]) >= 3

    async def test_get_work_feed_pagination(
        self,
        async_client,
        test_user: User,
        user_headers: dict
    ):
        """测试工作动态feed分页"""
        response = await async_client.get(
            "/api/v1/work-logs/feed",
            headers=user_headers,
            params={"page": 2, "page_size": 5}
        )

        assert response.status_code == 200
        result = response.json()
        assert result["code"] == "SUCCESS"
        data = result["details"]
        assert data["page"] == 2
        assert data["page_size"] == 5

    async def test_get_work_statistics(
        self,
        async_client,
        db_session: AsyncSession,
        test_user: User,
        user_headers: dict
    ):
        """测试获取工作统计数据"""
        from app.schemas.work_record import WorkRecordCreate
        from app.services.work_record_service import WorkRecordService

        # Create work records with overtime
        service = WorkRecordService(db_session)
        clock_in = datetime.utcnow()
        clock_out = datetime.utcnow().replace(hour=20, minute=0)  # 8 hours later

        work_data1 = WorkRecordCreate(
            clock_in_time=clock_in,
            clock_out_time=clock_out,
            work_type="overtime",
            content="加班工作",
            mood="happy"
        )
        await service.create_work_record(test_user.id, work_data1)

        work_data2 = WorkRecordCreate(
            clock_in_time=clock_in,
            clock_out_time=clock_out,
            work_type="regular",
            content="正常工作",
            mood="neutral"
        )
        await service.create_work_record(test_user.id, work_data2)

        # Get statistics for current month
        now = datetime.utcnow()
        response = await async_client.get(
            "/api/v1/work-logs/statistics",
            headers=user_headers,
            params={"year": now.year, "month": now.month}
        )

        assert response.status_code == 200
        result = response.json()
        assert result["code"] == "SUCCESS"
        data = result["details"]
        assert "total_overtime_hours" in data
        assert "work_days" in data
        assert "recent_mood" in data
        assert data["total_overtime_hours"] > 0
        assert data["work_days"] >= 2
        assert data["recent_mood"] in ["happy", "neutral", "sad", None]

    async def test_get_work_statistics_no_data(
        self,
        async_client,
        test_user: User,
        user_headers: dict
    ):
        """测试获取工作统计数据（无数据）"""
        now = datetime.utcnow()
        response = await async_client.get(
            "/api/v1/work-logs/statistics",
            headers=user_headers,
            params={"year": now.year, "month": now.month}
        )

        assert response.status_code == 200
        result = response.json()
        assert result["code"] == "SUCCESS"
        data = result["details"]
        assert data["total_overtime_hours"] == 0
        assert data["work_days"] == 0
        assert data["recent_mood"] is None

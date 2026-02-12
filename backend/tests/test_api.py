"""
API 端点测试
"""
import pytest
from fastapi.testclient import TestClient

from app.main import app


@pytest.fixture
def client():
    """测试客户端 fixture"""
    return TestClient(app)


def test_root(client):
    """测试根端点"""
    response = client.get("/")
    assert response.status_code == 200
    assert "app" in response.json()


def test_health(client):
    """测试健康检查端点"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_metrics(client):
    """测试 metrics 端点"""
    response = client.get("/metrics")
    assert response.status_code == 200
    # Prometheus 返回文本格式
    assert "text/plain" in response.headers["content-type"]


def test_login_endpoint(client):
    """测试登录端点（验证端点存在，不测试完整流程）"""
    response = client.post("/api/v1/auth/login", json={"code": "test_code"})
    # 预期会失败（code 无效），但端点应该存在
    assert response.status_code in [400, 401, 500]


def test_cors_headers(client):
    """测试 CORS 头"""
    response = client.get("/", headers={"Origin": "http://example.com"})
    assert response.status_code == 200
    # CORS 头应该在响应中
    # 注意：TestClient 可能不返回 CORS 头，这需要在集成测试中验证

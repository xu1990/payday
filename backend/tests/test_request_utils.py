"""
请求工具函数测试
"""
import pytest
from fastapi import Request, HTTPException
from app.utils.request import get_client_ip


class TestGetClientIp:
    """测试 IP 地址提取功能"""

    def test_extract_from_x_forwarded_for(self):
        """测试从 X-Forwarded-For 头提取 IP"""
        # Mock request object
        class MockRequest:
            def __init__(self, headers):
                self.headers = headers
                self.client = None

        request = MockRequest({"X-Forwarded-For": "203.0.113.1, 10.0.0.1"})
        result = get_client_ip(request)
        assert result == "203.0.113.1"

    def test_takes_first_ip_from_forwarded_chain(self):
        """测试从 IP 链中取第一个 IP"""
        class MockRequest:
            def __init__(self, headers):
                self.headers = headers
                self.client = None

        request = MockRequest({"X-Forwarded-For": "203.0.113.1, 10.0.0.1, 192.168.1.1"})
        result = get_client_ip(request)
        assert result == "203.0.113.1"

    def test_extract_from_x_real_ip(self):
        """测试从 X-Real-IP 头提取 IP"""
        class MockRequest:
            def __init__(self, headers):
                self.headers = headers
                self.client = None

        request = MockRequest({"X-Real-IP": "198.51.100.1"})
        result = get_client_ip(request)
        assert result == "198.51.100.1"

    def test_x_real_ip_priority_over_forwarded(self):
        """测试 X-Real-IP 优先级高于 X-Forwarded-For"""
        class MockRequest:
            def __init__(self, headers):
                self.headers = headers
                self.client = None

        request = MockRequest({
            "X-Forwarded-For": "203.0.113.1",
            "X-Real-IP": "198.51.100.1"
        })
        result = get_client_ip(request)
        # X-Real-IP 优先级更高
        assert result == "198.51.100.1"

    def test_extract_from_client_host(self):
        """测试从 client.host 提取 IP"""
        class MockClient:
            def __init__(self, host):
                self.host = host

        class MockRequest:
            def __init__(self, client):
                self.headers = {}
                self.client = client

        client = MockClient("192.168.1.100")
        request = MockRequest(client)
        result = get_client_ip(request)
        assert result == "192.168.1.100"

    def test_strips_whitespace_from_ip(self):
        """测试去除 IP 地址中的空格"""
        class MockRequest:
            def __init__(self, headers):
                self.headers = headers
                self.client = None

        request = MockRequest({"X-Real-IP": "  198.51.100.1  "})
        result = get_client_ip(request)
        assert result == "198.51.100.1"

    def test_returns_loopback_when_no_headers(self):
        """测试无头信息时返回回环地址"""
        class MockRequest:
            def __init__(self, client):
                self.headers = {}
                self.client = client

        class MockClient:
            host = None

        request = MockRequest(MockClient())
        result = get_client_ip(request)
        assert result == "127.0.0.1"

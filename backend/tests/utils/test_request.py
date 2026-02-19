"""测试HTTP请求工具"""
import pytest
from fastapi import Request
from starlette.datastructures import Headers
from unittest.mock import Mock

from app.utils.request import get_client_ip


class TestGetClientIP:
    """测试获取客户端IP"""

    def test_x_forwarded_for_header(self):
        """测试从X-Forwarded-For获取IP"""
        # 创建mock request
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "x-forwarded-for": "203.0.113.195, 70.41.3.18, 150.172.238.178"
        })

        ip = get_client_ip(mock_request)
        assert ip == "203.0.113.195"

    def test_x_real_ip_header(self):
        """测试从X-Real-IP获取IP"""
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "x-real-ip": "198.51.100.1"
        })
        mock_request.client = None

        ip = get_client_ip(mock_request)
        assert ip == "198.51.100.1"

    def test_client_host(self):
        """测试从client.host获取IP"""
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({})
        mock_client = Mock()
        mock_client.host = "192.0.2.1"
        mock_request.client = mock_client

        ip = get_client_ip(mock_request)
        assert ip == "192.0.2.1"

    def test_no_ip_available(self):
        """测试没有IP时返回默认值"""
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({})
        mock_request.client = None

        ip = get_client_ip(mock_request)
        assert ip == "127.0.0.1"

    def test_forwarded_for_with_comma(self):
        """测试X-Forwarded-For包含多个IP时取第一个"""
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "x-forwarded-for": "  10.0.0.1  ,  10.0.0.2  "
        })

        ip = get_client_ip(mock_request)
        assert ip == "10.0.0.1"

    def test_x_real_ip_priority_lower_than_forwarded(self):
        """测试X-Forwarded-For优先级高于X-Real-IP"""
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "x-forwarded-for": "1.2.3.4",
            "x-real-ip": "5.6.7.8"
        })

        ip = get_client_ip(mock_request)
        assert ip == "1.2.3.4"

    def test_x_real_ip_used_when_no_forwarded(self):
        """测试没有X-Forwarded-For时使用X-Real-IP"""
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "x-real-ip": "9.10.11.12"
        })
        mock_request.client = None

        ip = get_client_ip(mock_request)
        assert ip == "9.10.11.12"

    def test_ipv6_address(self):
        """测试IPv6地址"""
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "x-forwarded-for": "2001:0db8:85a3::8a2e:0370:7334"
        })

        ip = get_client_ip(mock_request)
        assert ip == "2001:0db8:85a3::8a2e:0370:7334"

    def test_localhost_ipv4(self):
        """测试本地IPv4地址"""
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "x-forwarded-for": "127.0.0.1"
        })

        ip = get_client_ip(mock_request)
        assert ip == "127.0.0.1"

    def test_private_ip_range(self):
        """测试私有IP地址范围"""
        mock_request = Mock(spec=Request)
        mock_request.headers = Headers({
            "x-forwarded-for": "10.0.0.1"  # 私有IP
        })

        ip = get_client_ip(mock_request)
        assert ip == "10.0.0.1"

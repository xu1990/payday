"""
API tests configuration - Mock problematic external dependencies

IMPORTANT: This file runs before any test imports to set up mocks
"""
import sys
from unittest.mock import MagicMock, Mock
import pytest

# Setup mocks immediately when this file is loaded (before any test imports)
# Mock Celery
celery_mock = MagicMock()
celery_mock.shared_task = lambda **kwargs: lambda f: f
sys.modules['celery'] = celery_mock

# Mock tencentcloud with simple module stubs that support attribute access
class ModuleStub:
    """Simple module stub that returns itself for any attribute access"""
    def __init__(self, name=''):
        self.__name__ = name or 'tencentcloud'

    def __getattr__(self, name):
        # Return a new stub for any attribute access
        return ModuleStub(f'{self.__name__}.{name}')

    def __getitem__(self, name):
        return ModuleStub(f'{self.__name__}.{name}')

sys.modules['tencentcloud'] = ModuleStub()
# Pre-register commonly used submodules
for submodule in ['common', 'common.credential', 'common.exception', 'common.exception.tencent_cloud_sdk_exception',
                  'tms', 'tms.v20200713', 'tms.v20200713.models',
                  'ims', 'ims.v20201229', 'ims.v20201229.models',
                  'ocr', 'ocr.v20181119', 'ocr.v20181119.models']:
    sys.modules[f'tencentcloud.{submodule}'] = ModuleStub(f'tencentcloud.{submodule}')

# Mock OSS
sys.modules['oss2'] = MagicMock()

# Mock the tencent_yu service to prevent initialization issues
# This is needed because it tries to access settings attributes that don't exist
tencent_yu_mock = MagicMock()
sys.modules['app.utils.tencent_yu'] = tencent_yu_mock


@pytest.fixture
def client():
    """测试客户端 fixture - FastAPI TestClient"""
    from fastapi.testclient import TestClient
    from app.main import app
    return TestClient(app)

#!/bin/bash
# 运行所有测试的便捷脚本

set -e

echo "======================================"
echo "PayDay 三端自动化测试"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试结果
PASSED=0
FAILED=0

# Backend测试
echo -e "${YELLOW}1. Backend Tests (FastAPI)...${NC}"
cd backend
if python3 -m pytest --no-cov -q 2>&1 | grep -q "passed"; then
    echo -e "${GREEN}✓ Backend tests passed${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ Backend tests failed${NC}"
    ((FAILED++))
fi
cd ..

echo ""

# Miniapp测试
echo -e "${YELLOW}2. Miniapp Tests (WeChat Mini-program)...${NC}"
cd miniapp
if npm run test:run 2>&1 | grep -q "passed"; then
    echo -e "${GREEN}✓ Miniapp tests passed${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ Miniapp tests failed${NC}"
    ((FAILED++))
fi
cd ..

echo ""

# Admin-web测试
echo -e "${YELLOW}3. Admin Web Tests (Vue3)...${NC}"
cd admin-web
if npm run test:run 2>&1 | grep -q "passed"; then
    echo -e "${GREEN}✓ Admin web tests passed${NC}"
    ((PASSED++))
else
    echo -e "${RED}✗ Admin web tests failed${NC}"
    ((FAILED++))
fi
cd ..

echo ""
echo "======================================"
echo "测试结果汇总"
echo "======================================"
echo -e "通过: ${GREEN}$PASSED${NC}/3"
echo -e "失败: ${RED}$FAILED${NC}/3"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}所有测试通过！${NC}"
    exit 0
else
    echo -e "${RED}有测试失败，请检查日志${NC}"
    exit 1
fi

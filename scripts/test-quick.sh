#!/bin/bash
# 三端快速测试脚本 - 只运行关键测试

set -e

echo "======================================"
echo "PayDay 三端快速测试"
echo "======================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# 测试结果
PASSED=0
FAILED=0
RESULTS=()

# Backend 快速测试（关键模块）
echo -e "${YELLOW}1. Backend 关键测试...${NC}"
cd backend
if python3 -m pytest tests/test_sanitize.py tests/test_pagination.py tests/test_exceptions.py tests/test_utils.py --tb=no --no-cov -q 2>&1 | tail -1 | grep -q "passed"; then
    echo -e "${GREEN}✓ Backend 关键测试通过${NC}"
    ((PASSED++))
    RESULTS+=("Backend: ✅ 通过")
else
    echo -e "${RED}✗ Backend 关键测试失败${NC}"
    ((FAILED++))
    RESULTS+=("Backend: ❌ 失败")
fi
cd ..

echo ""

# Miniapp 测试
echo -e "${YELLOW}2. Miniapp 测试...${NC}"
cd miniapp
if npm run test:run 2>&1 | grep -q "Test Files.*passed"; then
    echo -e "${GREEN}✓ Miniapp 测试通过${NC}"
    ((PASSED++))
    RESULTS+=("Miniapp: ✅ 通过")
else
    echo -e "${RED}✗ Miniapp 测试失败${NC}"
    ((FAILED++))
    RESULTS+=("Miniapp: ❌ 失败")
fi
cd ..

echo ""

# Admin-web 测试
echo -e "${YELLOW}3. Admin Web 测试...${NC}"
cd admin-web
if npm run test:run 2>&1 | grep -q "Test Files.*passed"; then
    echo -e "${GREEN}✓ Admin Web 测试通过${NC}"
    ((PASSED++))
    RESULTS+=("Admin Web: ✅ 通过")
else
    echo -e "${RED}✗ Admin Web 测试失败${NC}"
    ((FAILED++))
    RESULTS+=("Admin Web: ❌ 失败")
fi
cd ..

echo ""
echo "======================================"
echo "测试结果汇总"
echo "======================================"
for result in "${RESULTS[@]}"; do
    echo "  $result"
done
echo ""
echo -e "通过: ${GREEN}$PASSED${NC}/3"
echo -e "失败: ${RED}$FAILED${NC}/3"
echo ""

if [ $FAILED -eq 0 ]; then
    echo -e "${GREEN}✅ 所有测试通过！${NC}"
    echo ""
    echo "提示: 运行完整测试请使用 ./scripts/test-all.sh"
    exit 0
else
    echo -e "${RED}❌ 有测试失败，请检查日志${NC}"
    exit 1
fi

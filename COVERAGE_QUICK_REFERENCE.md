# Test Coverage - Quick Reference

**Generated**: 2026-02-12
**Total Tests**: 149 (95 passed, 54 failed)
**Overall Coverage**: 41%

## Target Module Results

| Module | Coverage | Target | Status |
|--------|----------|--------|--------|
| **Services** |||
| `auth_service.py` | 78% | >80% | ❌ 2% below |
| `payment_service.py` | 82% | >85% | ❌ 3% below |
| `salary_service.py` | 92% | >85% | ✅ **EXCEEDS** |
| **API Routes** |||
| `auth.py` | 71% | >75% | ❌ 4% below |
| `payment.py` | 20% | >75% | ❌ 55% below |
| `salary.py` | 58% | >75% | ❌ 17% below |

## Key Findings

✅ **Strengths**:
- salary_service.py: 92% (exceeds target)
- Complete schema coverage (96-100%)
- Strong utility coverage (96-100%)

❌ **Issues**:
- 37 API integration tests failing (async mocking)
- payment.py API only 20% covered (critical)
- auth.py API 71% (slightly below target)
- salary.py API 58% (below target)

## Next Steps

1. Fix async mocking in `tests/conftest.py`
2. Add 2% coverage to auth_service.py
3. Add 3% coverage to payment_service.py
4. Re-run coverage after fixes

## Reports

- **Detailed Analysis**: `backend/COVERAGE_REPORT.md`
- **HTML Report**: `backend/htmlcov/index.html`
- **Task Summary**: `TASK_7_COVERAGE_SUMMARY.md`

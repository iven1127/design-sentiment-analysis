"""测试重试机制"""
import pytest
from core.retry import retry_on_exception


class TestRetry:
    def test_retry_success(self):
        """测试最终重试成功"""
        call_count = {"value": 0}

        @retry_on_exception(ZeroDivisionError, maxtries=3, backoff=0.1)
        def failing_function():
            call_count["value"] += 1
            if call_count["value"] < 3:
                raise ZeroDivisionError("Test error")
            return "success"

        result = failing_function()
        assert result == "success"
        assert call_count["value"] == 3

    def test_retry_exhausted(self):
        """测试重试次数用尽"""
        @retry_on_exception(ValueError, maxtries=2, backoff=0.1)
        def always_fail():
            raise ValueError("Always fails")

        with pytest.raises(ValueError):
            always_fail()

    def test_no_retry_on_unexpected_exception(self):
        """测试异常类型不匹配时不重试"""
        @retry_on_exception(ValueError, maxtries=3, backoff=0.1)
        def raise_type_error():
            raise TypeError("Unexpected error")

        with pytest.raises(TypeError):
            raise_type_error()
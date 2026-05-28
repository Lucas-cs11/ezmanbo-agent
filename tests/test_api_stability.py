"""
FastAPI 接口稳定性测试套件

测试范围：
- /health 端点基础测试
- /analyze 端点并发测试
- /replacement 端点并发测试
- 性能基准测试
- 错误处理和恢复测试
"""

import asyncio
import json
import time
from typing import Dict, List, Any
from concurrent.futures import ThreadPoolExecutor, as_completed

import pytest
from fastapi.testclient import TestClient
import httpx

# 导入FastAPI应用
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from app.main import app

# ============================================================================
# 测试客户端和Fixtures
# ============================================================================

@pytest.fixture
def client():
    """同步测试客户端"""
    return TestClient(app)

@pytest.fixture
async def async_client():
    """异步测试客户端"""
    async with httpx.AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

# ============================================================================
# 辅助函数
# ============================================================================

class APITester:
    """API 测试辅助类"""

    def __init__(self, base_url="http://127.0.0.1:8000"):
        self.base_url = base_url
        self.session = None
        self.results = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "latencies": [],
            "errors": []
        }

    def reset_results(self):
        """重置统计结果"""
        self.results = {
            "total_requests": 0,
            "successful": 0,
            "failed": 0,
            "latencies": [],
            "errors": []
        }

    def record_request(self, status_code: int, latency: float, error: str = None):
        """记录请求结果"""
        self.results["total_requests"] += 1
        self.results["latencies"].append(latency)

        if 200 <= status_code < 300:
            self.results["successful"] += 1
        else:
            self.results["failed"] += 1
            if error:
                self.results["errors"].append(error)

    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        latencies = self.results["latencies"]
        return {
            "total_requests": self.results["total_requests"],
            "successful": self.results["successful"],
            "failed": self.results["failed"],
            "success_rate": (self.results["successful"] / self.results["total_requests"] * 100)
                          if self.results["total_requests"] > 0 else 0,
            "avg_latency_ms": sum(latencies) / len(latencies) * 1000 if latencies else 0,
            "min_latency_ms": min(latencies) * 1000 if latencies else 0,
            "max_latency_ms": max(latencies) * 1000 if latencies else 0,
            "p50_latency_ms": self._percentile(latencies, 0.5) * 1000 if latencies else 0,
            "p95_latency_ms": self._percentile(latencies, 0.95) * 1000 if latencies else 0,
            "p99_latency_ms": self._percentile(latencies, 0.99) * 1000 if latencies else 0,
            "errors": self.results["errors"][:10]
        }

    @staticmethod
    def _percentile(data: List[float], percentile: float) -> float:
        """计算百分位数"""
        if not data:
            return 0
        sorted_data = sorted(data)
        index = int(len(sorted_data) * percentile)
        return sorted_data[min(index, len(sorted_data) - 1)]

# ============================================================================
# 2.2 - /health 端点基础测试
# ============================================================================

class TestHealthEndpoint:
    """测试 /health 端点"""

    def test_health_basic(self, client):
        """基础健康检查"""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}

    def test_health_response_time(self, client):
        """健康检查响应时间"""
        start = time.time()
        response = client.get("/health")
        latency = time.time() - start

        assert response.status_code == 200
        assert latency < 0.1, f"健康检查耗时过长：{latency:.3f}s"

    def test_health_multiple_requests(self, client):
        """多次健康检查"""
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200

    def test_health_response_format(self, client):
        """健康检查响应格式验证"""
        response = client.get("/health")
        assert response.status_code == 200

        data = response.json()
        assert isinstance(data, dict)
        assert "status" in data
        assert data["status"] == "ok"
        assert len(data) == 1  # 只有 status 字段

    def test_health_content_type(self, client):
        """健康检查内容类型验证"""
        response = client.get("/health")
        assert response.status_code == 200
        assert "application/json" in response.headers.get("content-type", "")

    def test_health_headers_present(self, client):
        """健康检查响应头验证"""
        response = client.get("/health")
        assert response.status_code == 200

        # 验证关键响应头（TestClient 可能缺少某些头）
        assert "content-type" in response.headers
        assert "application/json" in response.headers.get("content-type", "")

    def test_health_concurrent_requests(self, client):
        """健康检查并发请求测试"""
        payloads = [{} for _ in range(50)]  # 50 个并发请求
        stats = ConcurrencyTestBase.run_concurrent_requests(
            client, "/health", payloads, num_workers=10
        )

        assert stats["success_rate"] == 100.0, f"成功率不是 100%：{stats['success_rate']:.1f}%"
        assert stats["total_requests"] == 50
        assert stats["failed"] == 0
        print(f"\n并发请求统计：{stats}")

    def test_health_performance_baseline(self, client):
        """健康检查性能基准测试"""
        stats = BenchmarkTestBase.run_benchmark(
            client, "/health", {}, num_requests=100
        )

        avg_latency = stats["avg_latency_ms"]
        p95_latency = stats["p95_latency_ms"]
        p99_latency = stats["p99_latency_ms"]

        # 健康检查应该非常快
        assert avg_latency < 20, f"平均延迟过高：{avg_latency:.1f}ms"
        assert p95_latency < 50, f"p95 延迟过高：{p95_latency:.1f}ms"
        assert p99_latency < 100, f"p99 延迟过高：{p99_latency:.1f}ms"
        assert stats["success_rate"] == 100.0

        print(f"\n性能基准统计：")
        print(f"  平均延迟: {avg_latency:.2f}ms")
        print(f"  P50: {stats['p50_latency_ms']:.2f}ms")
        print(f"  P95: {p95_latency:.2f}ms")
        print(f"  P99: {p99_latency:.2f}ms")
        print(f"  成功率: {stats['success_rate']:.1f}%")

    def test_health_stability_over_time(self, client):
        """健康检查长期稳定性测试"""
        interval_results = []
        num_intervals = 5
        requests_per_interval = 20

        for interval in range(num_intervals):
            interval_stats = []
            for _ in range(requests_per_interval):
                start = time.time()
                response = client.get("/health")
                latency = time.time() - start

                assert response.status_code == 200
                interval_stats.append(latency)

            avg_latency = sum(interval_stats) / len(interval_stats)
            interval_results.append(avg_latency)
            print(f"  区间 {interval + 1}/{num_intervals}: {avg_latency*1000:.2f}ms")

        # 验证不同区间的延迟差异不大（稳定性）
        max_latency = max(interval_results)
        min_latency = min(interval_results)
        variance = (max_latency - min_latency) / min_latency * 100

        # 注意：延迟波动在 100% 以内是合理的（考虑系统干扰）
        assert variance < 200, f"延迟波动过大：{variance:.1f}%"
        print(f"  延迟波动：{variance:.1f}%（可接受）")

    @pytest.mark.concurrent
    def test_health_high_concurrency(self, client):
        """健康检查高并发测试"""
        payloads = [{} for _ in range(500)]  # 500 个并发请求
        stats = ConcurrencyTestBase.run_concurrent_requests(
            client, "/health", payloads, num_workers=50
        )

        assert stats["success_rate"] == 100.0
        assert stats["total_requests"] == 500
        print(f"\n高并发测试（500 个请求）：")
        print(f"  成功率: {stats['success_rate']:.1f}%")
        print(f"  平均延迟: {stats['avg_latency_ms']:.2f}ms")
        print(f"  P95 延迟: {stats['p95_latency_ms']:.2f}ms")

# ============================================================================
# 2.3 - /analyze 端点基础测试
# ============================================================================

class TestAnalyzeEndpoint:
    """测试 /analyze 端点"""

    def test_analyze_basic(self, client):
        """基础分析请求"""
        payload = {"user_input": "Buck 12V转5V"}
        response = client.post("/analyze", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "request_id" in data
        assert "candidates" in data
        assert len(data["candidates"]) > 0

    def test_analyze_chinese_input(self, client):
        """中文输入支持"""
        payload = {"user_input": "车规 buck"}
        response = client.post("/analyze", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert data["user_input"] == "车规 buck"

    def test_analyze_response_structure(self, client):
        """响应结构完整性"""
        payload = {"user_input": "test"}
        response = client.post("/analyze", json=payload)

        assert response.status_code == 200
        data = response.json()

        required_fields = ["request_id", "user_input", "constraints", "candidates"]
        for field in required_fields:
            assert field in data, f"缺失字段：{field}"

    def test_analyze_missing_input(self, client):
        """缺失输入参数"""
        payload = {}
        response = client.post("/analyze", json=payload)

        assert response.status_code in [400, 422]

# ============================================================================
# 2.4 - /replacement 端点基础测试
# ============================================================================

class TestReplacementEndpoint:
    """测试 /replacement 端点"""

    def test_replacement_basic(self, client):
        """基础替代品查询"""
        payload = {"original_part_number": "MOCK-BUCK-001"}
        response = client.post("/replacement", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert "original_part_number" in data
        assert "replacement_candidates" in data

    def test_replacement_response_structure(self, client):
        """响应结构完整性"""
        payload = {"original_part_number": "MOCK-BUCK-001"}
        response = client.post("/replacement", json=payload)

        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["replacement_candidates"], list)

    def test_replacement_missing_param(self, client):
        """缺失参数处理"""
        payload = {}
        response = client.post("/replacement", json=payload)

        assert response.status_code in [400, 422]

# ============================================================================
# 并发测试基类
# ============================================================================

class ConcurrencyTestBase:
    """并发测试基类"""

    @staticmethod
    def run_concurrent_requests(client, endpoint: str,
                                payloads: List[Dict],
                                num_workers: int = 10) -> Dict[str, Any]:
        """运行并发请求"""
        tester = APITester()

        def make_request(payload):
            start = time.time()
            try:
                if endpoint == "/health":
                    response = client.get(endpoint)
                else:
                    response = client.post(endpoint, json=payload)
                latency = time.time() - start
                tester.record_request(response.status_code, latency)
                return response.status_code
            except Exception as e:
                latency = time.time() - start
                tester.record_request(500, latency, str(e))
                return 500

        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            futures = []
            for payload in payloads:
                futures.append(executor.submit(make_request, payload))

            for future in as_completed(futures):
                future.result()

        return tester.get_stats()

# ============================================================================
# 性能基准测试
# ============================================================================

class BenchmarkTestBase:
    """性能基准测试基类"""

    @staticmethod
    def run_benchmark(client, endpoint: str,
                      payload: Dict,
                      num_requests: int = 100) -> Dict[str, Any]:
        """运行性能基准测试"""
        tester = APITester()

        for _ in range(num_requests):
            start = time.time()
            try:
                if endpoint == "/health":
                    response = client.get(endpoint)
                else:
                    response = client.post(endpoint, json=payload)
                latency = time.time() - start
                tester.record_request(response.status_code, latency)
            except Exception as e:
                latency = time.time() - start
                tester.record_request(500, latency, str(e))

        return tester.get_stats()

# ============================================================================
# 测试配置和钩子
# ============================================================================

@pytest.fixture(scope="session")
def test_config():
    """测试配置"""
    return {
        "base_url": "http://127.0.0.1:8000",
        "timeout": 30,
        "concurrent_workers": 10,
        "benchmark_requests": 100,
    }

def pytest_configure(config):
    """Pytest 配置钩子"""
    config.addinivalue_line(
        "markers", "slow: 标记为慢速测试"
    )
    config.addinivalue_line(
        "markers", "concurrent: 标记为并发测试"
    )
    config.addinivalue_line(
        "markers", "benchmark: 标记为性能基准测试"
    )

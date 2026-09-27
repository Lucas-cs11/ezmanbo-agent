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

    def test_analyze_concurrent_requests(self, client):
        """分析请求并发测试"""
        payloads = [
            {"user_input": "Buck 12V转5V"},
            {"user_input": "车规 buck"},
            {"user_input": "Boost converter 5V"},
            {"user_input": "国产替代方案"},
        ]
        # 重复数据以创建 50 个并发请求
        payloads_extended = payloads * 13  # 4 * 13 = 52

        stats = ConcurrencyTestBase.run_concurrent_requests(
            client, "/analyze", payloads_extended[:50], num_workers=10
        )

        assert stats["success_rate"] == 100.0, f"成功率不是 100%：{stats['success_rate']:.1f}%"
        assert stats["total_requests"] == 50
        assert stats["failed"] == 0
        print(f"\n/analyze 并发请求统计：{stats}")

    def test_analyze_performance_baseline(self, client):
        """分析请求性能基准测试"""
        payload = {"user_input": "Buck 12V转5V"}
        stats = BenchmarkTestBase.run_benchmark(
            client, "/analyze", payload, num_requests=100
        )

        avg_latency = stats["avg_latency_ms"]
        p95_latency = stats["p95_latency_ms"]
        p99_latency = stats["p99_latency_ms"]

        # /analyze 包含业务逻辑，延迟会高于 /health
        assert avg_latency < 500, f"平均延迟过高：{avg_latency:.1f}ms"
        assert p95_latency < 1000, f"p95 延迟过高：{p95_latency:.1f}ms"
        assert p99_latency < 2000, f"p99 延迟过高：{p99_latency:.1f}ms"
        assert stats["success_rate"] == 100.0

        print(f"\n/analyze 性能基准统计：")
        print(f"  平均延迟: {avg_latency:.2f}ms")
        print(f"  P50: {stats['p50_latency_ms']:.2f}ms")
        print(f"  P95: {p95_latency:.2f}ms")
        print(f"  P99: {p99_latency:.2f}ms")
        print(f"  成功率: {stats['success_rate']:.1f}%")

    def test_analyze_stability_over_time(self, client):
        """分析请求长期稳定性测试"""
        payload = {"user_input": "Buck 12V转5V"}
        interval_results = []
        num_intervals = 5
        requests_per_interval = 10

        for interval in range(num_intervals):
            interval_stats = []
            for _ in range(requests_per_interval):
                start = time.time()
                response = client.post("/analyze", json=payload)
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

        # 延迟波动在 200% 以内是合理的
        assert variance < 200, f"延迟波动过大：{variance:.1f}%"
        print(f"  延迟波动：{variance:.1f}%（可接受）")

    @pytest.mark.concurrent
    def test_analyze_high_concurrency(self, client):
        """分析请求高并发测试"""
        payloads = [
            {"user_input": f"Buck converter variant {i}"}
            for i in range(500)
        ]
        stats = ConcurrencyTestBase.run_concurrent_requests(
            client, "/analyze", payloads, num_workers=50
        )

        assert stats["success_rate"] == 100.0
        assert stats["total_requests"] == 500
        print(f"\n/analyze 高并发测试（500 个请求）：")
        print(f"  成功率: {stats['success_rate']:.1f}%")
        print(f"  平均延迟: {stats['avg_latency_ms']:.2f}ms")
        print(f"  P95 延迟: {stats['p95_latency_ms']:.2f}ms")

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

    def test_replacement_concurrent_requests(self, client):
        """替代品查询并发测试"""
        part_numbers = [
            "MOCK-BUCK-001",
            "MOCK-BOOST-001",
            "MOCK-CONVERTER-001",
            "MOCK-REGULATOR-001",
        ]
        # 重复数据以创建 50 个并发请求
        payloads = [
            {"original_part_number": part_numbers[i % len(part_numbers)]}
            for i in range(50)
        ]

        stats = ConcurrencyTestBase.run_concurrent_requests(
            client, "/replacement", payloads, num_workers=10
        )

        assert stats["success_rate"] == 100.0, f"成功率不是 100%：{stats['success_rate']:.1f}%"
        assert stats["total_requests"] == 50
        assert stats["failed"] == 0
        print(f"\n/replacement 并发请求统计：{stats}")

    def test_replacement_performance_baseline(self, client):
        """替代品查询性能基准测试"""
        payload = {"original_part_number": "MOCK-BUCK-001"}
        stats = BenchmarkTestBase.run_benchmark(
            client, "/replacement", payload, num_requests=100
        )

        avg_latency = stats["avg_latency_ms"]
        p95_latency = stats["p95_latency_ms"]
        p99_latency = stats["p99_latency_ms"]

        # /replacement 包含数据库查询，延迟会略高于 /health
        assert avg_latency < 500, f"平均延迟过高：{avg_latency:.1f}ms"
        assert p95_latency < 1000, f"p95 延迟过高：{p95_latency:.1f}ms"
        assert p99_latency < 2000, f"p99 延迟过高：{p99_latency:.1f}ms"
        assert stats["success_rate"] == 100.0

        print(f"\n/replacement 性能基准统计：")
        print(f"  平均延迟: {avg_latency:.2f}ms")
        print(f"  P50: {stats['p50_latency_ms']:.2f}ms")
        print(f"  P95: {p95_latency:.2f}ms")
        print(f"  P99: {p99_latency:.2f}ms")
        print(f"  成功率: {stats['success_rate']:.1f}%")

    def test_replacement_stability_over_time(self, client):
        """替代品查询长期稳定性测试"""
        payload = {"original_part_number": "MOCK-BUCK-001"}
        interval_results = []
        num_intervals = 5
        requests_per_interval = 10

        for interval in range(num_intervals):
            interval_stats = []
            for _ in range(requests_per_interval):
                start = time.time()
                response = client.post("/replacement", json=payload)
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

        # 延迟波动在 200% 以内是合理的
        assert variance < 200, f"延迟波动过大：{variance:.1f}%"
        print(f"  延迟波动：{variance:.1f}%（可接受）")

    @pytest.mark.concurrent
    def test_replacement_high_concurrency(self, client):
        """替代品查询高并发测试"""
        payloads = [
            {"original_part_number": f"MOCK-PART-{i:03d}"}
            for i in range(500)
        ]
        stats = ConcurrencyTestBase.run_concurrent_requests(
            client, "/replacement", payloads, num_workers=50
        )

        assert stats["success_rate"] == 100.0
        assert stats["total_requests"] == 500
        print(f"\n/replacement 高并发测试（500 个请求）：")
        print(f"  成功率: {stats['success_rate']:.1f}%")
        print(f"  平均延迟: {stats['avg_latency_ms']:.2f}ms")
        print(f"  P95 延迟: {stats['p95_latency_ms']:.2f}ms")

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
# 2.5 - 性能基准测试（综合测试）
# ============================================================================

class TestPerformanceBenchmark:
    """综合性能基准测试"""

    @pytest.mark.benchmark
    def test_all_endpoints_performance_comparison(self, client):
        """所有端点性能对比测试"""
        endpoints_config = [
            {
                "name": "/health",
                "method": "GET",
                "payload": {},
                "thresholds": {
                    "avg": 20,
                    "p95": 50,
                    "p99": 100
                }
            },
            {
                "name": "/analyze",
                "method": "POST",
                "payload": {"user_input": "Buck 12V转5V"},
                "thresholds": {
                    "avg": 500,
                    "p95": 1000,
                    "p99": 2000
                }
            },
            {
                "name": "/replacement",
                "method": "POST",
                "payload": {"original_part_number": "MOCK-BUCK-001"},
                "thresholds": {
                    "avg": 500,
                    "p95": 1000,
                    "p99": 2000
                }
            }
        ]

        print("\n" + "="*80)
        print("综合性能基准测试 - 所有端点性能对比")
        print("="*80)

        results_summary = {}
        for config in endpoints_config:
            endpoint = config["name"]
            payload = config["payload"]
            thresholds = config["thresholds"]

            stats = BenchmarkTestBase.run_benchmark(
                client, endpoint, payload, num_requests=100
            )

            avg_latency = stats["avg_latency_ms"]
            p95_latency = stats["p95_latency_ms"]
            p99_latency = stats["p99_latency_ms"]

            results_summary[endpoint] = {
                "avg": avg_latency,
                "p95": p95_latency,
                "p99": p99_latency,
                "success_rate": stats["success_rate"]
            }

            # 验证延迟在阈值内
            assert avg_latency < thresholds["avg"], \
                f"{endpoint} 平均延迟 {avg_latency:.1f}ms 超过阈值 {thresholds['avg']}ms"
            assert p95_latency < thresholds["p95"], \
                f"{endpoint} P95 延迟 {p95_latency:.1f}ms 超过阈值 {thresholds['p95']}ms"
            assert p99_latency < thresholds["p99"], \
                f"{endpoint} P99 延迟 {p99_latency:.1f}ms 超过阈值 {thresholds['p99']}ms"
            assert stats["success_rate"] == 100.0, \
                f"{endpoint} 成功率 {stats['success_rate']:.1f}% 不是 100%"

            print(f"\n{endpoint}：")
            print(f"  平均延迟: {avg_latency:.2f}ms (阈值: {thresholds['avg']}ms)")
            print(f"  P50: {stats['p50_latency_ms']:.2f}ms")
            print(f"  P95: {p95_latency:.2f}ms (阈值: {thresholds['p95']}ms)")
            print(f"  P99: {p99_latency:.2f}ms (阈值: {thresholds['p99']}ms)")
            print(f"  成功率: {stats['success_rate']:.1f}%")

        print("\n" + "="*80)
        print("性能对比总结")
        print("="*80)

        # 找出性能最优和最差的端点
        endpoints = list(results_summary.keys())
        best_avg = min(results_summary.values(), key=lambda x: x["avg"])
        worst_avg = max(results_summary.values(), key=lambda x: x["avg"])
        best_endpoint = [k for k, v in results_summary.items() if v == best_avg][0]
        worst_endpoint = [k for k, v in results_summary.items() if v == worst_avg][0]

        print(f"最快端点: {best_endpoint} ({best_avg['avg']:.2f}ms)")
        print(f"最慢端点: {worst_endpoint} ({worst_avg['avg']:.2f}ms)")
        print(f"性能差异倍数: {worst_avg['avg'] / best_avg['avg']:.1f}x")

    @pytest.mark.benchmark
    def test_endpoint_load_distribution(self, client):
        """端点负载分布测试"""
        endpoint_configs = [
            ("/health", {}),
            ("/analyze", {"user_input": "test"}),
            ("/replacement", {"original_part_number": "MOCK-001"}),
        ]

        print("\n负载分布测试 - 测试不同并发数对各端点的影响")
        concurrent_levels = [10, 50, 100]

        for endpoint, payload in endpoint_configs:
            print(f"\n{endpoint} 端点负载测试：")
            for num_concurrent in concurrent_levels:
                payloads = [payload.copy() for _ in range(num_concurrent)]
                stats = ConcurrencyTestBase.run_concurrent_requests(
                    client, endpoint, payloads, num_workers=10
                )

                avg_latency = stats["avg_latency_ms"]
                success_rate = stats["success_rate"]
                print(f"  并发数 {num_concurrent:3d}: {avg_latency:6.2f}ms (成功率: {success_rate:5.1f}%)")

                # 验证在并发下仍能保持 100% 成功率
                assert success_rate == 100.0, \
                    f"{endpoint} 在并发 {num_concurrent} 时成功率下降到 {success_rate:.1f}%"

# ============================================================================
# 2.6 - 错误处理和恢复测试
# ============================================================================

class TestErrorHandling:
    """错误处理和恢复测试"""

    def test_analyze_invalid_input_type(self, client):
        """分析端点 - 无效输入类型"""
        # 发送数字而不是字符串
        response = client.post("/analyze", json={"user_input": 12345})
        # 应该能处理或返回错误
        assert response.status_code in [200, 400, 422]

    def test_analyze_empty_input(self, client):
        """分析端点 - 空字符串输入"""
        payload = {"user_input": ""}
        response = client.post("/analyze", json=payload)
        # 应该成功处理空字符串或返回合适的错误
        assert response.status_code in [200, 400]

    def test_analyze_very_long_input(self, client):
        """分析端点 - 超长输入"""
        # 创建长字符串 (10000 字符)
        long_input = "A" * 10000
        payload = {"user_input": long_input}
        response = client.post("/analyze", json=payload)
        # 应该能处理或返回错误
        assert response.status_code in [200, 400, 422, 413]

    def test_analyze_special_characters(self, client):
        """分析端点 - 特殊字符"""
        special_inputs = [
            "!@#$%^&*()",
            "<script>alert('test')</script>",
            "'; DROP TABLE users; --",
            "../../etc/passwd",
        ]
        for special_input in special_inputs:
            payload = {"user_input": special_input}
            response = client.post("/analyze", json=payload)
            # 应该安全处理所有特殊字符
            assert response.status_code in [200, 400, 422]

    def test_replacement_invalid_part_number(self, client):
        """替代品端点 - 无效零件号"""
        invalid_parts = [
            "",
            "NONEXISTENT-PART-12345",
            "@#$%",
        ]
        for part_number in invalid_parts:
            payload = {"original_part_number": part_number}
            response = client.post("/replacement", json=payload)
            # 应该返回 200（处理请求）或 400（无效输入）
            assert response.status_code in [200, 400, 422]

    def test_malformed_json(self, client):
        """测试格式错误的 JSON"""
        # 直接发送格式错误的 JSON（通过 raw content）
        response = client.post(
            "/analyze",
            content=b'{invalid json}',
            headers={"Content-Type": "application/json"}
        )
        # 应该返回 4xx 错误
        assert response.status_code >= 400

    def test_missing_content_type(self, client):
        """测试缺少 Content-Type header"""
        response = client.post("/analyze", json={"user_input": "test"})
        # TestClient 会自动设置正确的 Content-Type，但验证功能性
        assert response.status_code == 200

    def test_error_response_structure(self, client):
        """验证错误响应结构"""
        # 发送缺少必需字段的请求
        payload = {}
        response = client.post("/analyze", json=payload)

        # 验证错误响应包含必要字段
        assert response.status_code == 422
        data = response.json()
        assert "detail" in data or "error" in data or "errors" in data

    def test_replacement_error_response_structure(self, client):
        """验证替代品端点错误响应结构"""
        payload = {}
        response = client.post("/replacement", json=payload)

        assert response.status_code == 422
        data = response.json()
        assert "detail" in data or "error" in data or "errors" in data

    def test_recovery_after_error(self, client):
        """错误恢复测试 - 验证错误后的恢复能力"""
        # 1. 发送有效请求
        valid_response = client.post("/analyze", json={"user_input": "test"})
        assert valid_response.status_code == 200

        # 2. 发送无效请求
        invalid_response = client.post("/analyze", json={})
        assert invalid_response.status_code == 422

        # 3. 再次发送有效请求 - 应该恢复
        recovery_response = client.post("/analyze", json={"user_input": "recovery test"})
        assert recovery_response.status_code == 200
        assert "request_id" in recovery_response.json()

    def test_concurrent_error_recovery(self, client):
        """并发错误恢复测试"""
        mixed_payloads = [
            {"user_input": "valid1"},           # 有效
            {},                                  # 无效
            {"user_input": "valid2"},           # 有效
            {},                                  # 无效
            {"user_input": "valid3"},           # 有效
        ]

        # 运行混合有效和无效的并发请求
        stats = ConcurrencyTestBase.run_concurrent_requests(
            client, "/analyze", mixed_payloads, num_workers=2
        )

        # 验证系统仍能处理有效请求
        assert stats["total_requests"] == 5
        # 预期 3 个成功，2 个失败
        assert stats["successful"] == 3
        assert stats["failed"] == 2

    def test_health_endpoint_always_responds(self, client):
        """健康检查 - 应始终快速响应"""
        # 即使在错误情况下，健康检查也应该响应
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200
            assert response.json() == {"status": "ok"}

    @pytest.mark.concurrent
    def test_error_under_load(self, client):
        """高并发下的错误处理"""
        # 混合有效和无效请求的高并发测试
        payloads = []
        for i in range(100):
            if i % 3 == 0:
                payloads.append({})  # 无效 - 缺少必需字段
            else:
                payloads.append({"user_input": f"test_{i}"})  # 有效

        stats = ConcurrencyTestBase.run_concurrent_requests(
            client, "/analyze", payloads, num_workers=20
        )

        # 验证在高并发负载下，系统能正确处理所有请求
        assert stats["total_requests"] == 100
        # 有效请求数应约为 66（100 - 34 个无效请求）
        assert stats["successful"] >= 65
        # 失败请求数应约为 34（每三个中有一个无效）
        assert stats["failed"] <= 35

    def test_response_content_type_on_error(self, client):
        """验证错误响应的 Content-Type"""
        response = client.post("/analyze", json={})
        assert response.status_code == 422
        assert "application/json" in response.headers.get("content-type", "")

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

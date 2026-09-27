#!/usr/bin/env python3
"""
Integration test for /schematic/{topology} API endpoint

Tests the FastAPI endpoint with different topologies and parameters.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi.testclient import TestClient
from app.main import app


def test_schematic_endpoints():
    """Test /schematic API endpoints."""
    client = TestClient(app)

    test_cases = [
        {
            'name': 'Buck 12V->5V @ 3A',
            'params': {'topology': 'buck', 'Vin': 12, 'Vout': 5, 'Iout': 3}
        },
        {
            'name': 'Boost 5V->12V @ 2A',
            'params': {'topology': 'boost', 'Vin': 5, 'Vout': 12, 'Iout': 2}
        },
        {
            'name': 'LDO 12V->3.3V @ 1A',
            'params': {'topology': 'ldo', 'Vin': 12, 'Vout': 3.3, 'Iout': 1}
        },
    ]

    print("Testing /schematic/{topology} API endpoint:")
    print("-" * 70)

    for test_case in test_cases:
        params = test_case['params']
        topology = params.pop('topology')
        url = f"/schematic/{topology}"

        response = client.get(url, params=params)

        # Check response
        assert response.status_code == 200, f"Status code: {response.status_code}"
        assert response.headers['content-type'] == 'image/svg+xml', f"Content-Type: {response.headers.get('content-type')}"

        svg_content = response.text
        assert '<svg' in svg_content, "SVG tag missing"
        assert len(svg_content) > 1000, f"SVG too small: {len(svg_content)}"

        print(f"[PASS] {test_case['name']:30s} | {len(svg_content):6d} bytes | Status 200")

    print("-" * 70)

    # Test error case
    print("\nTesting error handling:")
    print("-" * 70)

    response = client.get("/schematic/invalid", params={'Vin': 12, 'Vout': 5, 'Iout': 3})
    assert response.status_code == 400, f"Expected 400, got {response.status_code}"
    print(f"[PASS] Invalid topology returns 400 status")

    print("-" * 70)
    print(f"\nAll API tests passed! ({len(test_cases)} topologies)")


if __name__ == '__main__':
    test_schematic_endpoints()
    print("\nB2 API integration test: PASSED")

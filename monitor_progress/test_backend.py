import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

from main import app
from fastapi.testclient import TestClient

client = TestClient(app)

print("="*60)
print("测试后端 API")
print("="*60)

# 测试 /api/stats
print("\n--- 测试 /api/stats ---")
response = client.get("/api/stats")
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    print("响应数据:")
    print(response.json())
else:
    print(f"错误: {response.text}")

# 测试 /api/heatmap
print("\n--- 测试 /api/heatmap ---")
response = client.get("/api/heatmap")
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"xAxis数量: {len(data.get('xAxis', []))}")
    print(f"yAxis数量: {len(data.get('yAxis', []))}")
    print(f"data数量: {len(data.get('data', []))}")
else:
    print(f"错误: {response.text}")

# 测试 /api/monthly-stats
print("\n--- 测试 /api/monthly-stats ---")
response = client.get("/api/monthly-stats")
print(f"状态码: {response.status_code}")
if response.status_code == 200:
    data = response.json()
    print(f"月份数: {len(data.get('months', []))}")
    print(f"账号数: {len(data.get('data', []))}")
    print(f"总计: {data.get('total')}")
else:
    print(f"错误: {response.text}")

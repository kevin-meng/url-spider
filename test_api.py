import requests
import json

# 测试第一个查询参数（包含is_collected和scores）
params1 = {
    "page": 1,
    "page_size": 10,
    "score_type": "socre",
    "scores": [8, 9, 10],
    "sort_by": "socre",
    "sort_order": "desc",
    "start_date": "2026-02-23",
    "end_date": "2026-02-23",
}


# 测试第二个查询参数（不包含is_collected和scores）
params2 = {
    "page": 1,
    "page_size": 10,
    "score_type": "socre",
    "tags": "AI,投资",
    "sort_by": "socre",
    "sort_order": "desc",
    "start_date": "2026-02-23",
    "end_date": "2026-02-23",
}


url = "http://localhost:8000/api/articles"

print("测试第一个查询参数（包含is_collected和scores）:")
print("参数:", params1)
try:
    response1 = requests.get(url, params=params1)
    response1.raise_for_status()
    data1 = response1.json()
    print("状态码:", response1.status_code)
    print("返回结果总数:", data1.get("total", 0))
except Exception as e:
    print("请求失败:", e)

print("\n测试第二个查询参数（不包含is_collected和scores）:")
print("参数:", params2)
try:
    response2 = requests.get(url, params=params2)
    response2.raise_for_status()
    data2 = response2.json()
    print("状态码:", response2.status_code)
    print("返回结果总数:", data2.get("total", 0))
except Exception as e:
    print("请求失败:", e)

print("\n结果比较:")
if "data1" in locals() and "data2" in locals():
    total1 = data1.get("total", 0)
    total2 = data2.get("total", 0)
    print(f"第一个查询结果数: {total1}")
    print(f"第二个查询结果数: {total2}")
    print(f"两个查询结果数是否相同: {total1 == total2}")

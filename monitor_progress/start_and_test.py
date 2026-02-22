import sys
import os
import time
import subprocess
import requests

print("="*60)
print("启动后端并测试")
print("="*60)

# 先停止可能正在运行的后端
print("\n--- 清理旧进程 ---")
try:
    subprocess.run(["pkill", "-f", "uvicorn.*8000"], capture_output=True)
except:
    pass
time.sleep(1)

# 启动后端
print("\n--- 启动后端 ---")
backend_proc = subprocess.Popen(
    [sys.executable, "-m", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"],
    cwd=os.path.join(os.path.dirname(__file__), "backend"),
    stdout=subprocess.PIPE,
    stderr=subprocess.STDOUT,
    text=True
)

# 等待后端启动
print("等待后端启动...")
time.sleep(5)

# 测试API
print("\n--- 测试 API ---")
try:
    response = requests.get("http://localhost:8000/api/stats", timeout=10)
    print(f"状态码: {response.status_code}")
    if response.status_code == 200:
        print("成功！数据:")
        print(response.json())
    else:
        print(f"错误: {response.text}")
except Exception as e:
    print(f"请求异常: {e}")
    # 打印后端日志
    print("\n--- 后端日志 ---")
    try:
        backend_proc.terminate()
        stdout, _ = backend_proc.communicate(timeout=2)
        print(stdout)
    except:
        pass

print("\n按 Ctrl+C 停止后端")
try:
    while True:
        time.sleep(1)
except KeyboardInterrupt:
    print("\n停止后端...")
    backend_proc.terminate()
    try:
        backend_proc.wait(timeout=5)
    except:
        backend_proc.kill()
    print("已停止")

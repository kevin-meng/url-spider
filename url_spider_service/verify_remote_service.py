import requests
import json
import time

BASE_URL = "http://192.168.2.18:8013"

def test_endpoint(name, method, endpoint, data=None):
    print(f"Testing {name} ({endpoint})...")
    try:
        start_time = time.time()
        if method == "GET":
            response = requests.get(f"{BASE_URL}{endpoint}")
        elif method == "POST":
            response = requests.post(f"{BASE_URL}{endpoint}", json=data)
        
        duration = time.time() - start_time
        
        if response.status_code == 200:
            print(f"✅ {name}: Success ({duration:.2f}s)")
            try:
                print(f"   Result: {str(response.json())[:200]}...") # Truncate output
            except:
                print(f"   Result: {response.text[:200]}...")
            return True, response.json()
        else:
            print(f"❌ {name}: Failed with {response.status_code}")
            print(f"   Error: {response.text}")
            return False, None
    except Exception as e:
        print(f"❌ {name}: Error - {e}")
        return False, None

def main():
    print(f"Verifying Service at {BASE_URL}")
    
    # 1. Health
    success, _ = test_endpoint("Health Check", "GET", "/health")
    if not success:
        print("Health check failed, aborting further tests.")
        return

    # 2. Clip (Interface 1)
    clip_payload = {"url": "https://example.com"}
    success, clip_result = test_endpoint("Clip Interface", "POST", "/api/clip", clip_payload)
    
    markdown_content = ""
    if success and clip_result:
        markdown_content = clip_result.get("full_markdown", "")
        if not markdown_content:
            markdown_content = clip_result.get("content", "")

    # 3. Evaluate (Interface 3)
    evaluate_payload = {
        "articles": [
            {
                "title": "Example Domain",
                "description": "This domain is for use in illustrative examples in documents."
            }
        ]
    }
    test_endpoint("Evaluate Interface", "POST", "/api/evaluate", evaluate_payload)

    # 4. Summarize (Interface 2)
    if markdown_content:
        summarize_payload = {"markdown_content": markdown_content}
        test_endpoint("Summarize Interface", "POST", "/api/summarize", summarize_payload)
    else:
        print("Skipping Summarize test because Clip failed or returned empty content.")

if __name__ == "__main__":
    main()

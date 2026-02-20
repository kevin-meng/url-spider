import asyncio
import sys
import os

# Ensure we can import from current directory
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.clipper_service import ClipperService

async def test_clip_single():
    url = "https://mp.weixin.qq.com/s/6w-CxmZPNfrRArOBw8n-bQ"
    
    print(f"正在测试剪藏: {url}")
    
    # 确保能找到配置文件
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    clipper = ClipperService()
    
    result = await clipper.process_url(url)
    
    if "error" in result:
        print(f"剪藏失败: {result['error']}")
    else:
        full_markdown = result.get("full_markdown", "")
        filename = "test_clip_result.md"
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(full_markdown)
            
        print(f"\n✅ 剪藏成功！结果已保存到: {os.path.abspath(filename)}")
        
        # 简单检查
        content = result.get("content", "")
        print("\n=== 链接/图片检查 ===")
        if "![" in content:
            print("✅ 发现图片标记 (![)")
        else:
            print("❌ 未发现图片标记")
            
        if "http" in content and "](" in content:
             print("✅ 发现超链接标记 (](http...)")
        else:
             print("⚠️ 未发现明显超链接")

if __name__ == "__main__":
    asyncio.run(test_clip_single())

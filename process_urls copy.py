import asyncio
import json
import os
import sys
import argparse
import re
from typing import List, Dict, Any, Optional

# Add current directory to path to import clipper
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from clipper import Clipper

try:
    from openai import AsyncOpenAI
except ImportError:
    pass

try:
    from anthropic import AsyncAnthropic
except ImportError:
    pass

if 'AsyncOpenAI' not in globals() and 'AsyncAnthropic' not in globals():
    print("Please install openai or anthropic: pip install openai anthropic")
    sys.exit(1)

# Configuration defaults
DEFAULT_SETTINGS_PATH = "exmemo_tools_settings_2026-02-19.json"
DEFAULT_CLIPPER_SETTINGS = "obsidian-web-clipper-settings.json"

class URLProcessor:
    def __init__(self, settings_path: str, clipper_settings_path: str, concurrency: int = 5, model_name: Optional[str] = None):
        self.settings_path = settings_path
        self.clipper_settings_path = clipper_settings_path
        self.concurrency = concurrency
        
        self._load_settings()
        self.clipper = Clipper(self.clipper_settings_path)
        
        self.client = None
        self.provider = "openai"
        self.model_name = model_name or self.settings.get("llmModelName")
        
        # Determine provider based on settings or model
        llm_base_url = self.settings.get("llmBaseUrl", "")
        llm_token = self.settings.get("llmToken")
        
        # Heuristic to switch to Anthropic if URL contains "anthropic" or model name starts with "claude" or "MiniMax" (as per user context)
        # The user provided config uses "MiniMax" model and "anthropic" in URL.
        if "anthropic" in llm_base_url.lower() or "minimax" in llm_base_url.lower() or (self.model_name and ("claude" in self.model_name.lower() or "minimax" in self.model_name.lower())):
              if 'AsyncAnthropic' in globals():
                  self.provider = "anthropic"
                  # Anthropic SDK expects base_url without /v1 usually, but some proxies require full path.
                  # For MiniMax via Anthropic SDK, it seems they follow Anthropic format which is /v1/messages
                  # But the SDK appends /messages. 
                  # If user provides "https://api.minimaxi.com/anthropic", SDK will likely call "https://api.minimaxi.com/anthropic/messages"
                  # However, standard Anthropic SDK calls base_url + "/messages" (actually it depends on version, usually /v1/messages)
                  # If base_url is "https://api.minimaxi.com", and we want "https://api.minimaxi.com/anthropic/messages"?
                  # The provided text says: export ANTHROPIC_BASE_URL=https://api.minimaxi.com/anthropic
                  # So we should probably use that.
                  
                  # If the settings has just "https://api.minimaxi.com", we might need to append "/anthropic" if it's MiniMax.
                  # But let's trust the settings first. If settings is "https://api.minimaxi.com", let's try appending /anthropic if it's minimax.
                  
                  if "minimax" in llm_base_url.lower() and "anthropic" not in llm_base_url.lower():
                       llm_base_url = llm_base_url.rstrip("/") + "/anthropic"
                  
                  self.client = AsyncAnthropic(
                      api_key=llm_token,
                      base_url=llm_base_url
                  )
              else:
                  print("Anthropic provider detected but anthropic package not installed.")
        
        if not self.client and 'AsyncOpenAI' in globals():
             self.provider = "openai"
             self.client = AsyncOpenAI(
                api_key=llm_token,
                base_url=llm_base_url
             )
             
        if not self.client:
             raise ImportError("No suitable LLM client found or configured.")
        
    def _load_settings(self):
        if not os.path.exists(self.settings_path):
            raise FileNotFoundError(f"Settings file not found: {self.settings_path}")
            
        with open(self.settings_path, "r", encoding="utf-8") as f:
            self.settings = json.load(f)

    def construct_system_prompt(self) -> str:
        return "You are a helpful assistant capable of analyzing text and extracting structured information. You must return valid JSON only, without any markdown formatting or code blocks."

    def construct_user_prompt(self, content: str) -> str:
        instructions = []
        
        # 1. Description
        desc_field = self.settings.get("metaDescriptionFieldName", "description")
        desc_prompt = self.settings.get("metaDescription", "Summarize the content.")
        instructions.append(f"- '{desc_field}': {desc_prompt}")
        
        # 2. Tags
        tags_field = self.settings.get("metaTagsFieldName", "tags")
        tags_prompt = self.settings.get("metaTagsPrompt", "Extract tags.")
        instructions.append(f"- '{tags_field}': {tags_prompt} (Return as a list of strings)")
        
        # 3. Custom Metadata
        for item in self.settings.get("customMetadata", []):
            if item.get("type") == "prompt":
                key = item.get("key")
                value = item.get("value")
                instructions.append(f"- '{key}': {value}")
        
        instruction_str = "\n".join(instructions)
        
        # Truncate content if it's too long
        truncated_content = content[:30000]
        
        prompt = f"""
Please analyze the following content and extract information according to the instructions below.
Return a JSON object where keys match the field names specified in the instructions.

Instructions:
{instruction_str}

Content:
{truncated_content}
"""
        return prompt

    async def process_single_url(self, url: str, semaphore: asyncio.Semaphore):
        async with semaphore:
            print(f"Processing: {url}")
            try:
                # Step 1: Clip URL to Markdown
                md_path = await self.clipper.process_url(url)
                
                if not md_path:
                    print(f"Failed to clip URL: {url}")
                    return

                print(f"Clipped to: {md_path}")
                
                # Step 2: Read Markdown content
                if not os.path.exists(md_path):
                    print(f"File not found: {md_path}")
                    return
                    
                with open(md_path, "r", encoding="utf-8") as f:
                    file_content = f.read()
                
                # Step 3: Call LLM
                prompt = self.construct_user_prompt(file_content)
                
                print(f"Analyzing with LLM ({self.model_name}) using {self.provider}...")
                
                result_content = ""
                
                if self.provider == "openai":
                    response = await self.client.chat.completions.create(
                        model=self.model_name,
                        messages=[
                            {"role": "system", "content": self.construct_system_prompt()},
                            {"role": "user", "content": prompt}
                        ],
                        response_format={"type": "json_object"}
                    )
                    result_content = response.choices[0].message.content
                elif self.provider == "anthropic":
                    response = await self.client.messages.create(
                        model=self.model_name,
                        max_tokens=4096,
                        system=self.construct_system_prompt(),
                        messages=[
                            {"role": "user", "content": prompt}
                        ]
                    )
                    # Anthropic response content is a list of blocks
                    if response.content and len(response.content) > 0:
                        for block in response.content:
                            if block.type == 'text':
                                result_content += block.text
                            # Handle MiniMax 'thinking' blocks if needed, but usually we just want text
                            # MiniMax might return 'thinking' type blocks.
                
                if not result_content:
                    print(f"Empty response from LLM for {md_path}")
                    return

                try:
                    llm_data = json.loads(result_content)
                except json.JSONDecodeError:
                    # Try to fix common JSON errors
                    clean_content = result_content.replace("```json", "").replace("```", "").strip()
                    try:
                        llm_data = json.loads(clean_content)
                    except json.JSONDecodeError:
                        print(f"Failed to parse JSON response for {md_path}: {result_content[:100]}...")
                        return

                # Step 4: Update Markdown file
                self.update_markdown_file(md_path, file_content, llm_data)
                print(f"Updated metadata for: {md_path}")

            except Exception as e:
                print(f"Error processing {url}: {e}")
                import traceback
                traceback.print_exc()

    def update_markdown_file(self, file_path: str, original_content: str, new_metadata: Dict[str, Any]):
        frontmatter_lines = []
        body = original_content
        
        if original_content.startswith("---\n"):
            parts = original_content.split("---\n", 2)
            if len(parts) >= 3:
                frontmatter_raw = parts[1]
                frontmatter_lines = frontmatter_raw.splitlines()
                body = parts[2]
        
        new_frontmatter_lines = []
        for k, v in new_metadata.items():
            if isinstance(v, list):
                new_frontmatter_lines.append(f"{k}:")
                for item in v:
                    if ":" in str(item) or "#" in str(item):
                         new_frontmatter_lines.append(f"  - \"{str(item)}\"")
                    else:
                         new_frontmatter_lines.append(f"  - {str(item)}")
            else:
                val_str = str(v)
                if "\n" in val_str:
                    new_frontmatter_lines.append(f"{k}: |")
                    for line in val_str.splitlines():
                        new_frontmatter_lines.append(f"  {line}")
                else:
                    if ":" in val_str or "#" in val_str or "[" in val_str:
                         new_frontmatter_lines.append(f"{k}: \"{val_str}\"")
                    else:
                         new_frontmatter_lines.append(f"{k}: {val_str}")
        
        # Remove existing keys if they are being updated
        keys_to_update = set(new_metadata.keys())
        filtered_lines = []
        skip_mode = False 
        
        for line in frontmatter_lines:
            stripped = line.lstrip()
            indent = len(line) - len(stripped)
            
            if indent == 0 and ":" in line:
                key = line.split(":", 1)[0].strip()
                if key in keys_to_update:
                    skip_mode = True
                    continue
                else:
                    skip_mode = False
                    filtered_lines.append(line)
            elif skip_mode and indent > 0:
                continue
            else:
                filtered_lines.append(line)
        
        final_frontmatter = "\n".join(filtered_lines + new_frontmatter_lines)
        new_content = f"---\n{final_frontmatter}\n---\n{body}"
            
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(new_content)

    async def run(self, urls: List[str]):
        semaphore = asyncio.Semaphore(self.concurrency)
        tasks = [self.process_single_url(url, semaphore) for url in urls]
        await asyncio.gather(*tasks)

async def main():
    parser = argparse.ArgumentParser(description="Process URLs: Clip to Markdown and enrich with LLM.")
    parser.add_argument("urls", nargs="*", help="List of URLs to process")
    parser.add_argument("--file", "-f", help="File containing URLs (one per line)")
    parser.add_argument("--concurrency", "-c", type=int, default=5, help="Concurrency limit")
    parser.add_argument("--model", "-m", help="Override LLM model name")
    
    args = parser.parse_args()
    
    urls = args.urls
    if args.file:
        if os.path.exists(args.file):
            with open(args.file, "r", encoding="utf-8") as f:
                urls.extend([line.strip() for line in f if line.strip()])
        else:
            print(f"File not found: {args.file}")
            return

    if not urls:
        print("No URLs provided.")
        return

    processor = URLProcessor(
        settings_path=DEFAULT_SETTINGS_PATH,
        clipper_settings_path=DEFAULT_CLIPPER_SETTINGS,
        concurrency=args.concurrency,
        model_name=args.model
    )
    
    print(f"Starting processing of {len(urls)} URLs with concurrency {args.concurrency}...")
    await processor.run(urls)
    print("All done.")

if __name__ == "__main__":
    asyncio.run(main())

import json
import re
import sys
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional
from urllib.parse import urlparse

from playwright.async_api import async_playwright, Page
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from dateutil import parser as date_parser
import trafilatura

# Configuration
SETTINGS_PATH = "obsidian-web-clipper-settings.json"
OUTPUT_DIR = "inbox"

class TemplateEngine:
    def __init__(self, page: Page, soup: BeautifulSoup, url: str):
        self.page = page
        self.soup = soup
        self.url = url
        self.context = {
            "url": url,
            "date": datetime.now(),
            "title": "", # Will be populated
            "description": "" # Will be populated
        }

    async def extract_value(self, expression: str) -> Any:
        # Remove {{ and }}
        content = expression.strip("{}")
        parts = content.split("|")
        
        # The first part is the source
        source = parts[0].strip()
        value = await self._get_source_value(source)
        
        # Apply filters
        for part in parts[1:]:
            filter_def = part.strip()
            if ":" in filter_def:
                filter_name, filter_args = filter_def.split(":", 1)
                # Handle quoted arguments like "a", "b"
                # This is a simple parser, might need more robustness
                args = self._parse_args(filter_args)
            else:
                filter_name = filter_def
                args = []
            
            value = self._apply_filter(value, filter_name, args)
            
        return value

    async def _get_source_value(self, source: str):
        if source == "url":
            return self.url
        elif source == "date":
            return datetime.now()
        elif source == "title":
            return await self.page.title()
        elif source == "author":
            # Try to get meta author
            try:
                author = await self.page.locator('meta[name="author"]').get_attribute("content")
                return author if author else ""
            except:
                return ""
        elif source == "content":
            # Use Trafilatura to extract main content
            html = await self.page.content()
            try:
                # Extract directly to Markdown
                extracted = trafilatura.extract(
                    html, 
                    include_links=True, 
                    include_images=True, 
                    include_comments=False,
                    output_format="markdown"
                )
                return extracted if extracted else ""
            except Exception as e:
                print(f"Error extracting content: {e}")
                return ""
        elif source == "description":
            # Try to get meta description
            try:
                desc = await self.page.locator('meta[name="description"]').get_attribute("content")
                return desc if desc else ""
            except:
                return ""
        elif source.startswith("selector:"):
            selector = source.split(":", 1)[1]
            try:
                # Use BeautifulSoup for more consistent text extraction or Playwright
                # Playwright inner_text is good
                if await self.page.locator(selector).count() > 0:
                     return await self.page.locator(selector).first.inner_text()
                return ""
            except Exception as e:
                print(f"Error extracting selector {selector}: {e}")
                return ""
        elif source.startswith("selectorHtml:"):
            selector = source.split(":", 1)[1]
            try:
                if await self.page.locator(selector).count() > 0:
                    return await self.page.locator(selector).first.inner_html()
                return ""
            except:
                return ""
        
        # Default fallback if it's a literal or unknown
        return source

    def _parse_args(self, args_str: str) -> List[Any]:
        # Simple argument parser handling quoted strings
        # e.g. "YYYY-MM-DD" or " - 知乎",""
        args = []
        current = ""
        in_quote = False
        quote_char = None
        
        for char in args_str:
            if char in ['"', "'"]:
                if not in_quote:
                    in_quote = True
                    quote_char = char
                elif char == quote_char:
                    in_quote = False
                    quote_char = None
                else:
                    current += char
            elif char == ',' and not in_quote:
                args.append(current.strip())
                current = ""
            else:
                current += char
        
        if current:
            args.append(current.strip())
            
        return args

    def _apply_filter(self, value: Any, filter_name: str, args: List[Any]) -> Any:
        try:
            if filter_name == "date":
                fmt = args[0] if args else "%Y-%m-%d"
                # Map Moment.js format to Python strftime
                fmt = fmt.replace("YYYY", "%Y").replace("MM", "%m").replace("DD", "%d")
                fmt = fmt.replace("HH", "%H").replace("mm", "%M").replace("ss", "%S")
                
                if isinstance(value, str):
                    try:
                        dt = date_parser.parse(value)
                    except:
                        return value
                elif isinstance(value, datetime):
                    dt = value
                else:
                    return value
                return dt.strftime(fmt)
            
            elif filter_name == "replace":
                old = args[0] if len(args) > 0 else ""
                new = args[1] if len(args) > 1 else ""
                # Handle regex replacement if needed, but simple replace for now
                # JSON settings might use regex syntax? " - 知乎":"" implies string replace
                return str(value).replace(old, new)
            
            elif filter_name == "split":
                sep = args[0] if args else ","
                return str(value).split(sep)
            
            elif filter_name == "join":
                sep = args[0] if args else " "
                if isinstance(value, list):
                    return sep.join(value)
                return value
            
            elif filter_name == "slice":
                # slice:4 means first 4? or start at 4?
                # slice:0,1
                if len(args) == 1:
                    end = int(args[0])
                    return value[:end]
                elif len(args) >= 2:
                    start = int(args[0])
                    end = int(args[1]) if args[1] else None
                    return value[start:end]
                return value
                
            elif filter_name == "markdown":
                return md(str(value), heading_style="ATX")
            
            elif filter_name == "remove_tags":
                tag = args[0] if args else ""
                soup = BeautifulSoup(str(value), "html.parser")
                for s in soup.select(tag):
                    s.decompose()
                return str(soup)
                
            elif filter_name == "wikilink":
                if isinstance(value, list):
                    return [f"[[{v}]]" for v in value]
                return f"[[{value}]]"
            
            elif filter_name == "first":
                if isinstance(value, list) and len(value) > 0:
                    return value[0]
                return value

        except Exception as e:
            print(f"Error applying filter {filter_name}: {e}")
            return value
        
        return value

class Clipper:
    def __init__(self, settings_path: str):
        with open(settings_path, "r", encoding="utf-8") as f:
            self.settings = json.load(f)
        self.templates = self._load_templates()

    def _load_templates(self):
        templates = {}
        for t_id in self.settings.get("template_list", []):
            if f"template_{t_id}" in self.settings:
                templates[t_id] = self.settings[f"template_{t_id}"]
        return templates

    def find_template(self, url: str):
        for t_id, template in self.templates.items():
            triggers = template.get("triggers", [])
            for trigger in triggers:
                # Convert glob to regex
                # Simple glob: * matches anything
                pattern = re.escape(trigger).replace(r"\*", ".*")
                if re.match(f"^{pattern}", url):
                    return template
        
        # Fallback to generic template if exists (usually first or specific name)
        # Based on settings file, 17641814671660kno01p6y is "通用" (General)
        # But it has empty triggers.
        for t_id, template in self.templates.items():
            if template.get("name") == "通用":
                return template
        
        return None

    async def process_url(self, url: str):
        template = self.find_template(url)
        if not template:
            print(f"No template found for {url}")
            return

        print(f"Using template: {template['name']}")

        async with async_playwright() as p:
            # Launch with a real user agent to avoid basic detection
            browser = await p.chromium.launch(
                headless=True,
                args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
                timezone_id="Asia/Shanghai"
            )
            page = await context.new_page()
            
            # Stealth script
            await page.add_init_script("""
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """)
            
            try:
                print(f"Navigating to {url}...")
                await page.goto(url, wait_until="domcontentloaded", timeout=60000)
                
                # Intelligent waiting based on template selectors
                # Find the first 'selector:' in properties to wait for
                wait_selector = None
                for prop in template.get("properties", []):
                    val = prop.get("value", "")
                    if "selector:" in val:
                        match = re.search(r"selector:([^|}]*)", val)
                        if match:
                            wait_selector = match.group(1).strip()
                            break
                    elif "selectorHtml:" in val:
                        match = re.search(r"selectorHtml:([^|}]*)", val)
                        if match:
                            wait_selector = match.group(1).strip()
                            break
                
                if wait_selector:
                    print(f"Waiting for selector: {wait_selector}")
                    try:
                        await page.wait_for_selector(wait_selector, timeout=10000)
                    except Exception as e:
                        print(f"Warning: Timeout waiting for {wait_selector}, proceeding anyway...")

                # Give a little extra time for dynamic content to settle
                await page.wait_for_timeout(3000) 
                
                title = await page.title()
                print(f"Page Title: {title}")
                
                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                
                engine = TemplateEngine(page, soup, url)
                
                # 1. Extract Properties
                properties = {}
                for prop in template.get("properties", []):
                    name = prop["name"]
                    value_expr = prop.get("value", "")
                    if value_expr:
                        # Parse template string like "{{title}}" or "{{selector:...}}"
                        # We need to find all {{...}} blocks and replace them
                        
                        # Helper to replace matches asynchronously
                        # Python regex doesn't support async replacement directly
                        # So we find all matches, compute values, then replace
                        matches = re.findall(r"\{\{.*?\}\}", value_expr)
                        result_str = value_expr
                        
                        for match in matches:
                            val = await engine.extract_value(match)
                            # If the result is a list (e.g. multiline), join it or keep it?
                            # Property values are usually strings in the final MD
                            if isinstance(val, list):
                                val = ", ".join(str(v) for v in val)
                            result_str = result_str.replace(match, str(val))
                            
                        properties[name] = result_str
                    else:
                        # If no value expression, use default or empty
                        properties[name] = ""

                # 2. Extract Content
                content_fmt = template.get("noteContentFormat", "{{content}}")
                matches = re.findall(r"\{\{.*?\}\}", content_fmt)
                final_content = content_fmt
                
                for match in matches:
                    val = await engine.extract_value(match)
                    final_content = final_content.replace(match, str(val))

                # 3. Generate Filename
                name_fmt = template.get("noteNameFormat", "{{title}}")
                matches = re.findall(r"\{\{.*?\}\}", name_fmt)
                filename = name_fmt
                for match in matches:
                    val = await engine.extract_value(match)
                    filename = filename.replace(match, str(val))
                
                # Sanitize filename
                filename = re.sub(r'[\\/*?:"<>|]', "", filename)
                filename = filename.strip()
                if not filename:
                    filename = "Untitled"

                # 4. Construct File Content (Frontmatter + Content)
                file_output = "---\n"
                for k, v in properties.items():
                    # Handle multiline or special chars in YAML
                    if "\n" in str(v):
                        file_output += f"{k}: |\n  {str(v).replace(chr(10), chr(10)+'  ')}\n"
                    else:
                        file_output += f"{k}: {v}\n"
                file_output += "---\n\n"
                file_output += final_content

                # 5. Save
                if not os.path.exists(OUTPUT_DIR):
                    os.makedirs(OUTPUT_DIR)
                
                out_path = os.path.join(OUTPUT_DIR, f"{filename}.md")
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(file_output)
                
                print(f"Saved to {out_path}")
                return out_path

            except Exception as e:
                print(f"Error processing {url}: {e}")
                import traceback
                traceback.print_exc()
                return None
            finally:
                await browser.close()

if __name__ == "__main__":
    print("Starting clipper...")
    if len(sys.argv) < 2:
        print("Usage: python clipper.py <url>")
        sys.exit(1)
        
    url = sys.argv[1]
    clipper = Clipper(SETTINGS_PATH)
    print(f"Loaded {len(clipper.templates)} templates.")
    asyncio.run(clipper.process_url(url))

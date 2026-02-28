import json
import re
import os
import asyncio
from datetime import datetime
from typing import Dict, List, Any, Optional

from playwright.async_api import async_playwright, Page, TimeoutError
from bs4 import BeautifulSoup
from markdownify import markdownify as md
from dateutil import parser as date_parser
import trafilatura


class TemplateEngine:
    def __init__(self, page: Page, soup: BeautifulSoup, url: str):
        self.page = page
        self.soup = soup
        self.url = url

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
            try:
                author = await self.page.locator('meta[name="author"]').get_attribute(
                    "content"
                )
                return author if author else ""
            except:
                return ""
        elif source == "content":
            html = await self.page.content()

            # Pre-process HTML to handle lazy-loaded images (common in WeChat/lazy-load sites)
            # Replace data-src with src to ensure extractors pick up images
            html = html.replace('data-src="', 'src="').replace(
                'data-original-src="', 'src="'
            )

            try:
                # 微信公众号文章强制使用 markdownify，因为 trafilatura 经常丢失图片
                # 改进：先定位到正文区域，再转换，避免包含无关内容
                if "mp.weixin.qq.com" in self.url:
                    print("检测到微信公众号文章，优先使用 markdownify...")
                    soup = BeautifulSoup(html, "html.parser")

                    # 微信公众号正文通常在 id="js_content" 或 class="rich_media_content"
                    content_div = soup.find(id="js_content") or soup.find(
                        class_="rich_media_content"
                    )

                    if content_div:
                        # 移除无关的js脚本和样式
                        for s in content_div(["script", "style"]):
                            s.decompose()
                        from markdownify import markdownify as md

                        return md(str(content_div))
                    else:
                        # 如果找不到特定区域，回退到 body
                        for s in soup(["script", "style"]):
                            s.decompose()
                        from markdownify import markdownify as md

                        return md(str(soup))

                # Extract directly to Markdown using trafilatura
                extracted = trafilatura.extract(
                    html,
                    include_links=True,
                    include_images=True,
                    include_comments=False,
                    include_formatting=True,  # 保留格式，包括链接
                    output_format="markdown",
                )

                # Fallback to markdownify if trafilatura returns empty or non-markdown (simple check)
                if not extracted or (len(extracted) < 50 and "<html" in html):
                    print("Trafilatura extraction weak, falling back to markdownify...")
                    from markdownify import markdownify as md

                    extracted = md(html)

                return extracted if extracted else ""
            except Exception as e:
                print(f"提取内容失败: {e}")
                # Fallback
                try:
                    from markdownify import markdownify as md

                    return md(html)
                except:
                    return ""
        elif source == "description":
            try:
                desc = await self.page.locator(
                    'meta[name="description"]'
                ).get_attribute("content")
                return desc if desc else ""
            except:
                return ""
        elif source.startswith("selector:"):
            selector = source.split(":", 1)[1]
            try:
                if await self.page.locator(selector).count() > 0:
                    return await self.page.locator(selector).first.inner_text()
                return ""
            except Exception as e:
                print(f"提取选择器失败 {selector}: {e}")
                return ""
        elif source.startswith("selectorHtml:"):
            selector = source.split(":", 1)[1]
            try:
                if await self.page.locator(selector).count() > 0:
                    return await self.page.locator(selector).first.inner_html()
                return ""
            except:
                return ""

        return source

    def _parse_args(self, args_str: str) -> List[Any]:
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
            elif char == "," and not in_quote:
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
            print(f"应用过滤器失败 {filter_name}: {e}")
            return value

        return value


class ClipperService:
    def __init__(self, settings_path: str = "obsidian-web-clipper-settings.json"):
        if os.path.exists(settings_path):
            with open(settings_path, "r", encoding="utf-8") as f:
                self.settings = json.load(f)
        else:
            self.settings = {}
        self.templates = self._load_templates()

    def _load_templates(self):
        templates = {}
        for t_id in self.settings.get("template_list", []):
            if f"template_{t_id}" in self.settings:
                templates[t_id] = self.settings[f"template_{t_id}"]
        return templates

    def find_template(self, url: str):
        # 1. Try to match triggers
        for t_id, template in self.templates.items():
            triggers = template.get("triggers", [])
            for trigger in triggers:
                # Convert glob to regex
                pattern = re.escape(trigger).replace(r"\*", ".*")
                if re.match(f"^{pattern}", url):
                    return template

        # 2. Fallback to "通用" template
        for t_id, template in self.templates.items():
            if template.get("name") == "通用":
                return template

        # 3. Last resort: Return the first available template or a default structure
        if self.templates:
            return list(self.templates.values())[0]

        # 4. Absolute fallback if no templates exist
        return {
            "name": "Fallback",
            "properties": [],
            "noteContentFormat": "{{content}}",
            "noteNameFormat": "{{title}}",
        }

    async def process_url(self, url: str) -> Dict[str, Any]:
        template = self.find_template(url)
        if not template:
            return {"error": f"未找到匹配的模板: {url}"}

        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True, args=["--disable-blink-features=AutomationControlled"]
            )
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                viewport={"width": 1920, "height": 1080},
                locale="zh-CN",
                timezone_id="Asia/Shanghai",
            )
            page = await context.new_page()

            await page.add_init_script(
                """
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined
                });
            """
            )

            try:
                # 增加重试机制 (3次)
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        timeout_ms = 60000 + (attempt * 30000)  # 60s, 90s, 120s
                        print(
                            f"正在访问: {url} (尝试 {attempt + 1}/{max_retries}, 超时: {timeout_ms}ms)..."
                        )
                        await page.goto(
                            url, wait_until="domcontentloaded", timeout=timeout_ms
                        )
                        break  # 成功则跳出重试循环
                    except TimeoutError:
                        print(f"警告: 访问超时 ({timeout_ms}ms)")
                        if attempt == max_retries - 1:
                            raise  # 最后一次重试失败，抛出异常
                        print("正在重试...")
                    except Exception as e:
                        # 忽略特定的网络错误以便重试
                        if "net::" in str(e) or "Timeout" in str(e):
                            print(f"警告: 网络错误: {e}")
                            if attempt == max_retries - 1:
                                raise
                            print("正在重试...")
                        else:
                            raise e  # 其他错误直接抛出

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
                    try:
                        await page.wait_for_selector(wait_selector, timeout=10000)
                    except Exception as e:
                        print(f"警告: 等待选择器超时 {wait_selector}, 继续执行...")

                await page.wait_for_timeout(3000)

                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")

                engine = TemplateEngine(page, soup, url)

                # 1. Extract Properties
                properties = {}
                for prop in template.get("properties", []):
                    name = prop["name"]
                    value_expr = prop.get("value", "")
                    if value_expr:
                        matches = re.findall(r"\{\{.*?\}\}", value_expr)
                        result_str = value_expr

                        for match in matches:
                            val = await engine.extract_value(match)
                            if isinstance(val, list):
                                val = ", ".join(str(v) for v in val)
                            result_str = result_str.replace(match, str(val))

                        properties[name] = result_str
                    else:
                        properties[name] = ""

                # 2. Extract Content
                content_fmt = template.get("noteContentFormat", "{{content}}")
                matches = re.findall(r"\{\{.*?\}\}", content_fmt)
                final_content = content_fmt

                for match in matches:
                    val = await engine.extract_value(match)
                    final_content = final_content.replace(match, str(val))

                # 3. Construct File Content (Frontmatter + Content)
                file_output = "---\n"
                for k, v in properties.items():
                    if "\n" in str(v):
                        file_output += (
                            f"{k}: |\n  {str(v).replace(chr(10), chr(10)+'  ')}\n"
                        )
                    else:
                        file_output += f"{k}: {v}\n"
                file_output += "---\n\n"
                file_output += final_content

                return {
                    "metadata": properties,
                    "content": final_content,
                    "full_markdown": file_output,
                }

            except Exception as e:
                import traceback

                traceback.print_exc()
                return {"error": str(e)}
            finally:
                await browser.close()

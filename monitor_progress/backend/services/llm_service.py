import json
import os
import asyncio
from typing import List, Dict, Any, Optional

try:
    from openai import AsyncOpenAI
except ImportError:
    pass

try:
    from anthropic import AsyncAnthropic
except ImportError:
    pass


class LLMService:
    def __init__(
        self,
        settings_path: str = "exmemo_tools_settings_2026-02-19.json",
        model_name: Optional[str] = None,
    ):
        self.settings_path = settings_path
        self._load_settings()

        self.client = None
        self.provider = "openai"
        self.model_name = model_name or self.settings.get("llmModelName")

        llm_base_url = self.settings.get("llmBaseUrl", "")
        llm_token = self.settings.get("llmToken")

        if (
            "anthropic" in llm_base_url.lower()
            or "minimax" in llm_base_url.lower()
            or (
                self.model_name
                and (
                    "claude" in self.model_name.lower()
                    or "minimax" in self.model_name.lower()
                )
            )
        ):
            if "AsyncAnthropic" in globals():
                self.provider = "anthropic"
                if (
                    "minimax" in llm_base_url.lower()
                    and "anthropic" not in llm_base_url.lower()
                ):
                    llm_base_url = llm_base_url.rstrip("/") + "/anthropic"

                self.client = AsyncAnthropic(api_key=llm_token, base_url=llm_base_url)
            else:
                print("检测到 Anthropic 提供商，但未安装 anthropic 包。")

        if not self.client and "AsyncOpenAI" in globals():
            self.provider = "openai"
            self.client = AsyncOpenAI(api_key=llm_token, base_url=llm_base_url)

        if not self.client:
            raise ImportError("未找到或配置合适的 LLM 客户端。")

    def _load_settings(self):
        if os.path.exists(self.settings_path):
            with open(self.settings_path, "r", encoding="utf-8") as f:
                self.settings = json.load(f)
        else:
            self.settings = {}

    def construct_system_prompt(self) -> str:
        return "You are a helpful assistant capable of analyzing text and extracting structured information. You must return valid JSON only, without any markdown formatting or code blocks."

    def construct_summary_prompt(self, content: str) -> str:
        instructions = []

        desc_field = self.settings.get("metaDescriptionFieldName", "description")
        desc_prompt = self.settings.get("metaDescription", "Summarize the content.")
        instructions.append(f"- '{desc_field}': {desc_prompt}")

        tags_field = self.settings.get("metaTagsFieldName", "tags")
        tags_prompt = self.settings.get("metaTagsPrompt", "Extract tags.")
        instructions.append(
            f"- '{tags_field}': {tags_prompt} (Return as a list of strings)"
        )

        for item in self.settings.get("customMetadata", []):
            if item.get("type") == "prompt":
                key = item.get("key")
                value = item.get("value")
                instructions.append(f"- '{key}': {value}")

        instruction_str = "\n".join(instructions)
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

    def construct_evaluation_prompt(self, articles: List[Dict[str, str]]) -> str:
        articles_json = json.dumps(articles, ensure_ascii=False, indent=2)

        prompt = f"""
你是一位文章价值评估助手。我的核心价值领域包括：
- 金融风控技能（模型、算法、风险管理）
- 创业和领导力
- 金融投资和财富认知
- 写作《AI提升效率》书稿
- 写作《向AI学习》书稿
- 写作《数据挖掘案例》书稿
- 写作《金融风控大全》书稿
- 会作为我的头马俱乐部演讲素材
- 个人心理成长
- 认知提升、心理韧性，自信
- 金融行业资讯动态，金融政策法规

任务：一次性接收几十篇文章含title, description），为每篇输出：
- title
- pre_value_score（1-10，基于领域相关性、实用性、新颖性， 要非常严格的评分，大胆给低分，精力聚焦）
- article_type（从预定义列表选，只选1个）
- pre_value_score_reason（一句话说明价值或排除原因）
标签列表：["旅行","娱乐","灵感创意","方法论","工作思考","投资","健康","摘录","世界观","美食","金融","心理学","个人成长","科技","数据挖掘","AI","人工智能","编程","理财"]

输入JSON格式：[{{"title":"...","description":"..."}}, ...]
输出JSON格式：{{"articles":[{{"title":"...","pre_value_score":5,"article_type":人工智能","pre_value_score_reason":"..."}}, ...]}}

规则：
1. 仅输出JSON，无额外文字。
2. 无关文章pre_value_score=1，原因简明。
3. 标签严格从列表选择。
4. 确保JSON有效。

输入文章列表：
{articles_json}
"""
        return prompt

    async def _call_llm(self, prompt: str) -> str:
        result_content = ""
        if self.provider == "openai":
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": self.construct_system_prompt()},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
            )
            result_content = response.choices[0].message.content
        elif self.provider == "anthropic":
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=4096,
                system=self.construct_system_prompt(),
                messages=[{"role": "user", "content": prompt}],
            )
            if response.content and len(response.content) > 0:
                for block in response.content:
                    if block.type == "text":
                        result_content += block.text
        return result_content

    async def process_content(self, content: str) -> Dict[str, Any]:
        prompt = self.construct_summary_prompt(content)
        result_content = await self._call_llm(prompt)
        return self._parse_json(result_content)

    async def evaluate_articles(self, articles: List[Dict[str, str]]) -> Dict[str, Any]:
        prompt = self.construct_evaluation_prompt(articles)
        result_content = await self._call_llm(prompt)
        return self._parse_json(result_content)

    def _parse_json(self, content: str) -> Dict[str, Any]:
        if not content:
            return {}
        try:
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to clean markdown
            clean_content = content.replace("```json", "").replace("```", "").strip()
            try:
                return json.loads(clean_content)
            except json.JSONDecodeError:
                # Try regex to find the first { and last }
                import re

                match = re.search(r"(\{.*\})", content, re.DOTALL)
                if match:
                    try:
                        return json.loads(match.group(1))
                    except:
                        pass

                print(f"解析 JSON 失败: {content[:100]}...")
                return {}

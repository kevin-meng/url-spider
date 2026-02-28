import os
import logging
from datetime import datetime
import lark_oapi as lark
from lark_oapi.api.bitable.v1 import *
from typing import Dict, Any

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

APP_ID = "cli_a91f65341fb8dcba"
APP_SECRET = "8i0QcsYuRnbGNhF06VZfOCt82OKzwkpA"
APP_TOKEN = "J6o3bXzkTaucTMstG5jc4ZZWnyz"
TABLE_ID = "tblGojo7DpqKTNZu"


def get_client():
    client = lark.Client.builder().app_id(APP_ID).app_secret(APP_SECRET).build()
    return client


def save_article_to_feishu(article: Dict[str, Any]) -> bool:
    try:
        client = get_client()

        publish_time = article.get("publish_time")
        if isinstance(publish_time, str):
            try:
                dt = datetime.strptime(publish_time, "%Y-%m-%d %H:%M:%S")
                date_value = int(dt.timestamp() * 1000)
            except:
                date_value = 0
        elif isinstance(publish_time, int):
            date_value = publish_time * 1000
        else:
            date_value = 0

        score = article.get("socre", "")
        if isinstance(score, str) and score.isdigit():
            score_value = int(score)
        elif isinstance(score, int):
            score_value = score
        else:
            score_value = 0

        fields = {
            "文章标题": article.get("title", ""),
            "文章类型": (
                ", ".join(article.get("article_type", []))
                if isinstance(article.get("article_type"), list)
                else article.get("article_type", "")
            ),
            "来源": article.get("source", ""),
            "日期": date_value,
            "发布时间": article.get("publish_time", ""),
            "评分": score_value,
            "评分原因": article.get("reason", ""),
            "原文链接": (
                {"link": article.get("url", "")} if article.get("url", "") else None
            ),
        }

        request = (
            CreateAppTableRecordRequest.builder()
            .app_token(APP_TOKEN)
            .table_id(TABLE_ID)
            .request_body(AppTableRecord.builder().fields(fields).build())
            .build()
        )

        response = client.bitable.v1.app_table_record.create(request)

        if not response.success():
            logger.error(f"飞书写入失败, code: {response.code}, msg: {response.msg}")
            return False

        logger.info(f"飞书写入成功! Record ID: {response.data.record.record_id}")
        return True

    except Exception as e:
        logger.error(f"飞书写入异常: {e}")
        return False


def save_articles_batch(articles: list) -> Dict[str, int]:
    success_count = 0
    fail_count = 0

    for article in articles:
        if save_article_to_feishu(article):
            success_count += 1
        else:
            fail_count += 1

    logger.info(f"批量写入完成: 成功 {success_count}, 失败 {fail_count}")
    return {"success": success_count, "fail": fail_count}

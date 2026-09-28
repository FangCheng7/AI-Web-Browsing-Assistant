from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from datetime import datetime, timedelta
from collections import Counter
import logging

from database import (
    Base,
    engine,
    ensure_schema,
    SessionLocal
)
from models import BrowseRecord, PageAnalysis
from analysis import (
    build_local_analysis,
    clean_items,
    normalize_ai_analysis,
    normalize_tags_for_analysis,
    parse_list,
    serialize_list
)
from ai import (
    analyze_page,
    analyze_agent_question
)

from config import (
    save_api_key,
    get_api_key,
    get_model,
    has_api_key,
    clear_api_key
)

from time_utils import get_local_day_range_ms


logging.basicConfig(
    level=logging.INFO,
    format=(
        "%(asctime)s %(levelname)s "
        "%(name)s %(message)s"
    )
)


# ==========================================
# 初始化数据库
# ==========================================

Base.metadata.create_all(bind=engine)

ensure_schema()


# ==========================================
# FastAPI
# ==========================================

app = FastAPI(
    title="AI Information Diet Agent",
    version="1.0.0"
)

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ==========================================
# Dashboard 静态页面
# ==========================================

import sys
from pathlib import Path

if getattr(sys, "frozen", False):
    PROJECT_ROOT = Path(sys._MEIPASS)
else:
    PROJECT_ROOT = Path(__file__).resolve().parent.parent

DASHBOARD_DIR = PROJECT_ROOT / "dashboard"

app.mount(
    "/dashboard",
    StaticFiles(directory=str(DASHBOARD_DIR), html=True),
    name="dashboard"
)


# ==========================================
# CORS
# ==========================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==========================================
# 数据模型
# ==========================================

class BrowserStart(BaseModel):

    tabId: int

    url: str

    title: str

    startTime: int


class BrowserFinish(BaseModel):

    browseRecordId: int

    endTime: int


class PageContent(BaseModel):

    title: str

    content: str

    url: str

    browseRecordId: int | None = None


class AgentQuestion(BaseModel):

    question: str


# ==========================================
# 基础工具
# ==========================================

def is_valid_webpage(url: str):

    if not url:

        return False

    return (
        url.startswith("http://")
        or
        url.startswith("https://")
    )


def should_analyze_page(
    title: str,
    content: str,
    url: str
):

    if not is_valid_webpage(url):

        return False


    if not title:

        return False


    blocked_words = [

        "登录",
        "注册",
        "登陆",
        "sign in",
        "sign up",
        "login",
        "register"

    ]


    title_lower = title.lower()
    content_length = len(
        (content or "").strip()
    )


    for word in blocked_words:

        if (
            word.lower() in title_lower
            and content_length < 120
        ):

            return False


    return True


def backfill_pending_analyses():
    db = SessionLocal()

    try:
        analyses = db.query(PageAnalysis).all()

        for analysis in analyses:
            analysis.tags = serialize_list(
                normalize_tags_for_analysis(
                    [
                        analysis.tags,
                        analysis.subcategory,
                        analysis.topics
                    ],
                    analysis.title or "",
                    analysis.summary or "",
                    analysis.url or "",
                    analysis.category or "其他"
                ),
                limit=4
            )

            if not analysis.analysis_source:
                analysis.analysis_source = "ai"

        analyzed_ids = {
            record_id
            for (record_id,) in db.query(
                PageAnalysis.browse_record_id
            ).filter(
                PageAnalysis.browse_record_id.isnot(None)
            ).all()
        }

        records = db.query(
            BrowseRecord
        ).order_by(
            BrowseRecord.id.desc()
        ).limit(500).all()

        for record in records:
            if record.id in analyzed_ids:
                continue

            if not record.title and not record.url:
                continue

            result = build_local_analysis(
                record.title or "",
                "",
                record.url or ""
            )

            db.add(PageAnalysis(
                browse_record_id=record.id,
                url=record.url,
                title=record.title or "无标题",
                category=result["category"],
                subcategory=result["subcategory"],
                topics=serialize_list(result["topics"]),
                tags=serialize_list(result["tags"]),
                summary=result["summary"],
                interest=result["interest"],
                importance=result["importance"],
                analysis_source="local",
                created_at=(
                    record.start_time
                    or int(datetime.now().timestamp() * 1000)
                )
            ))

        db.commit()

    except Exception as error:
        db.rollback()
        print(f"补充分类数据失败：{error}")

    finally:
        db.close()


backfill_pending_analyses()


# ==========================================
# 根路由
# ==========================================

@app.get("/")
def root():

    return {

        "success": True,

        "message":
            "AI Information Diet Agent API",

        "status":
            "running"

    }



# ==========================================
# 浏览记录：开始
# ==========================================

@app.post("/api/browse/start")
def browse_start(data: BrowserStart):

    db = SessionLocal()

    try:

        # 防止同一个 tab + URL
        # 在极短时间内重复创建记录

        existing = db.query(
            BrowseRecord
        ).filter(
            BrowseRecord.tab_id == data.tabId,
            BrowseRecord.url == data.url,
            BrowseRecord.end_time.is_(None)
        ).order_by(
            BrowseRecord.id.desc()
        ).first()


        if existing:

            return {

                "success": True,

                "recorded": False,

                "browse_record_id":
                    existing.id,

                "message":
                    "当前页面已经存在记录"

            }


        record = BrowseRecord(

            tab_id=data.tabId,

            url=data.url,

            title=data.title,

            start_time=data.startTime,

            end_time=None,

            duration=None

        )


        db.add(record)

        db.commit()

        db.refresh(record)


        return {

            "success": True,

            "recorded": True,

            "browse_record_id":
                record.id

        }


    finally:

        db.close()


# ==========================================
# 浏览记录：结束
# ==========================================

@app.post("/api/browse/finish")
def browse_finish(data: BrowserFinish):

    db = SessionLocal()

    try:

        record = db.query(
            BrowseRecord
        ).filter(
            BrowseRecord.id
            == data.browseRecordId
        ).first()


        if not record:

            return {

                "success": False,

                "message":
                    "浏览记录不存在"

            }


        record.end_time = data.endTime


        if record.start_time:

            record.duration = max(

                0,

                data.endTime
                - record.start_time

            )


        db.commit()


        return {

            "success": True,

            "browse_record_id":
                record.id,

            "duration":
                record.duration or 0

        }


    finally:

        db.close()


# ==========================================
# 网页内容 + AI分析
# ==========================================

@app.post("/api/page-content")
def page_content(data: PageContent):

    db = SessionLocal()

    try:

        if not should_analyze_page(
            data.title,
            data.content,
            data.url
        ):

            return {

                "success": True,

                "analyzed": False,

                "message":
                    "网页不满足分析条件"

            }


        content = data.content[:12000]


        # 查找对应的浏览记录

        browse_record = None


        if data.browseRecordId:

            browse_record = db.query(
                BrowseRecord
            ).filter(
                BrowseRecord.id
                == data.browseRecordId
            ).first()


        # 如果存在浏览记录，
        # 确保 URL 对得上

        if browse_record:

            if browse_record.url != data.url:

                return {

                    "success": False,

                    "analyzed": False,

                    "message":
                        "浏览记录与网页 URL 不匹配"

                }


        # 已经由 AI 分析过时不重复请求。
        # 如果之前只是本地基础分类，且现在拿到了更完整正文，
        # 则允许升级为 AI 分析。

        existing = None

        if data.browseRecordId:

            existing = db.query(
                PageAnalysis
            ).filter(
                PageAnalysis.browse_record_id
                == data.browseRecordId
            ).first()


            if (
                existing
                and existing.analysis_source != "local"
            ):

                return {

                    "success": True,

                    "analyzed": False,

                    "message":
                        "该浏览记录已经分析过",

                    "analysis_id":
                        existing.id

                }


        # 优先调用 AI。AI 不可用时使用本地关键词分类，
        # 避免记录长期停留在“未分析”。

        if len(content) >= 120 and has_api_key():

            try:

                result = normalize_ai_analysis(
                    analyze_page(
                        data.title,
                        content,
                        data.url
                    ),
                    data.title,
                    content,
                    data.url
                )

            except Exception as error:

                print(f"AI 网页分析失败，已启用基础分类：{error}")

                result = build_local_analysis(
                    data.title,
                    content,
                    data.url
                )

        else:

            result = build_local_analysis(
                data.title,
                content,
                data.url
            )


        topics = clean_items(
            result.get("topics"),
            limit=8
        )

        tags = clean_items(
            result.get("tags"),
            limit=6
        )


        if existing:

            analysis = existing

        else:

            analysis = PageAnalysis(
                browse_record_id=data.browseRecordId,
                url=data.url,
                title=data.title,
                created_at=int(
                    datetime.now().timestamp()
                    * 1000
                )
            )

            db.add(analysis)


        analysis.category = result.get(
            "category",
            "其他"
        )

        analysis.subcategory = result.get(
            "subcategory",
            ""
        )

        analysis.topics = serialize_list(
            topics,
            limit=8
        )

        analysis.tags = serialize_list(
            tags,
            limit=6
        )

        analysis.summary = result.get(
            "summary",
            ""
        )

        analysis.interest = result.get(
            "interest",
            0
        )

        analysis.importance = result.get(
            "importance",
            0
        )

        analysis.analysis_source = result.get(
            "analysis_source",
            "local"
        )

        db.commit()

        db.refresh(analysis)


        return {

            "success": True,

            "analyzed": True,

            "analysis_id":
                analysis.id,

            "analysis": {

                "category":
                    analysis.category,

                "subcategory":
                    analysis.subcategory,

                "topics":
                    topics,

                "tags":
                    tags,

                "summary":
                    analysis.summary,

                "interest":
                    analysis.interest,

                "importance":
                    analysis.importance,

                "analysis_source":
                    analysis.analysis_source

            }

        }


    finally:

        db.close()


# ==========================================
# 今日基础统计
# ==========================================

@app.get("/api/stats/today")
def get_today_stats():

    db = SessionLocal()

    try:

        today_date, start_timestamp, end_timestamp = (
            get_local_day_range_ms()
        )


        records = db.query(
            BrowseRecord
        ).filter(

            BrowseRecord.start_time
            >= start_timestamp,

            BrowseRecord.start_time
            < end_timestamp

        ).all()


        duration = sum(

            record.duration or 0

            for record in records

        )


        return {

            "date":
                today_date,

            "total_pages":
                len(records),

            "total_minutes":
                round(
                    duration / 1000 / 60,
                    2
                )

        }


    finally:

        db.close()


# ==========================================
# 今日完整统计
# ==========================================

@app.get("/api/stats/today/full")
def get_today_full_stats():

    db = SessionLocal()

    try:

        today_date, start_timestamp, end_timestamp = (
            get_local_day_range_ms()
        )


        records = db.query(
            BrowseRecord
        ).filter(

            BrowseRecord.start_time
            >= start_timestamp,

            BrowseRecord.start_time
            < end_timestamp

        ).all()


        analyses = db.query(
            PageAnalysis
        ).filter(

            PageAnalysis.created_at
            >= start_timestamp,

            PageAnalysis.created_at
            < end_timestamp

        ).all()


        duration = sum(

            record.duration or 0

            for record in records

        )


        interests = [

            a.interest

            for a in analyses

            if a.interest is not None

        ]


        importance = [

            a.importance

            for a in analyses

            if a.importance is not None

        ]


        categories = Counter(

            a.category

            for a in analyses

            if a.category

        )


        category_result = {}


        for category, count in categories.items():

            category_records = [

                a

                for a in analyses

                if a.category == category

            ]


            category_record_ids = [

                a.browse_record_id

                for a in category_records

                if a.browse_record_id

            ]


            category_duration = sum(

                record.duration or 0

                for record in records

                if record.id
                in category_record_ids

            )


            category_result[category] = {

                "count":
                    count,

                "percentage":
                    round(
                        count
                        / len(analyses)
                        * 100,
                        2
                    )
                    if analyses
                    else 0,

                "minutes":
                    round(
                        category_duration
                        / 1000
                        / 60,
                        2
                    )

            }


        topic_counter = Counter()


        for analysis in analyses:

            values = []

            values.extend(
                parse_list(analysis.topics)
            )

            values.extend(
                parse_list(analysis.tags)
            )

            for topic in clean_items(
                values,
                limit=20
            ):

                topic_counter[
                    str(topic)
                ] += 1


        top_topics = [

            {

                "topic":
                    topic,

                "count":
                    count

            }

            for topic, count

            in topic_counter.most_common(10)

        ]


        top_interests = []


        sorted_analyses = sorted(

            analyses,

            key=lambda x:
                x.interest or 0,

            reverse=True

        )


        for analysis in sorted_analyses[:10]:

            top_interests.append({

                "title":
                    analysis.title,

                "interest":
                    analysis.interest,

                "importance":
                    analysis.importance,

                "category":
                    analysis.category,

                "summary":
                    analysis.summary

            })


        return {

            "date":
                today_date,

            "overview": {

                "pages":
                    len(records),

                "minutes":
                    round(
                        duration
                        / 1000
                        / 60,
                        2
                    ),

                "ai_analyses":
                    len(analyses),

                "average_interest":
                    round(
                        sum(interests)
                        / len(interests),
                        1
                    )
                    if interests
                    else 0,

                "average_importance":
                    round(
                        sum(importance)
                        / len(importance),
                        1
                    )
                    if importance
                    else 0

            },

            "categories":
                category_result,

            "top_topics":
                top_topics,

            "top_interests":
                top_interests

        }


    finally:

        db.close()

# ==========================================
# 最近 7 天统计
# ==========================================

@app.get("/api/stats/7days")
def get_7days_stats():

    db = SessionLocal()

    try:

        now = datetime.now()

        days = []


        for i in range(6, -1, -1):

            day = datetime(

                now.year,

                now.month,

                now.day

            ) - timedelta(days=i)


            next_day = day + timedelta(days=1)


            start_timestamp = int(

                day.timestamp() * 1000

            )


            end_timestamp = int(

                next_day.timestamp() * 1000

            )


            records = db.query(
                BrowseRecord
            ).filter(

                BrowseRecord.start_time
                >= start_timestamp,

                BrowseRecord.start_time
                < end_timestamp

            ).all()


            analyses = db.query(
                PageAnalysis
            ).filter(

                PageAnalysis.created_at
                >= start_timestamp,

                PageAnalysis.created_at
                < end_timestamp

            ).all()


            duration = sum(

                record.duration or 0

                for record in records

            )


            interests = [

                a.interest

                for a in analyses

                if a.interest is not None

            ]


            importance = [

                a.importance

                for a in analyses

                if a.importance is not None

            ]


            categories = Counter(

                a.category

                for a in analyses

                if a.category

            )


            days.append({

                "date":
                    day.strftime("%m-%d"),

                "pages":
                    len(records),

                "minutes":
                    round(
                        duration
                        / 1000
                        / 60,
                        2
                    ),

                "ai_analyses":
                    len(analyses),

                "interest":
                    round(
                        sum(interests)
                        / len(interests),
                        1
                    )
                    if interests
                    else 0,

                "importance":
                    round(
                        sum(importance)
                        / len(importance),
                        1
                    )
                    if importance
                    else 0,

                "top_category":
                    categories.most_common(1)[0][0]
                    if categories
                    else "暂无"

            })


        return {

            "days":
                days

        }


    finally:

        db.close()


# ==========================================
# 最近浏览记录
# ==========================================

@app.get("/api/browse/recent")
def get_recent_browse(limit: int = 50):

    db = SessionLocal()

    try:

        records = db.query(
            BrowseRecord
        ).order_by(
            BrowseRecord.start_time.desc()
        ).limit(limit).all()


        result = []


        for record in records:

            analysis = db.query(
                PageAnalysis
            ).filter(

                PageAnalysis.browse_record_id
                == record.id

            ).first()


            result.append({

                "id":
                    record.id,

                "title":
                    record.title
                    or "无标题",

                "url":
                    record.url,

                "duration":
                    round(
                        (record.duration or 0)
                        / 1000,
                        1
                    ),

                "start_time":
                    record.start_time,

                "category":
                    analysis.category
                    if analysis
                    else "未分析",

                "subcategory":
                    analysis.subcategory
                    if analysis
                    else "",

                "summary":
                    analysis.summary
                    if analysis
                    else "",

                "tags":
                    parse_list(analysis.tags)
                    if analysis
                    else [],

                "interest":
                    analysis.interest
                    if analysis
                    else None,

                "importance":
                    analysis.importance
                    if analysis
                    else None,

                "analysis_source":
                    analysis.analysis_source
                    if analysis
                    else None

            })


        return {

            "records":
                result

        }


    finally:

        db.close()


# ==========================================
# AI Agent
# ==========================================

@app.post("/api/agent/chat")
def agent_chat(data: AgentQuestion):
    try:
        from agent_tools import get_enabled_tools

        result = analyze_agent_question(
            data.question,
            tools=get_enabled_tools()
        )

        return {
            "success": True,
            "question": data.question,
            "answer": result.get(
                "answer",
                "暂时无法生成回答。"
            ),
            "execution_steps": result.get(
                "execution_steps",
                []
            ),
            "tool_rounds": result.get(
                "tool_rounds",
                0
            )
        }

    except Exception as e:
        return {
            "success": False,
            "question": data.question,
            "answer": "AI Agent 暂时无法完成分析。",
            "execution_steps": [],
            "error": str(e)
        }



# =====================================================
# API 设置
# =====================================================

class ApiKeyRequest(BaseModel):
    api_key: str


@app.get("/api/settings")
def get_settings():

    return {
        "provider": "DeepSeek",
        "configured": has_api_key()
    }


@app.post("/api/settings/api-key")
def update_api_key(data: ApiKeyRequest):

    try:

        save_api_key(data.api_key)

        return {
            "success": True,
            "message": "API Key 保存成功"
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


@app.delete("/api/settings/api-key")
def delete_api_key():

    try:

        clear_api_key()

        return {
            "success": True,
            "message": "API Key 已删除"
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }


@app.post("/api/settings/test")
def test_api_connection():

    try:

        from ai import get_client

        client = get_client()

        response = client.chat.completions.create(
            model=get_model(),
            messages=[
                {
                    "role": "user",
                    "content": "请只回复：连接成功"
                }
            ],
            max_tokens=20,
            stream=False
        )

        return {
            "success": True,
            "message": "DeepSeek API 连接成功"
        }

    except Exception as e:

        return {
            "success": False,
            "error": str(e)
        }

# ==========================================
# 启动信息
# ==========================================


@app.get("/api/health")
def health_check():

    return {

        "success":
            True,

        "status":
            "ok",

        "service":
            "AI Information Diet Agent"

    }

    # =====================================================
# 每日报告
# =====================================================

@app.get("/api/report/today")
def get_today_report():

    db = SessionLocal()

    try:

        from collections import Counter

        report_date, today_start, today_end = (
            get_local_day_range_ms()
        )

        records = db.query(
            BrowseRecord
        ).filter(
            BrowseRecord.start_time >= today_start,
            BrowseRecord.start_time < today_end
        ).order_by(
            BrowseRecord.start_time.desc()
        ).all()

        if not records:
            return {
                "success": True,
                "has_data": False,
                "report": None,
                "stats": {
                    "pages": 0,
                    "minutes": 0,
                    "analyses": 0
                }
            }

        categories = Counter()

        analyzed_records = []

        total_duration = 0

        for record in records:

            total_duration += (
                record.duration or 0
            )

            analysis = db.query(
                PageAnalysis
            ).filter(
                PageAnalysis.browse_record_id
                == record.id
            ).first()

            if analysis:

                categories[
                    analysis.category
                ] += 1

                analyzed_records.append({

                    "title":
                        record.title or "无标题",

                    "url":
                        record.url,

                    "category":
                        analysis.category,

                    "subcategory":
                        analysis.subcategory,

                    "tags":
                        parse_list(analysis.tags),

                    "summary":
                        analysis.summary,

                    "interest":
                        analysis.interest,

                    "importance":
                        analysis.importance

                })

        # 只给 AI 最近的 30 条
        analyzed_records = analyzed_records[:30]

        # 分类统计
        category_stats = []

        for category, count in categories.most_common():

            category_stats.append({
                "category": category,
                "count": count
            })

        # 构造 AI 输入
        report_data = {

            "date":
                report_date,

            "pages":
                len(records),

            "minutes":
                round(
                    total_duration / 1000 / 60,
                    1
                ),

            "analyses":
                len(analyzed_records),

            "categories":
                category_stats,

            "records":
                analyzed_records

        }

        from ai import generate_daily_report

        report = generate_daily_report(
            report_data
        )

        return {

            "success": True,

            "has_data": True,

            "report": report,

            "stats": {

                "pages":
                    len(records),

                "minutes":
                    round(
                        total_duration
                        / 1000
                        / 60,
                        1
                    ),

                "analyses":
                    len(analyzed_records)

            }

        }

    except Exception as e:

        return {

            "success": False,

            "error":
                str(e)

        }

    finally:

        db.close()

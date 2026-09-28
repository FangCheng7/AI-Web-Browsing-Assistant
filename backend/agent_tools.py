import ast
import time
from collections import Counter
from urllib.parse import urlparse

from database import SessionLocal
from models import BrowseRecord, PageAnalysis
from analysis import TAG_GROUPS, parse_list
from memory import get_memory, save_memory
from time_utils import get_local_day_range_ms


# =====================================================
# 时间工具
# =====================================================

def normalize_timestamp(timestamp):
    """
    将数据库中的时间戳统一转换成 Python 使用的秒时间戳。

    浏览器 JavaScript 通常使用毫秒：
    1750000000000

    Python time 模块通常使用秒：
    1750000000
    """

    if not timestamp:
        return 0

    timestamp = int(timestamp)

    # 13位左右 = 毫秒
    if timestamp > 100000000000:
        return timestamp / 1000

    # 10位左右 = 秒
    return timestamp


def duration_to_seconds(duration):
    """
    数据库 duration 当前使用毫秒。
    转换成秒。
    """

    if not duration:
        return 0

    return float(duration) / 1000


# =====================================================
# 工具1：查询今日信息消费统计
# =====================================================

def get_today_stats():

    db = SessionLocal()

    try:

        today_date, today_start_ms, today_end_ms = (
            get_local_day_range_ms()
        )

        today_start = today_start_ms / 1000
        today_end = today_end_ms / 1000

        records = (
            db.query(BrowseRecord)
            .all()
        )

        today_records = []

        for record in records:

            record_time = normalize_timestamp(
                record.start_time
            )

            if today_start <= record_time < today_end:
                today_records.append(record)

        total_duration_seconds = 0

        category_duration = {}

        for record in today_records:

            duration_seconds = duration_to_seconds(
                record.duration
            )

            total_duration_seconds += (
                duration_seconds
            )

            analysis = (
                db.query(PageAnalysis)
                .filter(
                    PageAnalysis.browse_record_id
                    == record.id
                )
                .first()
            )

            if analysis:

                category = (
                    analysis.category
                    or "其他"
                )

                category_duration[category] = (
                    category_duration.get(
                        category,
                        0
                    )
                    + duration_seconds
                )

        return {

            "date": today_date,

            "total_browsing_seconds":
                round(
                    total_duration_seconds,
                    1
                ),

            "total_browsing_minutes":
                round(
                    total_duration_seconds / 60,
                    1
                ),

            "record_count":
                len(today_records),

            "category_duration_minutes": {

                key: round(
                    value / 60,
                    1
                )

                for key, value
                in category_duration.items()

            }

        }

    finally:

        db.close()


# =====================================================
# 工具2：查询最近7天趋势
# =====================================================

def get_7day_trend():

    db = SessionLocal()

    try:

        now = time.time()

        start_time = now - (
            7 * 86400
        )

        records = (
            db.query(BrowseRecord)
            .all()
        )

        daily_data = {}

        for record in records:

            record_time = normalize_timestamp(
                record.start_time
            )

            if record_time < start_time:
                continue

            date = time.strftime(
                "%Y-%m-%d",
                time.localtime(
                    record_time
                )
            )

            if date not in daily_data:

                daily_data[date] = {
                    "duration": 0,
                    "categories": {}
                }

            duration_seconds = duration_to_seconds(
                record.duration
            )

            daily_data[date][
                "duration"
            ] += duration_seconds

            analysis = (
                db.query(PageAnalysis)
                .filter(
                    PageAnalysis.browse_record_id
                    == record.id
                )
                .first()
            )

            if analysis:

                category = (
                    analysis.category
                    or "其他"
                )

                daily_data[date][
                    "categories"
                ][category] = (
                    daily_data[date][
                        "categories"
                    ].get(
                        category,
                        0
                    )
                    + duration_seconds
                )

        result = []

        for date, data in sorted(
            daily_data.items()
        ):

            result.append({

                "date":
                    date,

                "total_minutes":
                    round(
                        data["duration"] / 60,
                        1
                    ),

                "categories": {

                    key: round(
                        value / 60,
                        1
                    )

                    for key, value
                    in data[
                        "categories"
                    ].items()

                }

            })

        return {

            "period":
                "最近7天",

            "daily_data":
                result

        }

    finally:

        db.close()


# =====================================================
# 工具3：查询最近浏览记录
# =====================================================

def get_recent_browsing(limit=20):

    db = SessionLocal()

    try:

        records = (
            db.query(BrowseRecord)
            .order_by(
                BrowseRecord.start_time.desc()
            )
            .limit(limit)
            .all()
        )

        result = []

        for record in records:

            record_time = normalize_timestamp(
                record.start_time
            )

            item = {

                "title":
                    record.title or "",

                "url":
                    record.url or "",

                "duration_seconds":
                    round(
                        duration_to_seconds(
                            record.duration
                        ),
                        1
                    ),

                "time":
                    time.strftime(
                        "%Y-%m-%d %H:%M",
                        time.localtime(
                            record_time
                        )
                    )

            }

            analysis = (
                db.query(PageAnalysis)
                .filter(
                    PageAnalysis.browse_record_id
                    == record.id
                )
                .first()
            )

            if analysis:

                topics = analysis.topics

                if topics:

                    try:

                        topics = ast.literal_eval(
                            topics
                        )

                    except Exception:

                        pass

                item.update({

                    "category":
                        analysis.category,

                    "subcategory":
                        analysis.subcategory,

                    "topics":
                        topics,

                    "tags":
                        parse_list(analysis.tags),

                    "summary":
                        analysis.summary,

                    "interest":
                        analysis.interest,

                    "importance":
                        analysis.importance

                })

            result.append(item)

        return {

            "count":
                len(result),

            "records":
                result

        }

    finally:

        db.close()


# =====================================================
# 工具4：查询兴趣分类
# =====================================================

def get_category_stats():

    db = SessionLocal()

    try:

        analyses = (
            db.query(PageAnalysis)
            .all()
        )

        categories = {}

        for analysis in analyses:

            category = (
                analysis.category
                or "其他"
            )

            if category not in categories:

                categories[category] = {

                    "count":
                        0,

                    "interest_total":
                        0,

                    "importance_total":
                        0

                }

            categories[category][
                "count"
            ] += 1

            categories[category][
                "interest_total"
            ] += (
                analysis.interest
                or 0
            )

            categories[category][
                "importance_total"
            ] += (
                analysis.importance
                or 0
            )

        result = {}

        for category, data in categories.items():

            count = data["count"]

            if count == 0:
                continue

            result[category] = {

                "page_count":
                    count,

                "average_interest":
                    round(
                        data[
                            "interest_total"
                        ] / count,
                        1
                    ),

                "average_importance":
                    round(
                        data[
                            "importance_total"
                        ] / count,
                        1
                    )

            }

        return {

            "categories":
                result

        }

    finally:

        db.close()


# =====================================================
# 工具5：信息消费集中度分析
# =====================================================

def _clamp_integer(value, default, minimum, maximum):
    try:
        number = int(value)
    except (TypeError, ValueError):
        number = default

    return max(minimum, min(maximum, number))


def _recent_window(days):
    normalized_days = _clamp_integer(
        days,
        7,
        1,
        30
    )

    _, _, end_ms = get_local_day_range_ms()
    start_ms = end_ms - normalized_days * 86400 * 1000

    return normalized_days, start_ms, end_ms


def _analysis_topics(analysis):
    values = []
    values.extend(parse_list(analysis.topics))
    values.extend(parse_list(analysis.tags))

    result = []
    seen = set()

    for value in values:
        topic = str(value or "").strip()
        key = topic.casefold()

        if not topic or key in seen:
            continue

        seen.add(key)
        result.append(topic)

    return result


def _source_hostname(url):
    try:
        return (
            urlparse(url or "").hostname
            or "未知来源"
        ).casefold()
    except Exception:
        return "未知来源"


def analyze_information_bubble(days=7, top_n=5):
    normalized_days, start_ms, end_ms = _recent_window(days)
    normalized_top_n = _clamp_integer(top_n, 5, 1, 20)

    db = SessionLocal()

    try:
        records = db.query(BrowseRecord).filter(
            BrowseRecord.start_time >= start_ms,
            BrowseRecord.start_time < end_ms
        ).order_by(
            BrowseRecord.start_time.desc()
        ).all()

        record_ids = [record.id for record in records]

        analyses = []

        if record_ids:
            analyses = db.query(PageAnalysis).filter(
                PageAnalysis.browse_record_id.in_(record_ids)
            ).all()

        analysis_by_record = {
            analysis.browse_record_id: analysis
            for analysis in analyses
            if analysis.browse_record_id is not None
        }

        category_counts = Counter()
        topic_counts = Counter()
        source_counts = Counter()

        for record in records:
            source_counts[
                _source_hostname(record.url)
            ] += 1

            analysis = analysis_by_record.get(record.id)

            if not analysis:
                continue

            category = analysis.category or "其他"
            category_counts[category] += 1

            for topic in _analysis_topics(analysis):
                topic_counts[topic] += 1

        analyzed_pages = sum(category_counts.values())

        category_distribution = []

        for category, count in category_counts.most_common():
            category_distribution.append({
                "category": category,
                "page_count": count,
                "share_percentage": (
                    round(
                        count / analyzed_pages * 100,
                        1
                    )
                    if analyzed_pages
                    else 0
                )
            })

        top_topics = [
            {
                "topic": topic,
                "count": count,
                "share_percentage": (
                    round(
                        count / analyzed_pages * 100,
                        1
                    )
                    if analyzed_pages
                    else 0
                )
            }
            for topic, count
            in topic_counts.most_common(
                normalized_top_n
            )
        ]

        repeated_topics = [
            {
                "topic": topic,
                "count": count
            }
            for topic, count
            in topic_counts.most_common()
            if count >= 2
        ][:normalized_top_n]

        category_shares = [
            count / analyzed_pages
            for count in category_counts.values()
        ] if analyzed_pages else []

        hhi = sum(
            share * share
            for share in category_shares
        )

        category_count = len(category_shares)

        normalized_hhi = (
            (hhi - (1 / category_count))
            / (1 - (1 / category_count))
            if category_count > 1
            else (1.0 if category_count == 1 else 0.0)
        )

        dominant_category = (
            category_counts.most_common(1)[0]
            if category_counts
            else (None, 0)
        )

        all_categories = list(TAG_GROUPS.keys())
        expected_share = (
            100 / len(all_categories)
            if all_categories
            else 0
        )

        underrepresented_categories = []

        for category in all_categories:
            count = category_counts.get(category, 0)
            share = (
                count / analyzed_pages * 100
                if analyzed_pages
                else 0
            )

            if share < expected_share:
                underrepresented_categories.append({
                    "category": category,
                    "page_count": count,
                    "share_percentage": round(share, 1),
                    "uniform_expected_percentage": round(
                        expected_share,
                        1
                    )
                })

        underrepresented_categories.sort(
            key=lambda item: (
                item["page_count"],
                -all_categories.index(item["category"])
            )
        )

        historical_topic_counts = Counter()
        historical_last_seen = {}

        for analysis in db.query(PageAnalysis).all():
            for topic in _analysis_topics(analysis):
                historical_topic_counts[topic] += 1
                historical_last_seen[topic] = max(
                    historical_last_seen.get(topic, 0),
                    analysis.created_at or 0
                )

        recent_topic_limit = max(
            1,
            int(analyzed_pages * 0.1)
        )

        underrepresented_topics = []

        for topic, historical_count in historical_topic_counts.items():
            recent_count = topic_counts.get(topic, 0)

            if recent_count >= recent_topic_limit:
                continue

            underrepresented_topics.append({
                "topic": topic,
                "recent_count": recent_count,
                "historical_count": historical_count,
                "last_seen_at": historical_last_seen.get(topic)
            })

        underrepresented_topics.sort(
            key=lambda item: (
                item["recent_count"],
                -item["historical_count"]
            )
        )

        source_distribution = [
            {
                "source": source,
                "page_count": count,
                "share_percentage": (
                    round(
                        count / len(records) * 100,
                        1
                    )
                    if records
                    else 0
                )
            }
            for source, count
            in source_counts.most_common(
                normalized_top_n
            )
        ]

        top_source_share = (
            source_distribution[0]["share_percentage"]
            if source_distribution
            else 0
        )

        caveats = []

        if len(records) < 5:
            caveats.append("最近浏览样本少于5条，统计结果稳定性有限")

        if analyzed_pages < len(records):
            caveats.append(
                f"有 {len(records) - analyzed_pages} 条记录尚无分类结果"
            )

        return {
            "period": f"{normalized_days}d",
            "window": {
                "start_ms": start_ms,
                "end_ms": end_ms
            },
            "status": (
                "insufficient_data"
                if not records or not analyzed_pages
                else "ok"
            ),
            "total_pages": len(records),
            "analyzed_pages": analyzed_pages,
            "category_distribution": category_distribution,
            "top_topics": top_topics,
            "repeated_topics": repeated_topics,
            "concentration": {
                "dominant_category": dominant_category[0],
                "dominant_category_share_percentage": round(
                    dominant_category[1] / analyzed_pages * 100,
                    1
                ) if analyzed_pages else 0,
                "category_hhi": round(hhi, 4),
                "normalized_category_hhi": round(
                    max(0.0, min(1.0, normalized_hhi)),
                    4
                ),
                "top_source_share_percentage": top_source_share
            },
            "source_distribution": source_distribution,
            "underrepresented_categories": (
                underrepresented_categories[:normalized_top_n]
            ),
            "underrepresented_topics": (
                underrepresented_topics[:normalized_top_n]
            ),
            "caveats": caveats
        }

    finally:
        db.close()


# =====================================================
# 工具6：主动发现新方向
# =====================================================

def discover_new_topics(limit=3, days=7):
    normalized_limit = _clamp_integer(
        limit,
        3,
        1,
        5
    )

    bubble = analyze_information_bubble(
        days=days,
        top_n=max(normalized_limit, 5)
    )

    top_topics = bubble.get("top_topics", [])
    repeated_topics = bubble.get("repeated_topics", [])
    underrepresented = bubble.get(
        "underrepresented_categories",
        []
    )

    current_interests = [
        {
            "topic": item["topic"],
            "page_count": item["count"],
            "basis": "recent_topic_frequency"
        }
        for item in top_topics[:normalized_limit]
    ]

    overexposed_topics = [
        {
            "topic": item["topic"],
            "page_count": item["count"],
            "basis": "repeated_recent_topic"
        }
        for item in repeated_topics[:normalized_limit]
    ]

    dominant_category = (
        bubble.get("concentration", {})
        .get("dominant_category")
    )

    if dominant_category:
        dominant_page_count = next(
            (
                item["page_count"]
                for item in bubble.get(
                    "category_distribution",
                    []
                )
                if item["category"] == dominant_category
            ),
            0
        )

        overexposed_topics.append({
            "topic": dominant_category,
            "page_count": dominant_page_count,
            "share_percentage": bubble.get(
                "concentration", {}
            ).get(
                "dominant_category_share_percentage",
                0
            ),
            "basis": "dominant_category_share"
        })

    anchors = [
        item["topic"]
        for item in top_topics[:3]
    ]

    if not anchors and dominant_category:
        anchors = [dominant_category]

    suggested_directions = []

    for index, category in enumerate(
        underrepresented[:normalized_limit]
    ):
        target_category = category["category"]

        if not anchors:
            break

        anchor = anchors[index % len(anchors)]

        if target_category in {
            dominant_category,
            "其他"
        }:
            continue

        suggested_directions.append({
            "direction": f"{anchor} × {target_category}",
            "anchor_topic": anchor,
            "target_category": target_category,
            "basis": {
                "anchor_recent_count": next(
                    (
                        item["count"]
                        for item in top_topics
                        if item["topic"] == anchor
                    ),
                    0
                ),
                "target_recent_pages": category["page_count"]
            },
            "exploration_keywords": [
                anchor,
                target_category,
                "实践案例",
                "基础知识"
            ],
            "confidence": (
                "low"
                if bubble.get("total_pages", 0) < 5
                else "medium"
            )
        })

        if len(suggested_directions) >= normalized_limit:
            break

    return {
        "period": bubble.get("period"),
        "status": (
            "ok"
            if suggested_directions
            else "insufficient_data"
        ),
        "current_interests": current_interests,
        "overexposed_topics": overexposed_topics,
        "underexplored_categories": underrepresented,
        "suggested_directions": suggested_directions,
        "message": (
            ""
            if suggested_directions
            else "最近数据不足，暂时无法生成可靠的探索方向"
        )
    }


# =====================================================
# Tool Calling 定义
# =====================================================

TOOL_REGISTRY = {
    "get_today_stats": {
        "handler": get_today_stats,
        "summary": "查询今日浏览统计",
        "description": (
            "查询用户今天的信息消费统计，包括浏览时长、"
            "浏览记录数量以及各类别浏览时长。"
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "get_7day_trend": {
        "handler": get_7day_trend,
        "summary": "查询最近7天浏览趋势",
        "description": (
            "查询用户最近7天的信息消费趋势，用于分析"
            "用户近期兴趣变化和类别变化。"
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "get_recent_browsing": {
        "handler": get_recent_browsing,
        "summary": "查询最近浏览记录",
        "description": (
            "查询用户最近浏览过的网页以及网页分析结果，"
            "用于回答用户最近看了什么。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "返回多少条记录，建议1到30。",
                    "minimum": 1,
                    "maximum": 30
                }
            },
            "required": []
        }
    },
    "get_category_stats": {
        "handler": get_category_stats,
        "summary": "查询兴趣分类统计",
        "description": (
            "查询用户全部网页分析结果的兴趣分类统计，"
            "包括各类别数量、平均兴趣程度和平均信息价值。"
        ),
        "parameters": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    "analyze_information_bubble": {
        "handler": analyze_information_bubble,
        "summary": "分析信息消费集中度",
        "description": (
            "基于最近浏览数据计算类别分布、高频主题、"
            "重复主题、集中度指标和较少涉及的方向。"
            "只返回客观统计，不判断用户是否一定陷入信息茧房。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "days": {
                    "type": "integer",
                    "description": "统计最近多少天，默认7天。",
                    "minimum": 1,
                    "maximum": 30
                },
                "top_n": {
                    "type": "integer",
                    "description": "每类列表返回多少项，默认5。",
                    "minimum": 1,
                    "maximum": 20
                }
            },
            "required": []
        }
    },
    "discover_new_topics": {
        "handler": discover_new_topics,
        "summary": "发现潜在新方向",
        "description": (
            "根据真实浏览记录中的已有主题和未充分覆盖的类别，"
            "生成数据驱动的候选探索方向和关键词。"
            "该工具不访问互联网，不提供最新文章或链接。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "建议方向数量，默认3。",
                    "minimum": 1,
                    "maximum": 5
                },
                "days": {
                    "type": "integer",
                    "description": "参考最近多少天，默认7天。",
                    "minimum": 1,
                    "maximum": 30
                }
            },
            "required": []
        }
    },
    "save_memory": {
        "handler": save_memory,
        "summary": "保存长期偏好",
        "description": (
            "仅在用户明确要求记住，或明确表达长期兴趣、偏好、"
            "目标、要求时保存。不要保存普通浏览记录或敏感个人信息。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "需要长期保存的简洁内容。"
                },
                "memory_type": {
                    "type": "string",
                    "description": "记忆类型。",
                    "enum": [
                        "interest",
                        "preference",
                        "goal",
                        "requirement"
                    ]
                }
            },
            "required": ["content"]
        }
    },
    "get_memory": {
        "handler": get_memory,
        "summary": "读取长期偏好",
        "description": (
            "读取用户明确保存的长期兴趣、偏好、目标或要求。"
            "没有记录时返回空列表。"
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "limit": {
                    "type": "integer",
                    "description": "最多返回多少条，默认20。",
                    "minimum": 1,
                    "maximum": 50
                },
                "memory_type": {
                    "type": "string",
                    "description": "可选，仅读取指定类型。",
                    "enum": [
                        "interest",
                        "preference",
                        "goal",
                        "requirement"
                    ]
                }
            },
            "required": []
        }
    }
}


def get_tool_schema(tool_name):
    entry = TOOL_REGISTRY.get(tool_name)

    if not entry:
        return None

    return {
        "name": tool_name,
        "description": entry["description"],
        "parameters": entry["parameters"]
    }


def get_tool_summary(tool_name):
    entry = TOOL_REGISTRY.get(tool_name)

    if not entry:
        return "执行未知工具"

    return entry["summary"]


def get_enabled_tools():
    return [
        {
            "type": "function",
            "function": get_tool_schema(tool_name)
        }
        for tool_name in TOOL_REGISTRY
    ]


TOOLS = [
    {
        "type": "function",
        "function": get_tool_schema(tool_name)
    }
    for tool_name in TOOL_REGISTRY
]


# =====================================================
# 执行工具
# =====================================================

def _tool_error(tool_name, error_type, message):
    return {
        "success": False,
        "error": {
            "type": error_type,
            "tool": tool_name,
            "message": str(message)
        }
    }


def execute_tool(tool_name, arguments=None):
    entry = TOOL_REGISTRY.get(tool_name)

    if not entry:
        return _tool_error(
            tool_name,
            "unknown_tool",
            f"未知工具：{tool_name}"
        )

    if arguments is None:
        arguments = {}

    if not isinstance(arguments, dict):
        return _tool_error(
            tool_name,
            "invalid_arguments",
            "工具参数必须是 JSON 对象"
        )

    try:
        result = entry["handler"](**arguments)

    except TypeError as error:
        return _tool_error(
            tool_name,
            "invalid_arguments",
            error
        )

    except Exception as error:
        return _tool_error(
            tool_name,
            "tool_execution_error",
            error
        )

    if not isinstance(result, dict):
        return {
            "result": result
        }

    return result

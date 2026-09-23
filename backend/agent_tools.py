import ast
import time

from database import SessionLocal
from models import BrowseRecord, PageAnalysis


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

        now = time.time()

        # 今天 00:00
        local_now = time.localtime(now)

        today_start = time.mktime((
            local_now.tm_year,
            local_now.tm_mon,
            local_now.tm_mday,
            0,
            0,
            0,
            0,
            0,
            -1
        ))

        records = (
            db.query(BrowseRecord)
            .all()
        )

        today_records = []

        for record in records:

            record_time = normalize_timestamp(
                record.start_time
            )

            if record_time >= today_start:
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

            "date": time.strftime(
                "%Y-%m-%d"
            ),

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
# Tool Calling 定义
# =====================================================

TOOLS = [

    {
        "type": "function",

        "function": {

            "name":
                "get_today_stats",

            "description":
                "查询用户今天的信息消费统计，包括浏览时长、浏览记录数量以及各类别浏览时长。",

            "parameters": {

                "type":
                    "object",

                "properties":
                    {},

                "required":
                    []

            }

        }

    },

    {
        "type": "function",

        "function": {

            "name":
                "get_7day_trend",

            "description":
                "查询用户最近7天的信息消费趋势，用于分析用户近期兴趣变化和类别变化。",

            "parameters": {

                "type":
                    "object",

                "properties":
                    {},

                "required":
                    []

            }

        }

    },

    {
        "type": "function",

        "function": {

            "name":
                "get_recent_browsing",

            "description":
                "查询用户最近浏览过的网页以及网页分析结果，用于回答用户最近看了什么。",

            "parameters": {

                "type":
                    "object",

                "properties": {

                    "limit": {

                        "type":
                            "integer",

                        "description":
                            "返回多少条记录，建议1到30。",

                        "minimum":
                            1,

                        "maximum":
                            30

                    }

                },

                "required":
                    []

            }

        }

    },

    {
        "type": "function",

        "function": {

            "name":
                "get_category_stats",

            "description":
                "查询用户全部网页分析结果的兴趣分类统计，包括各类别数量、平均兴趣程度和平均信息价值。",

            "parameters": {

                "type":
                    "object",

                "properties":
                    {},

                "required":
                    []

            }

        }

    }

]


# =====================================================
# 执行工具
# =====================================================

def execute_tool(
    tool_name,
    arguments
):

    if tool_name == "get_today_stats":

        return get_today_stats()

    if tool_name == "get_7day_trend":

        return get_7day_trend()

    if tool_name == "get_recent_browsing":

        limit = arguments.get(
            "limit",
            20
        )

        return get_recent_browsing(
            limit
        )

    if tool_name == "get_category_stats":

        return get_category_stats()

    return {

        "error":
            f"未知工具：{tool_name}"

    }
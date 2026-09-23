import json

from openai import OpenAI
from config import get_api_key


def get_client():
    api_key = get_api_key()

    if not api_key:
        raise ValueError(
            "尚未配置 DeepSeek API Key，请前往设置页面配置。"
        )

    return OpenAI(
        api_key=api_key,
        base_url="https://api.deepseek.com"
    )


def analyze_page(title, content):

    prompt = f"""
你是一个个人信息消费分析助手。

请分析下面这个网页。

网页标题：
{title}

网页正文：
{content}

请判断这个网页主要属于什么内容，以及用户可能从中获得什么信息。

请严格返回 JSON。

JSON 格式：

{{
    "category": "类别",
    "subcategory": "细分类别",
    "topics": ["主题1", "主题2"],
    "summary": "一句话总结",
    "interest": 0,
    "importance": 0
}}

category 只能选择：

AI科技
商业创业
财经
社会
娱乐
游戏
教育
生活
体育
其他

interest 是对这个内容作为用户兴趣的相关程度，范围 0-100。

importance 是这个内容的信息价值程度，范围 0-100。

不要输出 JSON 以外的内容。
"""

    client = get_client()

    response = client.chat.completions.create(
        model="deepseek-flash",
        messages=[
            {
                "role": "system",
                "content": "你是一个严谨的个人信息消费分析助手。请使用 JSON 格式回答。"
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        response_format={
            "type": "json_object"
        },
        stream=False
    )

    result = response.choices[0].message.content

    return json.loads(result)


def analyze_agent_question(
    prompt,
    tools=None
):

    client = get_client()

    messages = [

        {
            "role": "system",
            "content":
                """
你是一个个人信息消费分析 Agent。

你可以使用工具查询用户真实的信息消费数据。

你必须遵守：

1. 涉及今天的数据时，优先调用今日统计工具。
2. 涉及最近一周趋势时，调用7天趋势工具。
3. 涉及“最近看了什么”时，调用最近浏览工具。
4. 涉及兴趣分类时，调用分类统计工具。
5. 不要编造数据库中不存在的数据。
6. 如果工具返回的数据不足，要明确说明。
7. 工具返回的数据是真实数据，应优先于猜测。
8. 最终使用自然、清晰的中文回答。

你可以根据用户问题选择一个或多个工具。
"""
        },

        {
            "role": "user",
            "content": prompt
        }

    ]

    while True:

        response = client.chat.completions.create(

            model="deepseek-flash",

            messages=messages,

            tools=tools,

            tool_choice="auto",

            stream=False
        )

        message = (
            response
            .choices[0]
            .message
        )

        # 没有工具调用
        if not message.tool_calls:

            return (
                message.content
                or "暂时无法生成回答。"
            )

        # 保存 AI 的工具调用请求
        messages.append(
            message
        )

        from agent_tools import execute_tool

        for tool_call in message.tool_calls:

            tool_name = (
                tool_call
                .function
                .name
            )

            try:

                arguments = json.loads(
                    tool_call
                    .function
                    .arguments
                    or "{}"
                )

            except:

                arguments = {}

            tool_result = execute_tool(
                tool_name,
                arguments
            )

            messages.append({

                "role": "tool",

                "tool_call_id":
                    tool_call.id,

                "content":
                    json.dumps(
                        tool_result,
                        ensure_ascii=False
                    )

            })

# =====================================================
# 每日报告生成
# =====================================================

def generate_daily_report(data):

    client = get_client()

    prompt = f"""
你是一个个人信息消费分析 Agent。

请根据用户今天真实的浏览数据，
生成一份简洁但有洞察力的「今日信息消费报告」。

必须严格基于提供的数据。

不要编造用户没有浏览过的网站、
主题、兴趣或行为。

如果数据不足，要明确说明。

用户今天的数据：

{json.dumps(
    data,
    ensure_ascii=False,
    indent=2
)}

请严格返回 JSON：

{{
    "overview": "今天的信息消费总体概况，2-3句话",

    "focus": [
        {{
            "topic": "主要关注方向",
            "description": "为什么认为用户今天关注这个方向"
        }}
    ],

    "structure": "对今天信息消费结构的简短分析",

    "highlights": [
        {{
            "title": "值得关注的内容标题",
            "reason": "为什么值得关注"
        }}
    ],

    "insight": "AI 对今天信息消费行为的总结，2-4句话"
}}

要求：

1. focus 最多 3 个。
2. highlights 最多 5 个。
3. 不要夸大。
4. 不要进行心理诊断。
5. 不要把单次浏览直接判断成长期兴趣。
6. 如果只有少量数据，要明确说明样本较少。
7. 使用自然、简洁的中文。
8. 不要输出 JSON 以外的内容。
"""

    response = client.chat.completions.create(

        model="deepseek-flash",

        messages=[

            {
                "role": "system",
                "content":
                    "你是一个严谨的个人信息消费分析助手。"
            },

            {
                "role": "user",
                "content": prompt
            }

        ],

        response_format={
            "type": "json_object"
        },

        stream=False
    )

    result = response.choices[0].message.content

    return json.loads(result)
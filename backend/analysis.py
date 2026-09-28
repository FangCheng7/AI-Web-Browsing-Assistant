import ast
import json
import re
from urllib.parse import urlparse


CATEGORY_KEYWORDS = {
    "AI科技": [
        "ai", "人工智能", "大模型", "机器学习", "深度学习", "算法",
        "芯片", "编程", "开发", "程序员", "软件", "开源", "github",
        "python", "java", "javascript", "科技", "云计算", "数据",
        "机器人", "互联网", "网络安全", "数据库"
    ],
    "商业创业": [
        "创业", "公司", "企业", "商业", "融资", "投资", "产品", "运营",
        "品牌", "市场", "营销", "管理", "商业模式", "创业者", "独角兽"
    ],
    "财经": [
        "财经", "经济", "金融", "股票", "基金", "证券", "银行", "货币",
        "利率", "财报", "收入", "房价", "消费", "通胀", "汇率", "上市"
    ],
    "社会": [
        "社会", "新闻", "政策", "政府", "法律", "民生", "国际", "军事",
        "热点", "事件", "城市", "人口", "教育政策", "公共利益"
    ],
    "娱乐": [
        "娱乐", "明星", "电影", "电视剧", "综艺", "音乐", "动漫", "演员",
        "导演", "演唱会", "粉丝", "影视", "八卦"
    ],
    "游戏": [
        "游戏", "玩家", "电竞", "手游", "端游", "主机", "steam", "switch",
        "playstation", "xbox", "攻略", "版本更新", "网游"
    ],
    "教育": [
        "教育", "学习", "课程", "考试", "大学", "学校", "论文", "知识",
        "培训", "考研", "高考", "英语", "教程"
    ],
    "生活": [
        "生活", "健康", "美食", "旅行", "旅游", "家居", "购物", "穿搭",
        "育儿", "养生", "情感", "菜谱", "房产", "汽车"
    ],
    "体育": [
        "体育", "足球", "篮球", "网球", "比赛", "球员", "奥运", "世界杯",
        "nba", "cba", "冠军", "联赛", "运动员"
    ]
}


TAG_GROUPS = {
    "AI科技": {
        "人工智能": [
            "ai", "人工智能", "大模型", "机器学习", "深度学习",
            "生成式", "智能体", "chatgpt"
        ],
        "软件开发": [
            "编程", "开发", "程序员", "软件", "python", "java",
            "javascript", "api", "fastapi", "django", "flask",
            "sqlalchemy", "后端", "前端", "框架", "github"
        ],
        "数据技术": [
            "数据", "数据库", "数据分析", "大数据", "sql", "sqlite"
        ],
        "互联网": [
            "互联网", "网站", "平台", "电商", "社交媒体"
        ],
        "网络安全": [
            "网络安全", "漏洞", "黑客", "密码", "隐私安全"
        ],
        "硬件芯片": [
            "芯片", "处理器", "显卡", "硬件", "机器人"
        ],
        "云计算": [
            "云计算", "云服务", "服务器", "部署", "容器"
        ],
        "开源项目": [
            "开源", "开源项目", "代码仓库"
        ]
    },
    "商业创业": {
        "创业": ["创业", "创业者", "初创"],
        "企业管理": ["管理", "组织", "团队", "公司治理"],
        "商业模式": ["商业模式", "商业", "盈利模式"],
        "产品运营": ["产品", "运营", "增长", "用户增长"],
        "市场营销": ["市场", "营销", "品牌", "广告"],
        "投融资": ["融资", "投资", "股权", "独角兽"]
    },
    "财经": {
        "宏观经济": ["经济", "通胀", "汇率", "gdp", "宏观"],
        "金融市场": ["金融", "证券", "银行", "货币", "利率"],
        "股票投资": ["股票", "股市", "a股", "港股", "美股"],
        "基金理财": ["基金", "理财", "债券", "收益"],
        "房价楼市": ["房价", "楼市", "房地产", "购房"],
        "消费趋势": ["消费", "零售", "价格", "消费趋势"]
    },
    "社会": {
        "社会民生": ["社会", "民生", "人口", "生活问题"],
        "政策法规": ["政策", "政府", "法律", "法规", "规定"],
        "国际时事": ["国际", "外交", "全球", "海外"],
        "公共事件": ["事件", "热点", "突发", "公共事件"],
        "城市生活": ["城市", "交通", "社区", "公共设施"],
        "军事": ["军事", "军队", "武器", "国防"]
    },
    "娱乐": {
        "影视": ["电影", "电视剧", "影视", "导演", "演员"],
        "音乐": ["音乐", "歌曲", "专辑", "演唱会"],
        "明星娱乐": ["明星", "粉丝", "八卦", "艺人"],
        "动漫": ["动漫", "动画", "漫画"],
        "综艺": ["综艺", "节目", "真人秀"]
    },
    "游戏": {
        "游戏资讯": ["游戏", "版本更新", "新游", "网游", "端游"],
        "游戏攻略": ["攻略", "通关", "技巧", "玩法"],
        "电竞": ["电竞", "比赛", "战队", "选手"],
        "手机游戏": ["手游", "手机游戏", "移动游戏"],
        "主机游戏": ["主机", "steam", "switch", "playstation", "xbox"]
    },
    "教育": {
        "学习方法": ["学习", "学习方法", "记忆", "笔记"],
        "考试升学": ["考试", "考研", "高考", "升学"],
        "高等教育": ["大学", "高校", "论文", "学术"],
        "职业培训": ["培训", "课程", "职业技能"],
        "科普知识": ["科普", "知识", "教程", "入门"]
    },
    "生活": {
        "健康养生": ["健康", "养生", "运动健康", "医疗"],
        "美食": ["美食", "菜谱", "烹饪", "餐厅"],
        "旅行": ["旅行", "旅游", "景点", "攻略"],
        "家居": ["家居", "装修", "收纳", "家电"],
        "购物": ["购物", "商品", "优惠", "测评"],
        "穿搭": ["穿搭", "服装", "时尚", "美妆"],
        "育儿": ["育儿", "儿童", "教育孩子", "母婴"],
        "汽车": ["汽车", "车型", "驾驶", "新能源车"],
        "情感": ["情感", "恋爱", "婚姻", "关系"]
    },
    "体育": {
        "足球": ["足球", "世界杯", "欧冠", "中超"],
        "篮球": ["篮球", "nba", "cba"],
        "网球": ["网球", "大满贯"],
        "综合体育": ["体育", "奥运", "田径", "乒乓球"],
        "体育赛事": ["比赛", "联赛", "冠军", "球员"]
    },
    "其他": {
        "综合资讯": ["资讯", "新闻", "热点"],
        "个人兴趣": ["兴趣", "收藏"],
        "收藏内容": ["收藏", "稍后阅读"]
    }
}


TAG_KEYWORDS = {}
TAG_CATEGORY = {}

for category, tag_group in TAG_GROUPS.items():
    for tag, keywords in tag_group.items():
        TAG_KEYWORDS[tag] = keywords
        TAG_CATEGORY[tag] = category


DOMAIN_CATEGORY = {
    "github.com": "AI科技",
    "stackoverflow.com": "AI科技",
    "juejin.cn": "AI科技",
    "csdn.net": "AI科技",
    "arxiv.org": "AI科技",
    "bilibili.com": "娱乐",
    "douban.com": "娱乐",
    "weibo.com": "社会",
    "zhihu.com": "其他",
    "36kr.com": "商业创业",
    "huxiu.com": "商业创业",
    "eastmoney.com": "财经",
    "sina.com.cn": "社会",
    "sohu.com": "社会",
    "163.com": "社会",
    "qq.com": "社会"
}


def clean_items(values, category=None, limit=20):
    if values is None:
        values = []
    elif isinstance(values, str):
        values = [values]
    elif not isinstance(values, (list, tuple, set)):
        values = [values]

    result = []
    seen = set()

    for value in values:
        if value is None:
            continue

        text = str(value).strip().lstrip("#")

        if not text:
            continue

        for part in re.split(r"[,，、;；|/\n]+", text):
            item = re.sub(r"\s+", " ", part).strip()

            if not item or len(item) > 30:
                continue

            key = item.casefold()

            if key in seen:
                continue

            seen.add(key)
            result.append(item)

            if len(result) >= limit:
                break

        if len(result) >= limit:
            break

    if not result and category:
        result.append(str(category))

    return result


def parse_list(value, limit=20):
    if not value:
        return []

    if isinstance(value, (list, tuple, set)):
        return clean_items(value, limit=limit)

    text = str(value).strip()

    try:
        parsed = json.loads(text)
    except Exception:
        try:
            parsed = ast.literal_eval(text)
        except Exception:
            parsed = text

    return clean_items(parsed, limit=limit)


def serialize_list(values, limit=20):
    return json.dumps(
        clean_items(values, limit=limit),
        ensure_ascii=False
    )


def _is_chinese_label(value):
    text = str(value or "").strip()

    return (
        2 <= len(text) <= 8
        and bool(re.search(r"[\u4e00-\u9fff]", text))
        and not re.search(r"https?://|[a-z0-9_.-]{3,}", text, re.I)
    )


def _keyword_present(keyword, text):
    keyword = str(keyword or "").casefold()
    text = str(text or "").casefold()

    if not keyword:
        return False

    if keyword.isascii() and keyword.isalnum():
        pattern = (
            rf"(?<![a-z0-9])"
            rf"{re.escape(keyword)}"
            rf"(?![a-z0-9])"
        )

        return re.search(pattern, text) is not None

    return keyword in text


def _clamp_score(value, default):
    try:
        number = int(float(value))
    except Exception:
        number = default

    return max(0, min(100, number))


def _select_tags(candidates, text, category, limit=4):
    if category == "其他":
        limit = min(limit, 2)

    candidate_values = parse_list(candidates)
    text_lower = str(text or "").casefold()

    scores = {}

    for candidate in candidate_values:
        candidate_text = str(candidate).strip()

        if candidate_text in TAG_KEYWORDS:
            scores[candidate_text] = scores.get(candidate_text, 0) + 8
            continue

        candidate_lower = candidate_text.casefold()

        for tag, keywords in TAG_KEYWORDS.items():
            if any(
                _keyword_present(keyword, candidate_lower)
                for keyword in keywords
            ):
                scores[tag] = scores.get(tag, 0) + 4

    for tag, keywords in TAG_KEYWORDS.items():
        score = 0

        for keyword in keywords:
            if _keyword_present(keyword, text_lower):
                score += 1

        if score:
            scores[tag] = scores.get(tag, 0) + score

        if TAG_CATEGORY.get(tag) == category and score:
            scores[tag] = scores.get(tag, 0) + 1

    ordered_tags = sorted(
        scores,
        key=lambda tag: (
            -scores[tag],
            list(TAG_KEYWORDS).index(tag)
        )
    )

    if category in TAG_GROUPS:
        category_tags = [
            tag
            for tag in ordered_tags
            if TAG_CATEGORY.get(tag) == category
        ]

        if category_tags:
            ordered_tags = category_tags

    result = [
        tag
        for tag in ordered_tags
        if _is_chinese_label(tag)
    ][:limit]

    defaults = list(
        TAG_GROUPS.get(
            category,
            TAG_GROUPS["其他"]
        ).keys()
    )

    for tag in defaults:
        if tag in result:
            continue

        result.append(tag)

        if len(result) >= min(2, limit):
            break

    return result[:limit]


def normalize_tags_for_analysis(
    values,
    title="",
    content="",
    url="",
    category=""
):
    text = "\n".join([
        str(title or ""),
        str(content or ""),
        str(url or "")
    ])

    return _select_tags(
        values,
        text,
        category or "其他",
        limit=4
    )


def build_local_analysis(title, content, url):
    title = str(title or "").strip()
    content = str(content or "").strip()
    url = str(url or "").strip()

    title_lower = title.casefold()
    text_lower = f"{title}\n{content}".casefold()

    scores = {}
    matches = {}

    for category, keywords in CATEGORY_KEYWORDS.items():
        score = 0

        for keyword in keywords:
            if not _keyword_present(keyword, text_lower):
                continue

            score += 4 if _keyword_present(
                keyword,
                title_lower
            ) else 1

        if score:
            scores[category] = score
            matches[category] = True

    hostname = ""

    try:
        hostname = (
            urlparse(url).hostname
            or ""
        ).casefold()
    except Exception:
        hostname = ""

    for domain, category in DOMAIN_CATEGORY.items():
        if (
            hostname == domain
            or hostname.endswith(f".{domain}")
        ):
            scores[category] = scores.get(category, 0) + 3
            matches.setdefault(category, True)

    category = (
        max(scores, key=scores.get)
        if scores
        else "其他"
    )

    tags = normalize_tags_for_analysis(
        [],
        title,
        content,
        url,
        category
    )

    subcategory = tags[0] if tags else category

    if tags:
        summary = (
            f"页面内容主要涉及"
            f"{'、'.join(tags[:3])}，"
            f"已归类为“{category}”。"
        )
    elif content:
        summary = (
            f"根据页面正文进行了基础归类，"
            f"主要属于“{category}”。"
        )
    else:
        summary = (
            f"根据标题和来源网站进行了基础归类，"
            f"主要属于“{category}”。"
        )

    return {
        "category": category,
        "subcategory": subcategory,
        "topics": tags[:4],
        "tags": tags,
        "summary": summary,
        "interest": 55 if matches else 40,
        "importance": 45,
        "analysis_source": "local"
    }


def normalize_ai_analysis(result, title, content, url):
    fallback = build_local_analysis(
        title,
        content,
        url
    )

    if not isinstance(result, dict):
        return fallback

    category = str(
        result.get("category")
        or fallback["category"]
    ).strip()

    if category not in TAG_GROUPS:
        category = fallback["category"]

    tags = normalize_tags_for_analysis(
        result.get("tags"),
        title,
        content,
        url,
        category
    )

    if len(tags) < 2:
        tags = fallback["tags"]

    subcategory = str(
        result.get("subcategory")
        or fallback["subcategory"]
    ).strip()

    if not _is_chinese_label(subcategory):
        subcategory = tags[0] if tags else fallback["subcategory"]

    summary = str(
        result.get("summary")
        or fallback["summary"]
    ).strip()

    return {
        "category": category,
        "subcategory": subcategory,
        "topics": tags[:6],
        "tags": tags,
        "summary": summary,
        "interest": _clamp_score(
            result.get("interest"),
            fallback["interest"]
        ),
        "importance": _clamp_score(
            result.get("importance"),
            fallback["importance"]
        ),
        "analysis_source": "ai"
    }

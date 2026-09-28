const API = "http://127.0.0.1:8000";

let todayData = null;
let weekData = null;
let agentReady = false;
let agentRunning = false;
let currentAgentTask = "";
let currentExecutionPanel = null;


// =====================================================
// 页面启动
// =====================================================

document.addEventListener(
    "DOMContentLoaded",
    () => {

        setupNavigation();

        setupRefresh();

        setupAgent();

        setupSettings();

        loadData();

    }
);


// =====================================================
// 导航
// =====================================================

function setupNavigation() {

    const buttons =
        document.querySelectorAll(
            ".nav-item"
        );


    buttons.forEach(button => {

        button.addEventListener(
            "click",
            () => {

                const page =
                    button.dataset.page;


                switchPage(page);

            }
        );

    });

}


// =====================================================
// 切换页面
// =====================================================

function switchPage(page) {

    const buttons =
        document.querySelectorAll(
            ".nav-item"
        );


    buttons.forEach(button => {

        button.classList.remove(
            "active"
        );


        if (
            button.dataset.page === page
        ) {

            button.classList.add(
                "active"
            );

        }

    });


    document
        .querySelectorAll(".page")
        .forEach(section => {

            section.classList.remove(
                "active"
            );

        });


    const target =
        document.getElementById(
            `page-${page}`
        );


    if (target) {

        target.classList.add(
            "active"
        );

    }


    const titles = {
    overview: "我的信息消费",
    information: "我的浏览",
    report: "每日报告",
    interests: "我的兴趣画像",
    trends: "信息消费趋势",
    agent: "AI Agent",
    settings: "设置"
};


    document.getElementById(
        "page-title"
    ).textContent =
        titles[page] || "AI Information Diet";


    if (page === "information") {

        renderInformation();

    }

    if (page === "report") {
    loadDailyReport();
    }


    if (page === "interests") {

        renderInterestAnalysis();

    }


    if (page === "trends") {

        renderLargeTrend();

    }

    if (page === "settings") {
    loadSettings();
    }

}


// =====================================================
// 刷新按钮
// =====================================================

function setupRefresh() {

    const button =
        document.getElementById(
            "refresh-btn"
        );


    button.addEventListener(
        "click",
        async () => {

            button.disabled = true;

            button.textContent =
                "↻ 正在刷新...";


            await loadData();


            button.disabled = false;

            button.textContent =
                "↻ 刷新数据";

        }
    );

}


// =====================================================
// 加载数据
// =====================================================

async function loadData() {

    try {

        console.log(
            "开始加载数据..."
        );


        const todayResponse =
            await fetch(
                `${API}/api/stats/today/full`
            );


        if (!todayResponse.ok) {

            throw new Error(
                `今日数据接口错误：${todayResponse.status}`
            );

        }


        todayData =
            await todayResponse.json();


        const weekResponse =
            await fetch(
                `${API}/api/stats/7days`
            );


        if (!weekResponse.ok) {

            throw new Error(
                `7天数据接口错误：${weekResponse.status}`
            );

        }


        weekData =
            await weekResponse.json();


        console.log(
            "数据加载完成",
            todayData,
            weekData
        );


        renderToday();

        renderWeek();

        renderInformation();

        renderInterestAnalysis();

        renderLargeTrend();


    } catch (error) {

        console.error(
            "加载数据失败：",
            error
        );


        showError(
            error.message
        );

    }

}


// =====================================================
// 今日数据
// =====================================================

function renderToday() {

    if (!todayData) {
        return;
    }


    const overview =
        todayData.overview;


    document.getElementById(
        "today"
    ).textContent =
        todayData.date;


    document.getElementById(
        "minutes"
    ).textContent =
        overview.minutes ?? 0;


    document.getElementById(
        "pages"
    ).textContent =
        overview.pages ?? 0;


    document.getElementById(
        "analyses"
    ).textContent =
        overview.ai_analyses ?? 0;


    document.getElementById(
        "interest"
    ).textContent =
        overview.average_interest ?? 0;


    renderCategories();

    renderTopics();

    renderInterests();

}


// =====================================================
// 分类
// =====================================================

function renderCategories() {

    const container =
        document.getElementById(
            "categories"
        );


    const categories =
        todayData.categories || {};


    const entries =
        Object.entries(
            categories
        );


    if (!entries.length) {

        container.innerHTML =
            "<div class='empty'>暂无数据</div>";

        return;

    }


    entries.sort(
        (a, b) =>
            b[1].percentage -
            a[1].percentage
    );


    container.innerHTML = "";


    entries.forEach(
        ([name, value]) => {

            const row =
                document.createElement(
                    "div"
                );


            row.className =
                "category-row";


            row.innerHTML = `

                <div class="category-head">

                    <span>
                        ${escapeHTML(name)}
                    </span>

                    <span>
                        ${value.percentage}%
                    </span>

                </div>


                <div class="progress">

                    <div
                        class="progress-inner"
                        style="
                            width:${value.percentage}%
                        "
                    ></div>

                </div>

            `;


            container.appendChild(
                row
            );

        }
    );

}


// =====================================================
// 主题
// =====================================================

function renderTopics() {

    const container =
        document.getElementById(
            "topics"
        );


    const topics =
        todayData.top_topics || [];


    if (!topics.length) {

        container.innerHTML =
            "<div class='empty'>暂无主题</div>";

        return;

    }


    container.innerHTML = "";


    topics.forEach(
        item => {

            const tag =
                document.createElement(
                    "span"
                );


            tag.className =
                "topic";


            tag.textContent =
                `${item.topic} · ${item.count}`;


            container.appendChild(
                tag
            );

        }
    );

}


// =====================================================
// 最近感兴趣内容
// =====================================================

function renderInterests() {

    const container =
        document.getElementById(
            "interests-list"
        );


    const items =
        todayData.top_interests || [];


    if (!items.length) {

        container.innerHTML =
            "<div class='empty'>暂无分析内容</div>";

        return;

    }


    container.innerHTML = "";


    items.forEach(
        item => {

            const div =
                document.createElement(
                    "div"
                );


            div.className =
                "interest-item";


            div.innerHTML = `

                <div class="interest-title">

                    ${escapeHTML(
                        item.title ||
                        "未命名网页"
                    )}

                </div>


                <div class="interest-meta">

                    ${escapeHTML(
                        item.category ||
                        "其他"
                    )}

                    · 兴趣度
                    ${item.interest ?? 0}

                    · 信息价值
                    ${item.importance ?? 0}

                </div>


                <div class="interest-summary">

                    ${escapeHTML(
                        item.summary || ""
                    )}

                </div>

            `;


            container.appendChild(
                div
            );

        }
    );

}


// =====================================================
// 7天趋势
// =====================================================

function renderWeek() {

    const container =
        document.getElementById(
            "trend"
        );


    if (!weekData) {
        return;
    }


    renderTrendTo(
        container
    );

}


// =====================================================
// 大趋势
// =====================================================

function renderLargeTrend() {

    const container =
        document.getElementById(
            "trend-large"
        );


    if (!weekData) {
        return;
    }


    renderLargeTrendDashboard(
        container
    );

}


function renderLargeTrendDashboard(container) {

    const days =
        weekData.days || [];

    if (!days.length) {

        container.innerHTML =
            "<div class='empty'>暂无趋势数据</div>";

        return;
    }

    const summary =
        document.getElementById(
            "trend-summary-grid"
        );

    const volume =
        document.getElementById(
            "trend-volume-chart"
        );

    const quality =
        document.getElementById(
            "trend-quality-chart"
        );

    const categories =
        document.getElementById(
            "trend-category-chart"
        );

    const insights =
        document.getElementById(
            "trend-insight-list"
        );

    const table =
        document.getElementById(
            "trend-data-table"
        );

    renderTrendSummary(
        summary,
        days
    );

    renderTrendVolumeChart(
        volume,
        days
    );

    renderTrendQualityChart(
        quality,
        days
    );

    renderTrendCategoryChart(
        categories,
        days
    );

    renderTrendInsights(
        insights,
        days
    );

    renderTrendTable(
        table,
        days
    );

}


function renderTrendSummary(container, days) {

    if (!container) {
        return;
    }

    const totalPages =
        days.reduce(
            (sum, day) =>
                sum + (Number(day.pages) || 0),
            0
        );

    const totalMinutes =
        days.reduce(
            (sum, day) =>
                sum + (Number(day.minutes) || 0),
            0
        );

    const activeDays =
        days.filter(
            day => (Number(day.pages) || 0) > 0
        ).length;

    const analyzedDays =
        days.filter(
            day =>
                (Number(day.ai_analyses) || 0) > 0
        );

    const averageInterest =
        analyzedDays.length
            ? analyzedDays.reduce(
                (sum, day) =>
                    sum +
                    (Number(day.interest) || 0),
                0
            ) / analyzedDays.length
            : 0;

    const cards = [
        {
            label: "浏览页数",
            value: totalPages,
            unit: "页",
            accent: "pages"
        },
        {
            label: "累计时长",
            value: totalMinutes.toFixed(1),
            unit: "分钟",
            accent: "minutes"
        },
        {
            label: "活跃天数",
            value: activeDays,
            unit: "/ 7 天",
            accent: "days"
        },
        {
            label: "平均兴趣度",
            value: averageInterest.toFixed(1),
            unit: "/ 100",
            accent: "interest"
        }
    ];

    container.innerHTML =
        cards.map(card => `
            <article class="trend-summary-card ${card.accent}">
                <span>${card.label}</span>
                <strong>${card.value}</strong>
                <small>${card.unit}</small>
            </article>
        `).join("");

}


function renderTrendVolumeChart(container, days) {

    if (!container) {
        return;
    }

    const width = 720;
    const height = 250;
    const left = 42;
    const right = 18;
    const top = 22;
    const bottom = 44;
    const innerWidth = width - left - right;
    const innerHeight = height - top - bottom;
    const maxValue = Math.max(
        ...days.map(
            day => Number(day.pages) || 0
        ),
        1
    );
    const slotWidth =
        innerWidth / days.length;
    const barWidth = Math.min(
        42,
        slotWidth * 0.48
    );

    const gridLines = [0, 0.25, 0.5, 0.75, 1]
        .map(ratio => {

            const y =
                top + innerHeight * (1 - ratio);

            const label =
                Math.round(maxValue * ratio);

            return `
                <line
                    x1="${left}"
                    y1="${y}"
                    x2="${width - right}"
                    y2="${y}"
                    class="trend-grid-line"
                />
                <text
                    x="${left - 8}"
                    y="${y + 4}"
                    text-anchor="end"
                    class="trend-axis-label"
                >${label}</text>
            `;

        }).join("");

    const bars = days.map((day, index) => {

        const value =
            Number(day.pages) || 0;

        const barHeight =
            value / maxValue * innerHeight;

        const x =
            left +
            slotWidth * index +
            (slotWidth - barWidth) / 2;

        const y =
            top + innerHeight - barHeight;

        const labelX =
            left + slotWidth * (index + 0.5);

        return `
            <rect
                x="${x}"
                y="${y}"
                width="${barWidth}"
                height="${Math.max(barHeight, 2)}"
                rx="5"
                class="trend-volume-bar"
            />
            <text
                x="${labelX}"
                y="${Math.max(y - 7, top - 5)}"
                text-anchor="middle"
                class="trend-value-label"
            >${value}</text>
            <text
                x="${labelX}"
                y="${height - 14}"
                text-anchor="middle"
                class="trend-axis-label"
            >${escapeHTML(day.date)}</text>
        `;

    }).join("");

    container.innerHTML = `
        <svg
            class="trend-svg"
            viewBox="0 0 ${width} ${height}"
            role="img"
            aria-label="每日浏览页数柱状图"
        >
            ${gridLines}
            ${bars}
        </svg>
    `;

}


function renderTrendQualityChart(container, days) {

    if (!container) {
        return;
    }

    const width = 720;
    const height = 250;
    const left = 42;
    const right = 20;
    const top = 26;
    const bottom = 44;
    const innerWidth = width - left - right;
    const innerHeight = height - top - bottom;
    const slotWidth =
        innerWidth / days.length;

    const buildPoints = metric =>
        days.map((day, index) => {

            const value = Math.max(
                0,
                Math.min(
                    100,
                    Number(day[metric]) || 0
                )
            );

            const x =
                left + slotWidth * (index + 0.5);

            const y =
                top +
                innerHeight *
                (1 - value / 100);

            return {
                x,
                y,
                value,
                date: day.date
            };

        });

    const interestPoints = buildPoints("interest");
    const importancePoints = buildPoints("importance");

    const gridLines = [0, 25, 50, 75, 100]
        .map(value => {

            const y =
                top +
                innerHeight *
                (1 - value / 100);

            return `
                <line
                    x1="${left}"
                    y1="${y}"
                    x2="${width - right}"
                    y2="${y}"
                    class="trend-grid-line"
                />
                <text
                    x="${left - 8}"
                    y="${y + 4}"
                    text-anchor="end"
                    class="trend-axis-label"
                >${value}</text>
            `;

        }).join("");

    const pointsToPolyline = points =>
        points.map(point => `${point.x},${point.y}`).join(" ");

    const dots = points =>
        points.map(point => `
            <circle
                cx="${point.x}"
                cy="${point.y}"
                r="4"
                class="trend-line-dot"
            >
                <title>${point.value}</title>
            </circle>
        `).join("");

    const dateLabels = days.map((day, index) => `
        <text
            x="${left + slotWidth * (index + 0.5)}"
            y="${height - 14}"
            text-anchor="middle"
            class="trend-axis-label"
        >${escapeHTML(day.date)}</text>
    `).join("");

    container.innerHTML = `
        <div class="trend-chart-legend">
            <span><i class="interest"></i>兴趣度</span>
            <span><i class="importance"></i>信息价值</span>
        </div>
        <svg
            class="trend-svg"
            viewBox="0 0 ${width} ${height}"
            role="img"
            aria-label="兴趣度和信息价值折线图"
        >
            ${gridLines}
            <polyline
                points="${pointsToPolyline(interestPoints)}"
                class="trend-line interest"
            />
            <polyline
                points="${pointsToPolyline(importancePoints)}"
                class="trend-line importance"
            />
            ${dots(interestPoints)}
            ${dots(importancePoints)}
            ${dateLabels}
        </svg>
    `;

}


function renderTrendCategoryChart(container, days) {

    if (!container) {
        return;
    }

    const counts = {};

    days.forEach(day => {

        const category =
            day.top_category &&
            day.top_category !== "暂无"
                ? day.top_category
                : "暂无分类";

        counts[category] =
            (counts[category] || 0) + 1;

    });

    const rows =
        Object.entries(counts)
            .sort((a, b) => b[1] - a[1]);

    const maxCount =
        Math.max(
            ...rows.map(row => row[1]),
            1
        );

    container.innerHTML = rows.map(
        ([category, count]) => `
            <div class="trend-category-row">
                <div class="trend-category-head">
                    <strong>${escapeHTML(category)}</strong>
                    <span>${count} 天</span>
                </div>
                <div class="trend-category-track">
                    <span
                        style="width:${count / maxCount * 100}%"
                    ></span>
                </div>
            </div>
        `
    ).join("");

}


function renderTrendInsights(container, days) {

    if (!container) {
        return;
    }

    const activeDays =
        days.filter(
            day => (Number(day.pages) || 0) > 0
        );

    const mostPages =
        days.reduce(
            (best, day) =>
                (Number(day.pages) || 0) >
                (Number(best.pages) || 0)
                    ? day
                    : best,
            days[0]
        );

    const mostMinutes =
        days.reduce(
            (best, day) =>
                (Number(day.minutes) || 0) >
                (Number(best.minutes) || 0)
                    ? day
                    : best,
            days[0]
        );

    const categoryCounts = {};

    activeDays.forEach(day => {

        if (
            day.top_category &&
            day.top_category !== "暂无"
        ) {
            categoryCounts[day.top_category] =
                (categoryCounts[day.top_category] || 0) +
                1;
        }

    });

    const dominantCategory =
        Object.entries(categoryCounts)
            .sort((a, b) => b[1] - a[1])[0];

    const insights = [
        {
            label: "浏览最多的一天",
            value: `${mostPages.date} · ${Number(mostPages.pages) || 0} 页`
        },
        {
            label: "停留最久的一天",
            value: `${mostMinutes.date} · ${Number(mostMinutes.minutes || 0).toFixed(1)} 分钟`
        },
        {
            label: "出现最多的类别",
            value: dominantCategory
                ? `${dominantCategory[0]} · ${dominantCategory[1]} 天`
                : "暂无足够数据"
        },
        {
            label: "活跃记录",
            value: `${activeDays.length} / ${days.length} 天`
        }
    ];

    container.innerHTML = insights.map(
        item => `
            <div class="trend-insight-item">
                <span>${item.label}</span>
                <strong>${escapeHTML(item.value)}</strong>
            </div>
        `
    ).join("");

}


function renderTrendTable(container, days) {

    if (!container) {
        return;
    }

    const rows = days.map(day => `
        <tr>
            <td>${escapeHTML(day.date)}</td>
            <td>${Number(day.pages) || 0}</td>
            <td>${Number(day.minutes || 0).toFixed(1)}</td>
            <td>${Number(day.ai_analyses) || 0}</td>
            <td>${Number(day.interest || 0).toFixed(1)}</td>
            <td>${Number(day.importance || 0).toFixed(1)}</td>
            <td>
                <span class="trend-table-category">
                    ${escapeHTML(day.top_category || "暂无")}
                </span>
            </td>
        </tr>
    `).join("");

    container.innerHTML = `
        <table class="trend-data-table">
            <thead>
                <tr>
                    <th>日期</th>
                    <th>页数</th>
                    <th>时长（分钟）</th>
                    <th>AI 分析</th>
                    <th>兴趣度</th>
                    <th>信息价值</th>
                    <th>主导类别</th>
                </tr>
            </thead>
            <tbody>${rows}</tbody>
        </table>
    `;

}


// =====================================================
// 绘制趋势
// =====================================================

function renderTrendTo(
    container
) {

    const days =
        weekData.days || [];


    if (!days.length) {

        container.innerHTML =
            "<div class='empty'>暂无趋势数据</div>";

        return;

    }


    const max =
        Math.max(
            ...days.map(
                item =>
                    Number(item.minutes) || 0
            ),
            1
        );


    container.innerHTML = "";


    days.forEach(
        day => {

            const minutes =
                Number(day.minutes) || 0;


            const height =
                Math.max(
                    4,
                    minutes /
                    max *
                    150
                );


            const item =
                document.createElement(
                    "div"
                );


            item.className =
                "day";


            item.innerHTML = `

                <div class="day-value">

                    ${minutes}m

                </div>


                <div class="bar-wrap">

                    <div
                        class="bar"
                        style="
                            height:${height}px
                        "
                    ></div>

                </div>


                <div class="day-label">

                    ${escapeHTML(
                        day.date
                    )}

                </div>

            `;


            container.appendChild(
                item
            );

        }
    );

}


// =====================================================
// 信息消费页面
// =====================================================

function formatBrowseDate(timestamp) {

    const value = Number(timestamp);

    if (
        !Number.isFinite(value) ||
        value <= 0
    ) {

        return "日期未知";
    }

    const milliseconds =
        value < 100000000000
            ? value * 1000
            : value;

    const date = new Date(milliseconds);

    if (Number.isNaN(date.getTime())) {

        return "日期未知";
    }

    const pad = number =>
        String(number).padStart(2, "0");

    return (
        `${date.getFullYear()}-` +
        `${pad(date.getMonth() + 1)}-` +
        `${pad(date.getDate())} ` +
        `${pad(date.getHours())}:` +
        `${pad(date.getMinutes())}`
    );
}


async function renderInformation() {

    const container =
        document.getElementById(
            "information-list"
        );

    if (!container) {
        return;
    }

    container.innerHTML =
        "<div class='empty'>正在加载最近浏览记录...</div>";

    try {

        const response =
            await fetch(
                `${API}/api/browse/recent?limit=50`
            );

        if (!response.ok) {
            throw new Error(
                "获取浏览记录失败"
            );
        }

        const data =
            await response.json();

        const records =
            data.records || [];

        if (!records.length) {

            container.innerHTML =
                "<div class='empty'>暂无浏览记录</div>";

            return;
        }

        container.innerHTML =
            records.map(record => {

                const title =
                    record.title ||
                    "无标题";

                const url =
                    record.url ||
                    "";

                const category =
                    record.category ||
                    "待分析";

                const summary =
                    record.summary ||
                    "暂无摘要";

                const tags =
                    Array.isArray(record.tags)
                        ? record.tags
                            .filter(Boolean)
                            .slice(0, 6)
                        : [];

                const analysisSource =
                    record.analysis_source === "local"
                        ? "基础分类"
                        : (
                            record.category
                                ? "AI 分析"
                                : "待分析"
                        );

                const browseDate =
                    formatBrowseDate(
                        record.start_time
                    );

                let hostname = "";

                try {

                    hostname =
                        new URL(url).hostname;

                } catch (error) {

                    hostname = url;
                }

                return `
                    <div class="information-item">

                        <div class="information-main">

                            <div class="information-title">
                                ${escapeHTML(title)}
                            </div>

                            <div class="information-date">
                                浏览时间：${escapeHTML(browseDate)}
                            </div>

                            <div
                                class="information-url"
                                title="${escapeHTML(url)}"
                            >
                                ${escapeHTML(hostname)}
                            </div>

                            ${tags.length ? `
                                <div class="information-tags">
                                    ${tags.map(tag => `
                                        <span class="information-tag">
                                            ${escapeHTML(tag)}
                                        </span>
                                    `).join("")}
                                </div>
                            ` : ""}

                            <div class="information-summary">
                                ${escapeHTML(summary)}
                            </div>

                        </div>

                        <div class="information-meta">

                            <span class="information-category">
                                ${escapeHTML(category)}
                            </span>

                            <span class="information-source">
                                ${escapeHTML(analysisSource)}
                            </span>

                        </div>

                    </div>
                `;

            }).join("");

    } catch (error) {

        console.error(
            "加载信息消费失败：",
            error
        );

        container.innerHTML =
            "<div class='empty'>加载信息消费失败，请检查后端是否运行</div>";
    }
}




// =====================================================
// 兴趣画像
// =====================================================

function renderInterestAnalysis() {

    const container =
        document.getElementById(
            "interest-analysis"
        );


    if (!todayData) {
        return;
    }


    const topics =
        todayData.top_topics || [];


    const overview =
        todayData.overview;


    let html = `

        <div class="profile-box">

            <div class="profile-number">

                ${overview.average_interest}

            </div>

            <div>

                <strong>
                    今日平均兴趣度
                </strong>

                <p>
                    AI 根据你的浏览内容计算出的兴趣相关程度。
                </p >

            </div>

        </div>


        <h3>
            当前主要兴趣
        </h3>

        <div class="topic-container">

    `;


    topics.forEach(
        item => {

            html += `

                <span class="topic">

                    ${escapeHTML(item.topic)}

                    · ${item.count}

                </span>

            `;

        }
    );


    html += `
        </div>
    `;


    container.innerHTML =
        html;

}


// =====================================================
// 错误
// =====================================================

function showError(
    message
) {

    document.getElementById(
        "today"
    ).textContent =
        "连接失败";


    document.getElementById(
        "categories"
    ).innerHTML = `

        <div class="error">

            ❌ ${escapeHTML(message)}

            <br><br>

            请确认：

            <br>

            FastAPI 是否运行在
            127.0.0.1:8000

        </div>

    `;

}


// =====================================================
// HTML 安全
// =====================================================

function escapeHTML(
    value
) {

    return String(value)

        .replaceAll(
            "&",
            "&amp;"
        )

        .replaceAll(
            "<",
            "&lt;"
        )

        .replaceAll(
            ">",
            "&gt;"
        )

        .replaceAll(
            '"',
            "&quot;"
        )

        .replaceAll(
            "'",
            "&#039;"
        );

}

// ===============================
// AI Agent
// ===============================

function setupAgent() {

    const input =
        document.getElementById("agent-input");

    const sendButton =
        document.getElementById("agent-send");

    if (!input || !sendButton) {
        return;
    }

    sendButton.addEventListener(
        "click",
        sendAgentQuestion
    );

    input.addEventListener(
        "keydown",
        function (event) {

            if (
                event.key === "Enter" &&
                !event.shiftKey
            ) {

                event.preventDefault();

                sendAgentQuestion();

            }

        }
    );


    document
        .querySelectorAll("[data-agent-task]")
        .forEach(button => {

            button.addEventListener(
                "click",
                function () {

                    if (
                        agentRunning ||
                        !agentReady
                    ) {
                        return;
                    }

                    startAgentTask(
                        this.dataset.agentTask
                    );

                }
            );

        });

    refreshAgentStatus();

}


function sendAgentQuestion() {

    const input =
        document.getElementById("agent-input");

    if (!input) {
        return;
    }

    startAgentTask(
        input.value.trim()
    );

}


async function refreshAgentStatus() {

    const status =
        document.getElementById("agent-status");

    const statusText =
        document.getElementById("agent-status-text");

    if (!status || !statusText) {
        return;
    }

    try {

        const response =
            await fetch(
                `${API}/api/settings`
            );

        if (!response.ok) {
            throw new Error(
                "Agent 状态接口不可用"
            );
        }

        const data =
            await response.json();

        if (data.configured) {

            agentReady = true;

            status.className =
                "agent-status online";

            statusText.textContent =
                "Agent Online";

        } else {

            agentReady = false;

            status.className =
                "agent-status offline";

            statusText.textContent =
                "未配置 DeepSeek API Key";

        }

    } catch (error) {

        console.error(
            "获取 Agent 状态失败:",
            error
        );

        agentReady = false;

        status.className =
            "agent-status offline";

        statusText.textContent =
            "后端未连接";

    }

    updateAgentControls();

}


function updateAgentControls() {

    const input =
        document.getElementById("agent-input");

    const sendButton =
        document.getElementById("agent-send");

    const enabled =
        agentReady && !agentRunning;

    if (input) {
        input.disabled = !enabled;
    }

    if (sendButton) {
        sendButton.disabled = !enabled;
        sendButton.textContent =
            agentRunning
                ? "执行中..."
                : "执行任务";
    }

    document
        .querySelectorAll(
            "[data-agent-task], .agent-rerun"
        )
        .forEach(button => {
            button.disabled = !enabled;
        });

}


function setAgentTaskState(text, state) {

    const element =
        document.getElementById(
            "agent-task-state"
        );

    if (!element) {
        return;
    }

    element.textContent = text;
    element.className =
        `agent-task-state ${state || ""}`.trim();

}


function setWorkflowPhase(
    phase,
    status,
    detail
) {

    const item =
        document.querySelector(
            `[data-phase="${phase}"]`
        );

    if (!item) {
        return;
    }

    item.className = status;

    const detailElement =
        item.querySelector("small");

    if (detailElement) {
        detailElement.textContent =
            detail || "";
    }

}


function startAgentTask(task) {

    const normalizedTask =
        String(task || "").trim();

    if (
        !normalizedTask ||
        agentRunning ||
        !agentReady
    ) {
        return;
    }

    runAgentTask(normalizedTask);

}


async function runAgentTask(task) {

    const input =
        document.getElementById("agent-input");

    currentAgentTask = task;
    currentExecutionPanel = null;
    agentRunning = true;

    if (input) {
        input.value = "";
    }

    updateAgentControls();
    setAgentTaskState(
        "Agent 正在执行",
        "running"
    );

    addTaskRequest(task);
    resetAgentWorkflow();
    setWorkflowPhase(
        "understand",
        "active",
        "正在理解任务"
    );
    showAgentExecutionPanel();

    let data = null;

    try {

        const response =
            await fetch(
                `${API}/api/agent/chat`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type":
                            "application/json"
                    },
                    body: JSON.stringify({
                        question: task
                    })
                }
            );

        data = await response.json();

        if (!response.ok) {
            throw new Error(
                data.error ||
                `Agent 接口错误：${response.status}`
            );
        }

        renderAgentExecutionSteps(
            data.execution_steps || [],
            data.success !== false
        );

        updateAgentWorkflow(
            data.execution_steps || [],
            data.success !== false
        );

        if (data.success === false) {

            addTaskResult(
                task,
                data.error ||
                data.answer ||
                "Agent 任务执行失败。",
                true
            );

        } else {

            addTaskResult(
                task,
                data.answer ||
                "Agent 没有返回分析结果。",
                false
            );

        }

    } catch (error) {

        console.error(
            "Agent 任务执行失败:",
            error
        );

        renderAgentExecutionSteps([], false);
        updateAgentWorkflow([], false);

        addTaskResult(
            task,
            error.message ||
            "无法连接 Agent。",
            true
        );

    } finally {

        agentRunning = false;
        setAgentTaskState("等待任务", "");
        updateAgentControls();

        if (input && agentReady) {
            input.focus();
        }

    }

}


function resetAgentWorkflow() {

    document
        .querySelectorAll(
            ".agent-workflow-list li"
        )
        .forEach(item => {

            item.className = "pending";

            const detail =
                item.querySelector("small");

            if (detail) {
                detail.textContent =
                    "等待执行";
            }

        });

}


function updateAgentWorkflow(
    steps,
    success
) {

    const tools =
        new Set(
            (steps || []).map(step => step.tool)
        );

    const gatherTools = new Set([
        "get_today_stats",
        "get_7day_trend",
        "get_recent_browsing",
        "get_category_stats",
        "get_memory"
    ]);

    const analyzeTools = new Set([
        "analyze_information_bubble"
    ]);

    const exploreTools = new Set([
        "discover_new_topics"
    ]);

    setWorkflowPhase(
        "understand",
        "done",
        "已完成"
    );

    const phases = [
        [
            "gather",
            gatherTools,
            "已获取数据"
        ],
        [
            "analyze",
            analyzeTools,
            "已完成分析"
        ],
        [
            "explore",
            exploreTools,
            "已生成探索方向"
        ]
    ];

    phases.forEach(
        ([phase, toolSet, doneText]) => {

            const used = [...tools].some(
                tool => toolSet.has(tool)
            );

            setWorkflowPhase(
                phase,
                used
                    ? "done"
                    : (success ? "skipped" : "pending"),
                used
                    ? doneText
                    : (success ? "本次无需调用" : "未执行")
            );

        }
    );

    setWorkflowPhase(
        "result",
        success ? "done" : "pending",
        success ? "任务已完成" : "未完成"
    );

}


function showAgentExecutionPanel() {

    const container =
        document.getElementById("chat-messages");

    if (!container) {
        return;
    }

    const panel =
        document.createElement("div");

    panel.className = "agent-execution-panel";
    panel.setAttribute("aria-live", "polite");
    panel.innerHTML = `
        <div class="agent-execution-header">
            <div>
                <span class="agent-execution-kicker">AGENT RUN</span>
                <strong class="agent-execution-title">Agent 正在执行任务</strong>
            </div>
            <span class="agent-execution-count">规划中</span>
        </div>
        <div class="agent-execution-steps">
            <div class="agent-execution-step active">
                <span class="execution-step-icon">●</span>
                <div>
                    <strong>理解任务</strong>
                    <small>正在决定需要调用的工具</small>
                </div>
            </div>
        </div>
    `;

    currentExecutionPanel = panel;
    container.appendChild(panel);
    scrollAgentChat();

}


function renderAgentExecutionSteps(
    executionSteps,
    success
) {

    const panel = currentExecutionPanel;

    if (!panel) {
        return;
    }

    const title = panel.querySelector(
        ".agent-execution-title"
    );

    const count = panel.querySelector(
        ".agent-execution-count"
    );

    const container = panel.querySelector(
        ".agent-execution-steps"
    );

    if (!title || !count || !container) {
        return;
    }

    const steps =
        Array.isArray(executionSteps)
            ? executionSteps
            : [];

    title.textContent = success
        ? "任务执行记录"
        : "任务执行未完成";

    count.textContent =
        `${steps.length} 步`;

    if (!steps.length) {

        container.innerHTML = `
            <div class="agent-execution-step muted">
                <span class="execution-step-icon">○</span>
                <div>
                    <strong>没有工具调用记录</strong>
                    <small>Agent 未返回 execution_steps</small>
                </div>
            </div>
        `;

        return;
    }

    container.innerHTML =
        steps.map(step => {

            const status =
                step.status === "error"
                    ? "error"
                    : "success";

            const icon =
                status === "error"
                    ? "×"
                    : "✓";

            return `
                <div class="agent-execution-step ${status}">
                    <span class="execution-step-icon">${icon}</span>
                    <div>
                        <strong>
                            ${escapeAgentHTML(
                                describeAgentTool(step.tool)
                            )}
                        </strong>
                        <small>
                            ${escapeAgentHTML(
                                step.tool || ""
                            )}
                        </small>
                    </div>
                </div>
            `;

        }).join("");

    scrollAgentChat();

}


function describeAgentTool(toolName) {

    const labels = {
        get_today_stats: "查询今日浏览",
        get_7day_trend: "分析 7 天趋势",
        get_recent_browsing: "查询最近浏览",
        get_category_stats: "分析内容类别",
        analyze_information_bubble: "分析信息消费结构",
        discover_new_topics: "发现新的兴趣方向",
        save_memory: "保存用户记忆",
        get_memory: "读取用户记忆"
    };

    return labels[toolName] || toolName || "执行工具";

}


function addTaskRequest(task) {

    const container =
        document.getElementById(
            "chat-messages"
        );

    const emptyState =
        document.getElementById(
            "agent-empty-state"
        );

    if (!container) {
        return;
    }

    if (emptyState) {
        emptyState.remove();
    }

    const element =
        document.createElement("div");

    element.className = "task-request";

    element.innerHTML = `
        <div class="task-request-kicker">
            TASK
        </div>
        <div class="task-request-text">
            ${escapeAgentHTML(task)}
        </div>
    `;

    container.appendChild(element);
    scrollAgentChat();

}


function addTaskResult(
    task,
    text,
    isError
) {

    const container =
        document.getElementById(
            "chat-messages"
        );

    if (!container) {
        return;
    }

    const result =
        document.createElement("div");

    result.className = isError
        ? "task-result error"
        : "task-result";

    const statusTitle = isError
        ? "任务未完成"
        : "任务完成 ✓";

    const sectionTitle = isError
        ? "执行说明"
        : "Agent 分析结果";

    result.innerHTML = `
        <div class="task-result-header">
            <div>
                <span class="task-result-kicker">
                    ${isError ? "ERROR" : "COMPLETED"}
                </span>
                <strong>${statusTitle}</strong>
            </div>
            <button class="agent-rerun" type="button">
                重新执行
            </button>
        </div>
        <div class="task-result-section-title">
            ${sectionTitle}
        </div>
        <div class="task-result-answer"></div>
    `;

    result.querySelector(
        ".task-result-answer"
    ).textContent = text;

    result.querySelector(
        ".agent-rerun"
    ).addEventListener(
        "click",
        () => runAgentTask(task)
    );

    container.appendChild(result);
    updateAgentControls();
    scrollAgentChat();

}


function escapeAgentHTML(text) {

    return String(text)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;")
        .replace(/'/g, "&#039;");

}


function scrollAgentChat() {

    const container =
        document.getElementById(
            "chat-messages"
        );

    if (!container) {
        return;
    }

    container.scrollTop =
        container.scrollHeight;

}

// =====================================================
// 设置 / API 配置
// =====================================================

async function loadSettings() {

    const status =
        document.getElementById("api-status");

    if (!status) {
        return;
    }

    try {

        const response =
            await fetch(
                `${API}/api/settings`
            );

        const data =
            await response.json();

        if (data.configured) {

            status.textContent =
                "● API Key 已配置";

            status.className =
                "api-status success";

        } else {

            status.textContent =
                "○ 尚未配置 API Key";

            status.className =
                "api-status warning";
        }

    } catch (error) {

        status.textContent =
            "无法连接后端";

        status.className =
            "api-status error";
    }
}


// =====================================================
// 保存 API Key
// =====================================================

async function saveApiKey() {

    const input =
        document.getElementById(
            "api-key-input"
        );

    const button =
        document.getElementById(
            "api-save"
        );

    const status =
        document.getElementById(
            "api-status"
        );

    const apiKey =
        input.value.trim();

    if (!apiKey) {

        status.textContent =
            "请输入 API Key";

        status.className =
            "api-status error";

        return;
    }

    button.disabled = true;
    button.textContent = "保存中...";

    try {

        const response =
            await fetch(
                `${API}/api/settings/api-key`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        api_key: apiKey
                    })
                }
            );

        const data =
            await response.json();

        if (data.success) {

            input.value = "";

            status.textContent =
                "● API Key 保存成功";

            status.className =
                "api-status success";

        } else {

            status.textContent =
                data.error ||
                "保存失败";

            status.className =
                "api-status error";
        }

    } catch (error) {

        status.textContent =
            "无法连接后端";

        status.className =
            "api-status error";
    }

    button.disabled = false;
    button.textContent = "保存配置";
}


// =====================================================
// 测试 API
// =====================================================

async function testApiConnection() {

    const button =
        document.getElementById(
            "api-test"
        );

    const status =
        document.getElementById(
            "api-status"
        );

    button.disabled = true;
    button.textContent =
        "测试中...";

    status.textContent =
        "正在连接 DeepSeek...";

    status.className =
        "api-status";

    try {

        const response =
            await fetch(
                `${API}/api/settings/test`,
                {
                    method: "POST"
                }
            );

        const data =
            await response.json();

        if (data.success) {

            status.textContent =
                "● DeepSeek API 连接成功";

            status.className =
                "api-status success";

        } else {

            status.textContent =
                "● 连接失败：" +
                (
                    data.error ||
                    "未知错误"
                );

            status.className =
                "api-status error";
        }

    } catch (error) {

        status.textContent =
            "无法连接后端";

        status.className =
            "api-status error";
    }

    button.disabled = false;
    button.textContent =
        "测试连接";
}


// =====================================================
// 删除 API Key
// =====================================================

async function deleteApiKey() {

    const confirmed =
        confirm(
            "确定要删除本机保存的 API Key 吗？"
        );

    if (!confirmed) {
        return;
    }

    const status =
        document.getElementById(
            "api-status"
        );

    try {

        const response =
            await fetch(
                `${API}/api/settings/api-key`,
                {
                    method: "DELETE"
                }
            );

        const data =
            await response.json();

        if (data.success) {

            status.textContent =
                "○ API Key 已删除";

            status.className =
                "api-status warning";

        } else {

            status.textContent =
                data.error ||
                "删除失败";

            status.className =
                "api-status error";
        }

    } catch (error) {

        status.textContent =
            "无法连接后端";

        status.className =
            "api-status error";
    }
}


// =====================================================
// 显示 / 隐藏 API Key
// =====================================================

function toggleApiKey() {

    const input =
        document.getElementById(
            "api-key-input"
        );

    const button =
        document.getElementById(
            "api-key-toggle"
        );

    if (input.type === "password") {

        input.type = "text";

        button.textContent =
            "隐藏";

    } else {

        input.type = "password";

        button.textContent =
            "显示";
    }
}


// =====================================================
// 设置初始化
// =====================================================

function setupSettings() {

    const saveButton =
        document.getElementById(
            "api-save"
        );

    const testButton =
        document.getElementById(
            "api-test"
        );

    const deleteButton =
        document.getElementById(
            "api-delete"
        );

    const toggleButton =
        document.getElementById(
            "api-key-toggle"
        );

    if (saveButton) {

        saveButton.addEventListener(
            "click",
            saveApiKey
        );

    }

    if (testButton) {

        testButton.addEventListener(
            "click",
            testApiConnection
        );

    }

    if (deleteButton) {

        deleteButton.addEventListener(
            "click",
            deleteApiKey
        );

    }

    if (toggleButton) {

        toggleButton.addEventListener(
            "click",
            toggleApiKey
        );

    }
}

/* =====================================================
   每日报告
   ===================================================== */

async function loadDailyReport() {

    const overview =
        document.getElementById(
            "report-overview"
        );

    if (!overview) {
        return;
    }

    overview.textContent =
        "正在生成今天的信息消费报告……";


    try {

        const response =
            await fetch(
                `${API}/api/report/today`
            );

        const data =
            await response.json();


        if (!data.success) {

            throw new Error(
                data.error ||
                "报告生成失败"
            );
        }


        /* 没有数据 */

        if (!data.has_data) {

            document.getElementById(
                "report-description"
            ).textContent =
                "今天还没有足够的浏览数据。";

            document.getElementById(
                "report-overview"
            ).textContent =
                "今天还没有可以分析的信息消费记录。";

            document.getElementById(
                "report-focus"
            ).innerHTML =
                "<div class='report-text'>暂无数据</div>";

            document.getElementById(
                "report-structure"
            ).textContent =
                "暂无数据";

            document.getElementById(
                "report-highlights"
            ).innerHTML =
                "<div class='report-text'>暂无数据</div>";

            document.getElementById(
                "report-insight"
            ).textContent =
                "暂无数据";

            return;
        }


        const report =
            data.report || {};

        const stats =
            data.stats || {};


        /* 统计数据 */

        document.getElementById(
            "report-pages"
        ).textContent =
            stats.pages || 0;


        document.getElementById(
            "report-minutes"
        ).textContent =
            stats.minutes || 0;


        document.getElementById(
            "report-analyses"
        ).textContent =
            stats.analyses || 0;


        /* 描述 */

        document.getElementById(
            "report-description"
        ).textContent =
            `今天分析了 ${stats.analyses || 0} 个页面。`;


        /* 总览 */

        document.getElementById(
            "report-overview"
        ).textContent =
            report.overview ||
            "暂无分析。";


        /* 关注方向 */

        const focusContainer =
            document.getElementById(
                "report-focus"
            );


        const focus =
            report.focus || [];


        if (!focus.length) {

            focusContainer.innerHTML =
                "<div class='report-text'>暂无明显关注方向。</div>";

        } else {

            focusContainer.innerHTML =
                focus.map(item => {

                    return `
                        <div class="report-focus-item">

                            <div class="report-focus-topic">
                                ${escapeHTML(
                                    item.topic || ""
                                )}
                            </div>

                            <div class="report-focus-description">
                                ${escapeHTML(
                                    item.description || ""
                                )}
                            </div>

                        </div>
                    `;

                }).join("");
        }


        /* 信息结构 */

        document.getElementById(
            "report-structure"
        ).textContent =
            report.structure ||
            "暂无分析。";


        /* 值得关注 */

        const highlightsContainer =
            document.getElementById(
                "report-highlights"
            );


        const highlights =
            report.highlights || [];


        if (!highlights.length) {

            highlightsContainer.innerHTML =
                "<div class='report-text'>暂无特别值得关注的内容。</div>";

        } else {

            highlightsContainer.innerHTML =
                highlights.map(item => {

                    return `
                        <div class="report-highlight">

                            <div class="report-highlight-title">
                                ${escapeHTML(
                                    item.title || ""
                                )}
                            </div>

                            <div class="report-highlight-reason">
                                ${escapeHTML(
                                    item.reason || ""
                                )}
                            </div>

                        </div>
                    `;

                }).join("");
        }


        /* AI 总结 */

        document.getElementById(
            "report-insight"
        ).textContent =
            report.insight ||
            "暂无总结。";


    } catch (error) {

        console.error(
            "加载每日报告失败：",
            error
        );


        document.getElementById(
            "report-description"
        ).textContent =
            "报告生成失败";


        document.getElementById(
            "report-overview"
        ).textContent =
            error.message ||
            "无法生成报告。";
    }
}

document.addEventListener(
    "DOMContentLoaded",
    function () {

        const button =
            document.getElementById(
                "report-refresh"
            );

        if (button) {

            button.addEventListener(
                "click",
                loadDailyReport
            );

        }

    }
);

const API = "http://127.0.0.1:8000";

let todayData = null;
let weekData = null;


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


    renderTrendTo(
        container
    );

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
                    "未分析";

                const summary =
                    record.summary ||
                    "暂无摘要";

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

                            <div class="information-url">
                                ${escapeHTML(hostname)}
                            </div>

                            <div class="information-summary">
                                ${escapeHTML(summary)}
                            </div>

                        </div>

                        <div class="information-meta">

                            <span class="information-category">
                                ${escapeHTML(category)}
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



    container.innerHTML = "";


    items.forEach(
        item => {

            const div =
                document.createElement(
                    "div"
                );


            div.className =
                "info-row";


            div.innerHTML = `

                <div>

                    <strong>

                        ${escapeHTML(
                            item.title ||
                            "未命名网页"
                        )}

                    </strong>

                    <p>

                        ${escapeHTML(
                            item.summary ||
                            ""
                        )}

                    </p >

                </div>


                <div class="score">

                    兴趣
                    ${item.interest ?? 0}

                </div>

            `;


            container.appendChild(
                div
            );

        }
    );




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
        .querySelectorAll(".quick-question")
        .forEach(button => {

            button.addEventListener(
                "click",
                function () {

                    input.value =
                        this.textContent.trim();

                    sendAgentQuestion();

                }
            );

        });

}


async function sendAgentQuestion() {

    const input =
        document.getElementById("agent-input");

    const sendButton =
        document.getElementById("agent-send");

    const question =
        input.value.trim();

    if (!question) {
        return;
    }


    addUserMessage(question);

    input.value = "";

    input.disabled = true;

    sendButton.disabled = true;

    sendButton.textContent =
        "分析中...";


    const loading =
        addAgentLoading();


    try {

        const response =
            await fetch(
                "http://127.0.0.1:8000/api/agent/chat",
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json"
                    },

                    body: JSON.stringify({
                        question: question
                    })
                }
            );


        const data =
            await response.json();


        loading.remove();


        if (
            data.success === false
        ) {

            addAgentMessage(
                data.error ||
                "Agent 分析失败。"
            );

        } else {

            addAgentMessage(
                data.answer ||
                "暂时没有得到回答。"
            );

        }


    } catch (error) {

        console.error(
            "Agent 请求失败:",
            error
        );


        loading.remove();


        addAgentMessage(
            "无法连接 AI Agent，请确认 FastAPI 正在运行。"
        );

    }


    input.disabled = false;

    sendButton.disabled = false;

    sendButton.textContent =
        "发送";

    input.focus();

}


function addUserMessage(text) {

    const container =
        document.getElementById(
            "chat-messages"
        );

    const div =
        document.createElement("div");

    div.className =
        "user-message";

    div.innerHTML = `
        <div class="message-label">
            你
        </div>

        <div class="message-content">
            ${escapeAgentHTML(text)}
        </div>
    `;

    container.appendChild(div);

    scrollAgentChat();

}


function addAgentMessage(text) {

    const container =
        document.getElementById(
            "chat-messages"
        );

    const div =
        document.createElement("div");

    div.className =
        "agent-message";

    div.innerHTML = `
        <div class="message-label">
            AI Agent
        </div>

        <div class="message-content">
            ${formatAgentText(text)}
        </div>
    `;

    container.appendChild(div);

    scrollAgentChat();

}


function addAgentLoading() {

    const container =
        document.getElementById(
            "chat-messages"
        );

    const div =
        document.createElement("div");

    div.className =
        "agent-message agent-loading";

    div.innerHTML = `
        <div class="message-label">
            AI Agent
        </div>

        <div class="message-content">
            正在分析你的浏览记录……
        </div>
    `;

    container.appendChild(div);

    scrollAgentChat();

    return div;

}


function formatAgentText(text) {

    if (!text) {
        return "";
    }

    let result =
        escapeAgentHTML(text);

    result =
        result.replace(
            /\n/g,
            "<br>"
        );

    return result;

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
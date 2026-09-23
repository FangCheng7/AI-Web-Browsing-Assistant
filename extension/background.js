let currentPage = null;


// =========================================================
// 当前时间
// =========================================================

function now() {
    return Date.now();
}


// =========================================================
// 判断是否是真实网页
// =========================================================

function isWebPage(url) {

    if (!url) {
        return false;
    }

    return (
        url.startsWith("http://") ||
        url.startsWith("https://")
    );
}


// =========================================================
// 结束当前页面
// =========================================================

async function finishCurrentPage() {

    if (!currentPage) {
        return;
    }

    const page = currentPage;

    currentPage = null;

    if (!page.browseRecordId) {
        console.log("当前页面没有数据库记录");
        return;
    }

    try {

        const response = await fetch(
            "http://127.0.0.1:8000/api/browse/finish",
            {
                method: "POST",

                headers: {
                    "Content-Type": "application/json"
                },

                body: JSON.stringify({
                    browseRecordId:
                        page.browseRecordId,

                    endTime:
                        now()
                })
            }
        );

        const result =
            await response.json();

        console.log(
            "网页记录完成：",
            result
        );

    } catch (error) {

        console.error(
            "完成浏览记录失败：",
            error
        );
    }
}


// =========================================================
// 开始记录页面
// =========================================================

async function startPage(tab) {

    if (!tab || !tab.url) {
        return;
    }

    // 不记录 Edge / Chrome 内部页面
    if (!isWebPage(tab.url)) {

        console.log(
            "跳过非网页：",
            tab.url
        );

        return;
    }


    // 如果当前已经是同一个页面
    // 不要重复创建记录

    if (
        currentPage &&
        currentPage.tabId === tab.id &&
        currentPage.url === tab.url
    ) {

        console.log(
            "同一个页面，不重复记录"
        );

        return;
    }


    // 只有真的换页面时才结束旧页面

    await finishCurrentPage();


    // 创建新的当前页面

    currentPage = {

        tabId:
            tab.id,

        url:
            tab.url,

        title:
            tab.title || "",

        startTime:
            now(),

        browseRecordId:
            null
    };


    console.log(
        "开始记录网页：",
        currentPage
    );


    // =====================================================
    // 创建数据库记录
    // =====================================================

    try {

        const response = await fetch(
            "http://127.0.0.1:8000/api/browse/start",
            {

                method: "POST",

                headers: {
                    "Content-Type":
                        "application/json"
                },

                body: JSON.stringify({

                    tabId:
                        currentPage.tabId,

                    url:
                        currentPage.url,

                    title:
                        currentPage.title,

                    startTime:
                        currentPage.startTime
                })
            }
        );


        const result =
            await response.json();


        console.log(
            "开始记录返回：",
            result
        );


        if (
            result.success &&
            result.recorded
        ) {

            currentPage.browseRecordId =
                result.browse_record_id;


            console.log(
                "BrowseRecord ID：",
                currentPage.browseRecordId
            );
        }

    } catch (error) {

        console.error(
            "创建浏览记录失败：",
            error
        );
    }
}


// =========================================================
// 标签页切换
// =========================================================

chrome.tabs.onActivated.addListener(
    async (activeInfo) => {

        try {

            const tab =
                await chrome.tabs.get(
                    activeInfo.tabId
                );

            await startPage(tab);

        } catch (error) {

            console.error(
                "获取标签页失败：",
                error
            );
        }
    }
);


// =========================================================
// 网页加载状态变化
// =========================================================

chrome.tabs.onUpdated.addListener(

    async (tabId, changeInfo, tab) => {

        // 只处理 URL 真正发生变化
        if (changeInfo.url) {

            const tabs =
                await chrome.tabs.query({
                    active: true,
                    lastFocusedWindow: true
                });

            if (
                tabs.length > 0 &&
                tabs[0].id === tabId
            ) {

                await startPage(tab);
            }

            return;
        }


        // 页面第一次加载完成
        if (
            changeInfo.status === "complete"
        ) {

            const tabs =
                await chrome.tabs.query({
                    active: true,
                    lastFocusedWindow: true
                });

            if (
                tabs.length > 0 &&
                tabs[0].id === tabId
            ) {

                await startPage(tab);
            }
        }
    }
);


// =========================================================
// 标签页关闭
// =========================================================

chrome.tabs.onRemoved.addListener(
    async (tabId) => {

        if (
            currentPage &&
            currentPage.tabId === tabId
        ) {

            await finishCurrentPage();
        }
    }
);


// =========================================================
// 接收网页正文
// =========================================================

chrome.runtime.onMessage.addListener(

    (message, sender) => {

        if (
            message.type !==
            "PAGE_CONTENT"
        ) {
            return;
        }


        const tab =
            sender.tab;


        if (!tab || !tab.url) {
            return;
        }


        console.log(
            "收到网页内容：",
            message.data.title
        );


        // 确认是不是当前页面

        if (
            !currentPage ||
            currentPage.tabId !== tab.id ||
            currentPage.url !== tab.url
        ) {

            console.log(
                "网页记录不匹配，跳过"
            );

            return;
        }


        // 数据库记录还没创建完成
        // 稍后重试

        if (!currentPage.browseRecordId) {

            console.log(
                "等待 BrowseRecord ID..."
            );


            setTimeout(() => {

                sendPageContent(
                    message.data,
                    tab.id
                );

            }, 500);

            return;
        }


        sendPageContent(
            message.data,
            tab.id
        );
    }
);


// =========================================================
// 发送网页内容给后端
// =========================================================

function sendPageContent(
    pageData,
    tabId
) {

    if (!currentPage) {
        return;
    }


    if (
        currentPage.tabId !== tabId
    ) {
        return;
    }


    if (
        !currentPage.browseRecordId
    ) {

        console.log(
            "BrowseRecord ID 不存在"
        );

        return;
    }


    fetch(
        "http://127.0.0.1:8000/api/page-content",
        {

            method: "POST",

            headers: {
                "Content-Type":
                    "application/json"
            },

            body: JSON.stringify({

                title:
                    pageData.title,

                content:
                    pageData.content,

                url:
                    currentPage.url,

                browseRecordId:
                    currentPage.browseRecordId
            })
        }
    )

    .then(response =>
        response.json()
    )

    .then(result => {

        console.log(
            "AI分析接口返回：",
            result
        );

    })

    .catch(error => {

        console.error(
            "发送网页内容失败：",
            error
        );

    });
}
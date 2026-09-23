// =========================================================
// 获取网页正文
// =========================================================

function getPageContent() {

    const title = document.title || "";

    const content =
        document.body
            ? document.body.innerText
            : "";

    return {

        title: title,

        content:
            content.slice(0, 6000)
    };
}


// =========================================================
// 只处理正常网页
// =========================================================

if (
    location.protocol === "http:" ||
    location.protocol === "https:"
) {

    const pageData =
        getPageContent();


    console.log(
        "网页标题：",
        pageData.title
    );


    console.log(
        "网页正文：",
        pageData.content
    );


    // =====================================================
    // 发送给 background.js
    // =====================================================

    chrome.runtime.sendMessage({

        type:
            "PAGE_CONTENT",

        data:
            pageData

    });

}
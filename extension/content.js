// =========================================================
// 获取网页正文
// =========================================================

function normalizeText(value) {
    return String(value || "")
        .replace(/\s+/g, " ")
        .trim();
}


function getMetaContent(selectors) {
    for (const selector of selectors) {
        const element =
            document.querySelector(selector);

        if (!element) {
            continue;
        }

        const content =
            element.getAttribute("content") ||
            element.textContent ||
            "";

        const normalized =
            normalizeText(content);

        if (normalized) {
            return normalized;
        }
    }

    return "";
}


function getMainText() {
    const selectors = [
        "article",
        "main",
        "[role='main']",
        ".article-content",
        ".post-content",
        ".entry-content",
        ".content"
    ];

    let bestText = "";

    for (const selector of selectors) {
        const elements =
            document.querySelectorAll(selector);

        for (const element of elements) {
            const text = normalizeText(
                element.innerText
            );

            if (text.length > bestText.length) {
                bestText = text;
            }
        }
    }

    if (bestText.length >= 200) {
        return bestText;
    }

    if (!document.body) {
        return bestText;
    }

    const clone =
        document.body.cloneNode(true);

    clone.querySelectorAll(
        [
            "script",
            "style",
            "noscript",
            "svg",
            "nav",
            "header",
            "footer",
            "aside",
            "form",
            "[aria-hidden='true']"
        ].join(",")
    ).forEach(element => element.remove());

    const bodyBlocks = Array.from(
        clone.querySelectorAll(
            "p, li, article, h1, h2, h3"
        )
    )
        .map(element => normalizeText(element.textContent))
        .filter(Boolean);

    const bodyText = bodyBlocks.length
        ? bodyBlocks.join(" ")
        : normalizeText(clone.textContent);

    return bodyText.length > bestText.length
        ? bodyText
        : bestText;
}


function getPageContent() {
    const title = normalizeText(
        getMetaContent([
            "meta[property='og:title']",
            "meta[name='twitter:title']"
        ]) || document.title
    );

    const description = getMetaContent([
        "meta[name='description']",
        "meta[property='og:description']",
        "meta[name='twitter:description']"
    ]);

    const keywords = getMetaContent([
        "meta[name='keywords']"
    ]);

    const headings = Array.from(
        document.querySelectorAll("h1, h2")
    )
        .slice(0, 12)
        .map(element => normalizeText(element.innerText))
        .filter(Boolean)
        .join("\n");

    const mainText = getMainText();

    const content = [
        title,
        description,
        keywords ? `关键词：${keywords}` : "",
        headings,
        mainText
    ]
        .filter(Boolean)
        .join("\n\n")
        .slice(0, 12000);

    return {
        title: title || document.title || "",
        content
    };
}


// =========================================================
// 发送给 background.js
// =========================================================

function sendPageContent() {
    const pageData = getPageContent();

    chrome.runtime.sendMessage({
        type: "PAGE_CONTENT",
        data: pageData
    });
}


async function collectAndSend(attempt = 0) {
    const pageData = getPageContent();

    if (
        pageData.content.length < 300 &&
        attempt < 4
    ) {
        setTimeout(
            () => collectAndSend(attempt + 1),
            1200
        );

        return;
    }

    sendPageContent();
}


if (
    location.protocol === "http:" ||
    location.protocol === "https:"
) {
    setTimeout(() => collectAndSend(0), 700);

    // 动态网页通常会在首次渲染后继续加载正文。
    // 第二次发送允许后端把基础分类升级为 AI 分析。
    setTimeout(sendPageContent, 4000);
}

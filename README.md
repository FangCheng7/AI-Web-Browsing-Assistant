# AI 网页浏览分析助手

一个本地运行的「个人信息探索 Agent」桌面工具。浏览器扩展记录网页内容和浏览行为，后端使用 FastAPI、SQLite 与 DeepSeek 进行结构化分析，Dashboard 展示信息消费、兴趣趋势和 Agent 任务结果。

## 功能

- 多轮 Tool Calling Agent
- 今日统计、最近 7 天趋势、最近浏览和分类统计
- 信息消费集中度分析
- 基于真实浏览数据的主动方向发现
- SQLite 长期 Memory
- 浏览器扩展自动采集网页正文
- 桌面 Dashboard 与 Windows EXE

本项目不包含 RAG、向量数据库或联网搜索。Agent 只调用 DeepSeek API 和本地 SQLite Tool。

## 隐私与数据

- 不提交 `.env`、API Key、SQLite 数据库或用户浏览数据。
- DeepSeek API Key 仅保存在本机应用数据目录。
- 结构化业务数据保存在：

```text
%LOCALAPPDATA%\AI网页浏览分析助手\browser.db
```

- 发布压缩包中不包含个人配置和数据库。

## 开发运行

安装依赖：

```powershell
cd C:\Users\24988\Desktop\Agent
backend\venv\Scripts\python.exe -m pip install -r requirements.txt
```

启动后端：

```powershell
cd C:\Users\24988\Desktop\Agent
$env:PYTHONPATH="$PWD\backend"
backend\venv\Scripts\python.exe -m uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

打开 Dashboard：

```text
http://127.0.0.1:8000/dashboard/
```

首次使用需要在「设置」页面填写自己的 DeepSeek API Key。

## 浏览器扩展

在 Edge 或 Chrome 的扩展管理页面启用“开发者模式”，选择“加载解压缩的扩展”，然后选择：

```text
C:\Users\24988\Desktop\Agent\extension
```

## 构建 EXE

```powershell
cd C:\Users\24988\Desktop\Agent
backend\venv\Scripts\python.exe -m PyInstaller --noconfirm --clean "AI网页浏览分析助手.spec"
```

构建结果：

```text
dist\AI网页浏览分析助手\AI网页浏览分析助手.exe
```

## 生成安全发布包

先提交并推送源码，确保工作区干净，然后运行：

```powershell
cd C:\Users\24988\Desktop\Agent
powershell -ExecutionPolicy Bypass -File .\build_release.ps1
```

脚本会生成：

- 源码压缩包：只包含 Git 已跟踪文件
- Windows 免安装包：包含 EXE、运行依赖和浏览器扩展

生成的文件位于 `release\`。脚本会在打包前检查跟踪文件、EXE 目录中是否存在 `.env`、数据库或密钥文件。发现风险时会直接停止。

## 测试

```powershell
cd C:\Users\24988\Desktop\Agent
$env:PYTHONPATH="$PWD\backend"
backend\venv\Scripts\python.exe -m unittest discover -s backend\tests -v
```

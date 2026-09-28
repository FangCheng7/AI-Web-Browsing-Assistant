import json
import os
import sys
import tempfile
import time
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool


BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))


import agent_tools
import ai
import config
import main
import memory
from database import Base
from models import AgentMemory, BrowseRecord, PageAnalysis
from fastapi.testclient import TestClient
from time_utils import get_local_day_range_ms


def make_tool_call(call_id, name, arguments):
    return SimpleNamespace(
        id=call_id,
        function=SimpleNamespace(
            name=name,
            arguments=json.dumps(arguments)
        )
    )


def make_message(content="", tool_calls=None):
    return SimpleNamespace(
        content=content,
        tool_calls=tool_calls or []
    )


def make_response(message):
    return SimpleNamespace(
        choices=[
            SimpleNamespace(message=message)
        ]
    )


class FakeClient:
    def __init__(self, responses):
        self.responses = list(responses)
        self.calls = []
        self.chat = SimpleNamespace(
            completions=SimpleNamespace(
                create=self.create
            )
        )

    def create(self, **kwargs):
        self.calls.append(kwargs)

        if not self.responses:
            raise AssertionError("FakeClient 没有剩余响应")

        return self.responses.pop(0)


class BackendAgentTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool
        )
        Base.metadata.create_all(self.engine)

        self.Session = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=self.engine
        )

        for module in (agent_tools, memory, main):
            self.addCleanup(
                setattr,
                module,
                "SessionLocal",
                module.SessionLocal
            )
            module.SessionLocal = self.Session

        self.seed_data()

    def seed_data(self):
        db = self.Session()
        _, today_start_ms, _ = get_local_day_range_ms()

        samples = [
            (
                "AI Agent 产品分析",
                "https://example.com/agent",
                "AI科技",
                ["人工智能", "产品运营"],
                90
            ),
            (
                "Agent 技术趋势",
                "https://example.com/agent-tech",
                "AI科技",
                ["人工智能", "软件开发"],
                85
            ),
            (
                "AI 教育应用",
                "https://school.example.com/ai",
                "AI科技",
                ["人工智能", "科普知识"],
                80
            ),
            (
                "财经市场观察",
                "https://finance.example.com/market",
                "财经",
                ["金融市场", "股票投资"],
                65
            ),
            (
                "本周电影推荐",
                "https://movie.example.com/list",
                "娱乐",
                ["影视"],
                55
            )
        ]

        for index, sample in enumerate(samples):
            title, url, category, tags, interest = sample
            start_time = (
                today_start_ms
                + (index + 1) * 60 * 1000
            )

            record = BrowseRecord(
                tab_id=index + 1,
                url=url,
                title=title,
                start_time=start_time,
                end_time=start_time + 10 * 60 * 1000,
                duration=10 * 60 * 1000
            )
            db.add(record)
            db.flush()

            db.add(PageAnalysis(
                browse_record_id=record.id,
                url=url,
                title=title,
                category=category,
                subcategory=tags[0],
                topics=json.dumps(tags, ensure_ascii=False),
                tags=json.dumps(tags, ensure_ascii=False),
                summary=f"{title} 的测试摘要",
                interest=interest,
                importance=70,
                analysis_source="ai",
                created_at=start_time
            ))

        db.commit()
        db.close()

    def test_existing_tools_still_work(self):
        today = agent_tools.get_today_stats()
        trend = agent_tools.get_7day_trend()
        recent = agent_tools.get_recent_browsing(3)
        categories = agent_tools.get_category_stats()

        self.assertGreater(today["record_count"], 0)
        self.assertGreater(len(trend["daily_data"]), 0)
        self.assertEqual(recent["count"], 3)
        self.assertIn("AI科技", categories["categories"])

    def test_memory_save_get_and_duplicate(self):
        first = memory.save_memory(
            "AI Agent",
            "interest"
        )
        second = memory.save_memory(
            "AI Agent",
            "interest"
        )
        result = memory.get_memory(limit=10)

        self.assertTrue(first["saved"])
        self.assertFalse(second["saved"])
        self.assertTrue(second["duplicate"])
        self.assertEqual(result["count"], 1)
        self.assertEqual(
            result["memories"][0]["content"],
            "AI Agent"
        )

    def test_memory_rejects_sensitive_data(self):
        result = memory.save_memory(
            "我的手机号是 13800138000",
            "preference"
        )

        self.assertFalse(result["success"])
        self.assertEqual(
            result["error"]["type"],
            "sensitive_memory"
        )

    def test_information_bubble_uses_sqlite_data(self):
        result = agent_tools.analyze_information_bubble(
            days=7,
            top_n=5
        )

        self.assertEqual(result["status"], "ok")
        self.assertEqual(result["total_pages"], 5)
        self.assertEqual(
            result["concentration"]["dominant_category"],
            "AI科技"
        )
        self.assertGreaterEqual(
            result["concentration"][
                "dominant_category_share_percentage"
            ],
            50
        )
        self.assertTrue(result["repeated_topics"])
        self.assertTrue(
            result["underrepresented_categories"]
        )

    def test_discover_new_topics_runs(self):
        result = agent_tools.discover_new_topics(
            limit=3,
            days=7
        )

        self.assertEqual(result["status"], "ok")
        self.assertTrue(result["current_interests"])
        self.assertTrue(result["suggested_directions"])

    def test_search_web_is_not_registered(self):
        names = {
            item["function"]["name"]
            for item in agent_tools.get_enabled_tools()
        }

        self.assertNotIn("search_web", names)
        self.assertEqual(len(names), 8)
        self.assertIn("save_memory", names)
        self.assertIn("get_memory", names)

    def test_agent_prompt_does_not_require_unconfigured_search(self):
        tools = [
            {
                "type": "function",
                "function": agent_tools.get_tool_schema(
                    "get_today_stats"
                )
            }
        ]

        prompt = ai._build_agent_system_prompt(tools)

        self.assertIn(
            "除非用户明确要求最新文章或外部链接",
            prompt
        )
        self.assertNotIn("search_web", prompt)

    def test_execute_unknown_tool_is_structured(self):
        result = agent_tools.execute_tool(
            "missing_tool",
            {}
        )

        self.assertFalse(result["success"])
        self.assertEqual(
            result["error"]["type"],
            "unknown_tool"
        )

    def test_agent_loop_multiple_rounds_and_steps(self):
        fake_client = FakeClient([
            make_response(make_message(
                tool_calls=[
                    make_tool_call(
                        "call-1",
                        "get_today_stats",
                        {}
                    ),
                    make_tool_call(
                        "call-2",
                        "get_category_stats",
                        {}
                    )
                ]
            )),
            make_response(make_message(
                tool_calls=[
                    make_tool_call(
                        "call-3",
                        "analyze_information_bubble",
                        {"days": 7}
                    )
                ]
            )),
            make_response(make_message(
                content="基于真实工具数据生成的最终回答"
            ))
        ])

        with patch.object(
            ai,
            "get_client",
            return_value=fake_client
        ):
            result = ai.analyze_agent_question(
                "分析最近的信息消费",
                tools=agent_tools.TOOLS,
                max_rounds=5
            )

        self.assertEqual(
            [
                step["tool"]
                for step in result["execution_steps"]
            ],
            [
                "get_today_stats",
                "get_category_stats",
                "analyze_information_bubble"
            ]
        )
        self.assertTrue(
            all(
                step["status"] == "success"
                for step in result["execution_steps"]
            )
        )
        self.assertEqual(
            set(result["execution_steps"][0].keys()),
            {"step", "tool", "status", "summary"}
        )
        self.assertEqual(len(fake_client.calls), 3)

    def test_agent_loop_malformed_arguments_do_not_crash(self):
        bad_call = SimpleNamespace(
            id="bad-call",
            function=SimpleNamespace(
                name="get_recent_browsing",
                arguments="{"
            )
        )

        fake_client = FakeClient([
            make_response(make_message(
                tool_calls=[bad_call]
            )),
            make_response(make_message(
                content="参数错误，但已安全结束"
            ))
        ])

        with patch.object(
            ai,
            "get_client",
            return_value=fake_client
        ), patch.object(
            ai,
            "execute_tool",
            wraps=agent_tools.execute_tool
        ) as execute_mock:
            result = ai.analyze_agent_question(
                "测试错误参数",
                tools=agent_tools.TOOLS,
                max_rounds=3
            )

        execute_mock.assert_not_called()
        self.assertEqual(
            result["execution_steps"][0]["status"],
            "error"
        )
        self.assertIn(
            "参数",
            fake_client.calls[1]["messages"][-1]["content"]
        )

    def test_agent_loop_full_six_tool_chain(self):
        fake_client = FakeClient([
            make_response(make_message(
                tool_calls=[
                    make_tool_call(
                        "call-1",
                        "get_7day_trend",
                        {}
                    ),
                    make_tool_call(
                        "call-2",
                        "get_category_stats",
                        {}
                    )
                ]
            )),
            make_response(make_message(
                tool_calls=[
                    make_tool_call(
                        "call-3",
                        "analyze_information_bubble",
                        {"days": 7}
                    ),
                    make_tool_call(
                        "call-4",
                        "get_memory",
                        {"limit": 10}
                    )
                ]
            )),
            make_response(make_message(
                tool_calls=[
                    make_tool_call(
                        "call-5",
                        "discover_new_topics",
                        {"limit": 3, "days": 7}
                    )
                ]
            )),
            make_response(make_message(
                content="完成完整多工具分析"
            ))
        ])

        with patch.object(
            ai,
            "get_client",
            return_value=fake_client
        ):
            result = ai.analyze_agent_question(
                "综合分析并寻找新方向",
                tools=agent_tools.TOOLS,
                max_rounds=5
            )

        self.assertEqual(
            [
                step["tool"]
                for step in result["execution_steps"]
            ],
            [
                "get_7day_trend",
                "get_category_stats",
                "analyze_information_bubble",
                "get_memory",
                "discover_new_topics"
            ]
        )
        self.assertEqual(result["tool_rounds"], 3)
        self.assertEqual(
            result["answer"],
            "完成完整多工具分析"
        )

    def test_agent_loop_stops_at_max_rounds(self):
        repeated_tool = make_response(make_message(
            tool_calls=[
                make_tool_call(
                    "loop-call",
                    "get_today_stats",
                    {}
                )
            ]
        ))

        fake_client = FakeClient([
            repeated_tool,
            repeated_tool,
            make_response(make_message(
                content="达到上限后的安全回答"
            ))
        ])

        with patch.object(
            ai,
            "get_client",
            return_value=fake_client
        ):
            result = ai.analyze_agent_question(
                "触发最大轮数",
                tools=agent_tools.TOOLS,
                max_rounds=2
            )

        self.assertEqual(result["tool_rounds"], 2)
        self.assertEqual(len(result["execution_steps"]), 2)
        self.assertEqual(
            result["answer"],
            "达到上限后的安全回答"
        )
        self.assertNotIn("tools", fake_client.calls[-1])

    def test_agent_chat_endpoint_returns_execution_steps(self):
        with patch.object(
            main,
            "analyze_agent_question",
            return_value={
                "answer": "测试回答",
                "execution_steps": [
                    {
                        "step": 1,
                        "tool": "get_today_stats",
                        "status": "success",
                        "summary": "查询今日浏览统计"
                    }
                ],
                "tool_rounds": 1
            }
        ):
            response = TestClient(main.app).post(
                "/api/agent/chat",
                json={"question": "今天看了什么？"}
            )

        body = response.json()

        self.assertEqual(response.status_code, 200)
        self.assertTrue(body["success"])
        self.assertEqual(body["answer"], "测试回答")
        self.assertEqual(
            body["execution_steps"][0]["tool"],
            "get_today_stats"
        )

    def test_existing_api_endpoints_still_work(self):
        client = TestClient(main.app)

        today = client.get("/api/stats/today/full")
        seven_days = client.get("/api/stats/7days")
        recent = client.get("/api/browse/recent?limit=3")

        self.assertEqual(today.status_code, 200)
        self.assertEqual(seven_days.status_code, 200)
        self.assertEqual(recent.status_code, 200)
        self.assertGreater(
            today.json()["overview"]["pages"],
            0
        )
        self.assertEqual(
            len(recent.json()["records"]),
            3
        )

        started = client.post(
            "/api/browse/start",
            json={
                "tabId": 99,
                "url": "https://example.com/new-page",
                "title": "新页面",
                "startTime": int(time.time() * 1000)
            }
        ).json()

        self.assertTrue(started["success"])

        finished = client.post(
            "/api/browse/finish",
            json={
                "browseRecordId": started["browse_record_id"],
                "endTime": int(time.time() * 1000) + 1000
            }
        )

        self.assertEqual(finished.status_code, 200)
        self.assertTrue(finished.json()["success"])

        with patch.object(
            main,
            "has_api_key",
            return_value=False
        ):
            content = client.post(
                "/api/page-content",
                json={
                    "title": "Python FastAPI 后端开发",
                    "content": (
                        "使用 Python 和 FastAPI 开发后端 API，"
                        "连接 SQLite 数据库。"
                    ) * 5,
                    "url": "https://example.com/new-page",
                    "browseRecordId": started[
                        "browse_record_id"
                    ]
                }
            )

        self.assertEqual(content.status_code, 200)
        self.assertTrue(content.json()["success"])


class ConfigTests(unittest.TestCase):
    def test_save_api_key_preserves_other_env_values(self):
        original_env_file = config.ENV_FILE

        with tempfile.TemporaryDirectory() as temp_dir:
            env_file = Path(temp_dir) / ".env"
            env_file.write_text(
                "DEEPSEEK_API_KEY=old-key\n"
                "DEEPSEEK_MODEL=deepseek-chat\n"
                "FUTURE_SETTING=keep-me\n",
                encoding="utf-8"
            )

            config.ENV_FILE = env_file

            try:
                config.save_api_key("new-key")

                saved = env_file.read_text(
                    encoding="utf-8"
                )

                self.assertIn(
                    "DEEPSEEK_API_KEY=new-key",
                    saved
                )
                self.assertIn(
                    "FUTURE_SETTING=keep-me",
                    saved
                )
                self.assertIn(
                    "DEEPSEEK_MODEL=deepseek-chat",
                    saved
                )

                config.clear_api_key()

                cleared = env_file.read_text(
                    encoding="utf-8"
                )

                self.assertNotIn(
                    "DEEPSEEK_API_KEY=",
                    cleared
                )
                self.assertIn(
                    "FUTURE_SETTING=keep-me",
                    cleared
                )

            finally:
                config.ENV_FILE = original_env_file
                os.environ.pop(
                    "DEEPSEEK_API_KEY",
                    None
                )


if __name__ == "__main__":
    unittest.main()

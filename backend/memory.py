import re
import time

from database import SessionLocal
from models import AgentMemory


ALLOWED_MEMORY_TYPES = {
    "interest",
    "preference",
    "goal",
    "requirement"
}


SENSITIVE_PATTERNS = [
    re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+"),
    re.compile(r"(?<!\d)1[3-9]\d{9}(?!\d)"),
    re.compile(r"(?i)\bsk-[a-z0-9_-]{12,}\b"),
    re.compile(r"(身份证|银行卡|信用卡|密码|验证码|住址)")
]


def _now_ms():
    return int(time.time() * 1000)


def _normalize_memory_type(memory_type):
    value = str(
        memory_type or "preference"
    ).strip().casefold()

    if value not in ALLOWED_MEMORY_TYPES:
        return "preference"

    return value


def _normalize_content(content):
    return re.sub(
        r"\s+",
        " ",
        str(content or "")
    ).strip()


def _contains_sensitive_data(content):
    return any(
        pattern.search(content)
        for pattern in SENSITIVE_PATTERNS
    )


def _memory_to_dict(memory):
    return {
        "id": memory.id,
        "memory_type": memory.memory_type,
        "content": memory.content,
        "created_at": memory.created_at,
        "updated_at": memory.updated_at
    }


def save_memory(content, memory_type="preference"):
    normalized_content = _normalize_content(content)
    normalized_type = _normalize_memory_type(memory_type)

    if not normalized_content:
        return {
            "success": False,
            "saved": False,
            "error": {
                "type": "invalid_memory",
                "message": "记忆内容不能为空"
            }
        }

    if len(normalized_content) > 500:
        return {
            "success": False,
            "saved": False,
            "error": {
                "type": "invalid_memory",
                "message": "记忆内容不能超过 500 个字符"
            }
        }

    if _contains_sensitive_data(normalized_content):
        return {
            "success": False,
            "saved": False,
            "error": {
                "type": "sensitive_memory",
                "message": "检测到联系方式、证件、密码等敏感信息，未保存"
            }
        }

    db = SessionLocal()

    try:
        existing = db.query(AgentMemory).filter(
            AgentMemory.memory_type == normalized_type
        ).all()

        for memory in existing:
            if (
                memory.content
                and memory.content.casefold()
                == normalized_content.casefold()
            ):
                return {
                    "success": True,
                    "saved": False,
                    "duplicate": True,
                    "memory": _memory_to_dict(memory),
                    "message": "相同记忆已存在"
                }

        timestamp = _now_ms()

        memory = AgentMemory(
            memory_type=normalized_type,
            content=normalized_content,
            created_at=timestamp,
            updated_at=timestamp
        )

        db.add(memory)
        db.commit()
        db.refresh(memory)

        return {
            "success": True,
            "saved": True,
            "duplicate": False,
            "memory": _memory_to_dict(memory)
        }

    except Exception:
        db.rollback()
        raise

    finally:
        db.close()


def get_memory(limit=20, memory_type=None):
    try:
        normalized_limit = int(limit)
    except (TypeError, ValueError):
        normalized_limit = 20

    normalized_limit = max(
        1,
        min(50, normalized_limit)
    )

    db = SessionLocal()

    try:
        query = db.query(AgentMemory)

        if memory_type:
            query = query.filter(
                AgentMemory.memory_type
                == _normalize_memory_type(memory_type)
            )

        memories = query.order_by(
            AgentMemory.updated_at.desc(),
            AgentMemory.id.desc()
        ).limit(normalized_limit).all()

        return {
            "success": True,
            "count": len(memories),
            "memories": [
                _memory_to_dict(memory)
                for memory in memories
            ],
            "message": (
                "暂无长期记忆"
                if not memories
                else ""
            )
        }

    finally:
        db.close()

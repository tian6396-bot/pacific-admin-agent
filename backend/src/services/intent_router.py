"""意图路由：规则优先，可后续接 LLM；本阶段保证无 Key 可降级。"""

from __future__ import annotations

import re
from dataclasses import dataclass

from src.core.config import settings


@dataclass
class IntentResult:
    route: str
    domain: str
    intent: str
    confidence: float
    need_clarify: bool
    reason: str = ""


_CLARIFY_PATTERNS = (
    r"^(嗯|啊|那个|这个|你好|在吗|帮我)[\s?？!！.。]*$",
    r"^.{1,4}$",
)

_HUMAN_PATTERNS = (r"转人工", r"人工客服", r"真人", r"找人工")

_SKILL_PATTERNS = (
    (r"请假|年假|调休", "hr", "leave_apply", "skill"),
    (r"报销|发票|差旅费", "expense", "expense_apply", "skill"),
    (r"报修|修电脑|vpn|开不了机", "it", "it_repair", "skill"),
    (r"会议室|订会", "admin", "meeting_book", "skill"),
)

_QA_HINTS = (
    r"多少|标准|上限|规则|怎么|如何|什么|几天|余额|流程|制度|政策|住宿|酒店",
)


def route_intent(query: str) -> IntentResult:
    text = query.strip()
    lower = text.lower()

    for pat in _HUMAN_PATTERNS:
        if re.search(pat, text, re.I):
            return IntentResult(
                route="human_review",
                domain="service_desk",
                intent="handoff",
                confidence=0.95,
                need_clarify=False,
                reason="用户显式转人工",
            )

    if "联网搜索" in text or "web search" in lower:
        return IntentResult(
            route="web",
            domain="platform",
            intent="web_search",
            confidence=0.9,
            need_clarify=False,
            reason="Web Search 默认关闭",
        )

    for pat in _CLARIFY_PATTERNS:
        if re.match(pat, text, re.I):
            return IntentResult(
                route="clarify",
                domain="general",
                intent="vague",
                confidence=0.4,
                need_clarify=True,
                reason="表述过短或模糊",
            )

    for pat, domain, intent, route in _SKILL_PATTERNS:
        if re.search(pat, text, re.I):
            # 若同时像问答（问标准/规则），优先 qa_rag
            if any(re.search(h, text, re.I) for h in _QA_HINTS):
                return IntentResult(
                    route="qa_rag",
                    domain=domain,
                    intent=intent + "_qa",
                    confidence=0.78,
                    need_clarify=False,
                    reason="含办理词但更偏咨询",
                )
            return IntentResult(
                route=route,
                domain=domain,
                intent=intent,
                confidence=0.82,
                need_clarify=False,
                reason="命中办理类关键词",
            )

    if any(re.search(h, text, re.I) for h in _QA_HINTS):
        return IntentResult(
            route="qa_rag",
            domain="general",
            intent="policy_qa",
            confidence=0.8,
            need_clarify=False,
            reason="咨询类问句",
        )

    # 默认走检索问答，置信偏低则澄清
    conf = 0.65
    need = conf < settings.intent_confidence_threshold
    return IntentResult(
        route="clarify" if need else "qa_rag",
        domain="general",
        intent="open_qa",
        confidence=conf,
        need_clarify=need,
        reason="开放问题，按阈值降级",
    )

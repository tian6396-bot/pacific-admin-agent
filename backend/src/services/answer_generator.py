"""基于检索结果生成回答；已配置百炼/LLM 时用模型润色，否则模板降级。"""

from __future__ import annotations

from pycore.core import get_logger

from src.models.chat import Citation
from src.models.knowledge import SearchHit
from src.services import llm_client

logger = get_logger()


def citations_from_hits(hits: list[SearchHit]) -> list[Citation]:
    return [
        Citation(
            document_id=h.document_id,
            title=h.title,
            text=h.text,
            score=h.score,
            version=h.version,
        )
        for h in hits
    ]


def _template_from_hits(query: str, hits: list[SearchHit]) -> str:
    top = hits[0]
    extras = [h for h in hits[1:3] if h.score >= max(0.25, top.score * 0.45)]
    lines = [
        f"根据《{top.title}》相关条款，结合您的问题「{query.strip()}」：",
        "",
        top.text.strip(),
    ]
    if extras:
        lines.append("")
        lines.append("补充参考：")
        for h in extras:
            lines.append(f"- {h.title}：{h.text.strip()[:120]}")
    lines.append("")
    lines.append("以上内容来自已发布知识，如与最新制度冲突请以正式发文为准。")
    return "\n".join(lines)


def generate_from_hits(query: str, hits: list[SearchHit]) -> tuple[str, list[Citation]]:
    """同步模板生成（兼容旧调用）。"""
    if not hits:
        return (
            "暂时没有找到足够可靠的制度依据。请补充业务场景（如职级、城市、费用类型），"
            "或点击「转人工」由坐席协助。",
            [],
        )
    return _template_from_hits(query, hits), citations_from_hits(hits)


async def generate_answer(query: str, hits: list[SearchHit]) -> tuple[str, list[Citation]]:
    """优先 LLM 据资料作答；失败或未配置时回退模板。"""
    if not hits:
        return generate_from_hits(query, hits)

    cites = citations_from_hits(hits)
    if not llm_client.llm_configured():
        return _template_from_hits(query, hits), cites

    evidence_blocks: list[str] = []
    for i, h in enumerate(hits[:4], start=1):
        evidence_blocks.append(
            f"[{i}] 标题：{h.title}\n摘要：{h.text.strip()[:800]}\n相关度：{h.score:.3f}"
        )
    evidence = "\n\n".join(evidence_blocks)

    system = (
        "你是太平洋金科企业内部「智能行政咨询助手」。"
        "只依据用户提供的【知识片段】回答制度/行政问题；不要编造未给出的条款。"
        "回答使用简洁中文，先给结论再给依据；必要时分点。"
        "若资料不足以回答，明确说明不确定并建议补充信息或转人工。"
        "结尾用一两句提醒以正式发文为准。"
    )
    user = (
        f"用户问题：{query.strip()}\n\n"
        f"【知识片段】\n{evidence}\n\n"
        "请基于以上片段作答。"
    )

    try:
        text = await llm_client.chat_completion(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.2,
            max_tokens=1200,
        )
        return text, cites
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM generate failed, fallback template: {}", exc)
        return _template_from_hits(query, hits), cites


def clarify_reply(reason: str = "") -> str:
    tip = f"（{reason}）" if reason else ""
    return (
        f"我还不太确定您的具体需求{tip}。请补充：想咨询哪类制度（差旅/报销/年假/IT），"
        "或说明职级、城市、时间等关键信息；也可以直接说「转人工」。"
    )


async def conversational_reply(query: str, reason: str = "") -> str:
    """寒暄 / 过短问句：有百炼时用模型自然回复，否则模板澄清。"""
    if not llm_client.llm_configured():
        return clarify_reply(reason)

    system = (
        "你是太平洋金科企业内部「智能行政咨询助手」。"
        "用户可能在寒暄或问题很短。用简洁友好的中文回复："
        "问候就正常打招呼，并引导可咨询差旅/报销/年假/IT 等制度，或办理请假报销等；"
        "也可提示可以说「转人工」。不要编造具体制度数字。"
    )
    tip = f"（路由提示：{reason}）" if reason else ""
    user = f"用户说：{query.strip()}{tip}"
    try:
        return await llm_client.chat_completion(
            [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.5,
            max_tokens=400,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning("LLM conversational failed, fallback clarify: {}", exc)
        return clarify_reply(reason)


def skill_placeholder(intent: str) -> str:
    return (
        f"已识别到办理类意图（{intent}）。完整 Skill 确认闸与写工具将在后续功能开通；"
        "当前可先通过「全部服务」发起申请，或继续提问制度细则。"
    )


def human_placeholder() -> str:
    return (
        "已收到转人工请求。坐席队列与交接包将在后续功能开通；"
        "当前可先在对话中补充问题摘要，便于接入后坐席快速了解背景。"
    )


def web_disabled_reply() -> str:
    return "Web Search 默认关闭，暂不支持联网搜索。请改问内部制度，或使用知识库相关问题。"

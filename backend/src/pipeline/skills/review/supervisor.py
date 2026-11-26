"""Supervisor: user-facing routing agent for Lingua Seeker.

The supervisor owns intent routing, action permission checks, and LLM replies.
Conversation persistence stays in :class:`ChatService`.
"""

from __future__ import annotations

import asyncio
import re
from typing import TYPE_CHECKING
from uuid import UUID

from loguru import logger

from src.core.tools.review.contracts import (
    ChatAction,
    ChatMessageResponse,
    ChatSessionResponse,
)
from src.pipeline.skills.review.providers import _KEEPALIVE

if TYPE_CHECKING:
    from src.pipeline.skills.review.chat_service import ChatService
    from src.pipeline.skills.review.providers import ChatLLMProvider

_KEEPALIVE_INTERVAL = 10  # seconds between SSE keepalive events

SUPERVISOR_CAPABILITIES_PROMPT = (
    "You are Supervisor, the Lingua Seeker orchestration assistant. You help clinical "
    "geneticists run literature evidence pipelines, upload PDFs, search "
    "existing evidence, classify variants, interpret evidence cards, and "
    "review pending changes. You ALWAYS reply in the same language as the "
    "user. Do NOT provide a clinical diagnosis.\n\n"
    "You have six dispatchable capabilities. Each requires specific slots "
    "before it can run. While slots are missing, ask one focused follow-up "
    "question and keep `action` null. After all required slots are gathered, "
    "do NOT dispatch immediately. First show a short human-readable summary "
    "of the route/request and ask for final confirmation, keeping `action` "
    "null. Only after the user's next message explicitly confirms should you "
    "set `action.intent` to the matching value and put the slots in "
    "`action.slots`. Keep the reply natural — do not echo JSON.\n\n"
    "GLOBAL ROUTING RULES:\n"
    "- Never tell the user to navigate to another page, click a sidebar item, "
    "or manually open Task Management/Evidence DB/Audit. If routing is needed, "
    "the structured action will route the request after confirmation.\n"
    "- Never emit a structured action in the same turn where the user first "
    "states a request. Gather missing information and/or ask for final "
    "confirmation first.\n"
    "- EXCEPTION (graph-qa): knowledge questions about relationships among "
    "genes, diseases, variants, and phenotypes are READ-ONLY and safe. Do NOT "
    "ask for confirmation and do NOT gather extra slots — emit the graph-qa "
    "action immediately in the same turn (see capability 7).\n"
    "- If the user changes any slot during confirmation, update the summary "
    "and keep `action` null until they confirm the updated plan.\n\n"
    "Capabilities:\n"
    "1. confirm-pipeline — submit the four-phase evidence pipeline after a "
    "conversational Q&A. This is the ONLY intent that starts a pipeline. "
    "Slots: { source_type: 'online'|'local', query?: str, "
    "identifiers?: list as comma-string, gene_symbol?: str, "
    "disease_name?: str, variant_hgvs_p?: str, filename?: str }.\n"
    "   Gathering rules for confirm-pipeline:\n"
    "   a. Decide source_type first. If the user's first message names a "
    "PMID, DOI, PMCID, or keyword search, set source_type='online'. If the "
    "user says 'upload a PDF' or similar, set source_type='local'. Do not "
    "tell them how to navigate. After final confirmation, the frontend will "
    "show an in-chat PDF upload control and submit the task from there.\n"
    "   c. For source_type='local': ask whether they want to narrow the "
    "extraction target before the in-chat upload step. If they provide a filename, "
    "capture it in filename; otherwise filename is optional.\n"
    "   d. OPTIONAL target slots: after the source is settled, ask ONCE "
    "whether the user wants to narrow extraction to a specific gene, "
    "disease, or variant (e.g. 'Want to target a gene, disease, or "
    "variant? Reply with the name, or type skip.'). Accept 'skip', 'no', "
    "'none', or similar to leave them unset. If the user volunteers a "
    "value, capture it into gene_symbol / disease_name / variant_hgvs_p. "
    "Do not ask the same optional question twice.\n"
    "   e. CONFIRMATION GATE: once all required slots are known and any "
    "optional targets are resolved, reply with a short human-readable "
    "summary of the plan ('Source: online — PMID 34521984. Target: BRCA1. "
    "Ready to start?') AND keep action=null for that turn. Wait for the "
    "user's next message.\n"
    "   f. If the next user message is affirmative ('yes', 'ok', 'go', "
    "'start', '开始', '确认', '好', '运行'), emit "
    "action={intent: 'confirm-pipeline', slots: {...}} with every gathered "
    "slot. If the user modifies a slot ('change disease to HBOC', 'skip "
    "the gene'), update the slot in your internal state, reply with an "
    "updated summary, and keep action=null — wait for the next "
    "affirmation.\n"
    "   g. If the user cancels ('no', 'cancel', 'never mind', '取消'), "
    "acknowledge and reply with action=null.\n"
    "   h. NEVER emit the legacy intents 'start-pipeline' or 'upload-pdf' "
    "— they are deprecated and the frontend will reject them.\n"
    "2. search-evidence — search the existing evidence database after final confirmation.\n"
    "   slots: { gene?, variant?, disease?, pmid?, doi? }. Need at least one.\n"
    "3. interpret-evidence — summarise an evidence card after final confirmation.\n"
    "   slots: { evidence_id?: uuid, gene?, variant? }.\n"
    "4. review-changes — list pending review items after final confirmation.\n"
    "   slots: { filter?: 'all' }. Default filter is 'all'.\n"
    "5. check-pipeline-status — check pipeline run status or navigate to "
    "task management after final confirmation.\n"
    "   slots: { run_id?: str }. No slots required (navigates to task list). "
    "If the user provides a run ID, include it.\n\n"
    "6. graph-qa — answer a knowledge question about genes, diseases, "
    "variants, phenotypes, and their relationships using the Neo4j knowledge "
    "graph (terminology baseline + literature evidence). Use this whenever the "
    "user asks WHAT/WHICH/HOW entities relate (e.g. 'What diseases are "
    "associated with COL2A1?', 'COL2A1 与哪些疾病相关?', '哪些变异导致 Stickler "
    "综合征?'). This capability is READ-ONLY: emit it immediately without a "
    "confirmation gate. Keep your text reply to a short lead-in (e.g. 'Let me "
    "check the knowledge graph.' / '让我在知识图谱中查询。') and set "
    "action={intent: 'graph-qa', slots: {question: <the user's full "
    "question>}}. The grounded answer and subgraph are produced by the graph "
    "engine, so do NOT fabricate the answer yourself.\n\n"
    "Identity questions ('who are you?', '你是谁') get a direct answer with "
    "action=null: you are Supervisor, the Lingua Seeker orchestration agent. "
    "Casual greetings get a brief greeting with action=null.\n\n"
    "FORMAT RULES: Reply in plain text and Markdown only. NEVER use HTML tags "
    "(no <span>, <div>, <p>, etc.). For classification labels, write them as "
    "plain text (e.g. 'Pathogenic', 'VUS') — the frontend renders badges "
    "automatically."
)

_QUESTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p)
    for p in [
        r"\?",
        r"^\s*(hi|hello|hey)\s*[!.。！]?\s*$",
        r"^\s*(你好|您好)\s*[!.。！]?\s*$",
        r"\bwhat\b",
        r"\bwhy\b",
        r"\bhow\b",
        r"\bwhich\b",
        r"\bhelp\b",
        r"\bi\s+(want|need|would like)\b.*\b(extract|extraction|search|query|analyze|analyse|upload)\b",
        r"\b(start|run)\b.*\bpipeline\b",
        r"\b(search|query|lookup)\b.*\b(database|db|evidence)\b",
        r"\b什么\b",
        r"\b为什么\b",
        r"\b如何\b",
        r"我想",
        r"我要",
        r"请帮",
        r"帮我",
        r"文献.*(提取|抽取|分析)",
        r"(证据|信息).*(提取|抽取)",
        r"(查询|检索|搜索|查找).*(数据库|证据库|已有证据|现有证据)",
    ]
]
_CORRECTION_PATTERNS: list[re.Pattern[str]] = [
    re.compile(p)
    for p in [
        r"\bchange\b.*\bto\b",
        r"\bupdate\b.*\bto\b",
        r"\bcorrect\b.*\bto\b",
        r"\b修改\b.*\b为\b",
        r"\b改为\b",
    ]
]

# Permissions are enforced in code, not only in the prompt.
_ALLOWED_INTENTS = frozenset(
    {
        "confirm-pipeline",
        "search-evidence",
        "interpret-evidence",
        "review-changes",
        "check-pipeline-status",
        "graph-qa",
    }
)


def validate_supervisor_action(action: ChatAction | None) -> ChatAction | None:
    """Drop actions the supervisor is not permitted to dispatch."""
    if action is None:
        return None
    if action.intent not in _ALLOWED_INTENTS:
        logger.warning("Supervisor rejected unsupported action intent: {}", action.intent)
        return None
    slots = action.slots or {}
    if action.intent == "search-evidence" and not any(
        slots.get(key) for key in ("gene", "variant", "disease", "pmid", "doi")
    ):
        logger.warning("Supervisor rejected search-evidence without search slots")
        return None
    if action.intent == "graph-qa" and not slots.get("question"):
        logger.warning("Supervisor rejected graph-qa without a question")
        return None
    if action.intent == "confirm-pipeline" and slots.get("source_type") not in ("online", "local"):
        logger.warning("Supervisor rejected confirm-pipeline without a valid source_type")
        return None
    return action


class Supervisor:
    """Route user messages to replies and permission-checked actions."""

    def __init__(
        self,
        *,
        chat: ChatService,
        chat_provider: ChatLLMProvider,
    ) -> None:
        self._chat = chat
        self._chat_provider = chat_provider

    async def create_session(
        self,
        *,
        processing_run_id: UUID | None,
        user_id: UUID | None = None,
    ) -> ChatSessionResponse:
        """Create a session through the conversation service."""
        return await self._chat.create_session(processing_run_id=processing_run_id, user_id=user_id)

    async def append_message(
        self,
        *,
        session_id: UUID,
        role: str,
        content: str,
        evidence_id: UUID | None = None,
        entity_id: UUID | None = None,
        action: ChatAction | None = None,
        owner_user_id: UUID | None = None,
    ) -> ChatMessageResponse:
        """Append a message through the conversation service."""
        return await self._chat.append_message(
            session_id=session_id,
            role=role,
            content=content,
            evidence_id=evidence_id,
            entity_id=entity_id,
            action=action,
            owner_user_id=owner_user_id,
        )

    async def list_messages(
        self,
        *,
        session_id: UUID,
        limit: int = 100,
        owner_user_id: UUID | None = None,
    ) -> list[ChatMessageResponse]:
        """List messages through the conversation service."""
        return await self._chat.list_messages(
            session_id=session_id,
            limit=limit,
            owner_user_id=owner_user_id,
        )

    async def build_evidence_context(
        self,
        *,
        canonical_evidence_id: UUID,
        owner_user_id: UUID | None = None,
    ) -> str:
        """Build evidence context through the conversation service."""
        return await self._chat.build_evidence_context(
            canonical_evidence_id=canonical_evidence_id,
            owner_user_id=owner_user_id,
        )

    def _detect_intent(self, message: str) -> str:
        """Detect user intent: question, correction, or note."""
        msg_lower = message.lower()
        if any(p.search(msg_lower) for p in _QUESTION_PATTERNS):
            return "question"
        if any(p.search(msg_lower) for p in _CORRECTION_PATTERNS):
            return "correction"
        return "question"

    def _system_prompt(self, *, has_evidence_context: bool) -> str:
        """Build the supervisor system prompt."""
        if has_evidence_context:
            return (
                "You are a clinical genetics assistant inside Lingua Seeker. Answer "
                "questions about evidence cards using the provided context. Be "
                "precise and cite specific fields from the evidence card. "
                "Reply in plain text and Markdown only — NEVER use HTML tags. "
                "For classification labels, write them as plain text (e.g. "
                "'Pathogenic', 'VUS')."
            )
        return SUPERVISOR_CAPABILITIES_PROMPT

    async def generate_reply(
        self,
        *,
        session_id: UUID,
        user_message: str,
        evidence_id: UUID | None = None,
        owner_user_id: UUID | None = None,
        reviewer_id: UUID | None = None,
    ) -> str | None:
        """Generate a reply based on intent and evidence context."""
        await self._chat.ensure_session(session_id=session_id, owner_user_id=owner_user_id)
        intent = self._detect_intent(user_message)

        if intent == "note":
            return None

        if intent == "correction" and evidence_id:
            return await self._chat.apply_correction(
                evidence_id=evidence_id,
                user_message=user_message,
                reviewer_id=reviewer_id,
                owner_user_id=owner_user_id,
            )

        context = ""
        if evidence_id:
            context = await self._chat.build_evidence_context(
                canonical_evidence_id=evidence_id,
                owner_user_id=owner_user_id,
            )

        system_prompt = self._system_prompt(has_evidence_context=bool(context))
        return await self._chat_provider.generate(
            system_prompt=system_prompt,
            user_message=user_message,
            context=context,
        )

    async def stream_reply(
        self,
        *,
        session_id: UUID,
        user_message: str,
        evidence_id: UUID | None = None,
        owner_user_id: UUID | None = None,
        reviewer_id: UUID | None = None,
    ):
        """Stream a reply as SSE events."""
        await self._chat.ensure_session(session_id=session_id, owner_user_id=owner_user_id)
        intent = self._detect_intent(user_message)

        if intent == "correction" and evidence_id:
            result = await self._chat.apply_correction(
                evidence_id=evidence_id,
                user_message=user_message,
                reviewer_id=reviewer_id,
                owner_user_id=owner_user_id,
            )
            yield {"type": "text", "content": result}
            yield {"type": "done"}
            return

        context = ""
        if evidence_id:
            context = await self._chat.build_evidence_context(
                canonical_evidence_id=evidence_id,
                owner_user_id=owner_user_id,
            )

        system_prompt = self._system_prompt(has_evidence_context=bool(context))

        if not context:
            async for event in self._stream_router_envelope(
                provider=self._chat_provider,
                session_id=session_id,
                system_prompt=system_prompt,
                user_message=user_message,
                owner_user_id=owner_user_id,
            ):
                yield event
            return

        buffered: list[str] = []
        try:
            async for event in self._stream_with_keepalive(
                self._chat_provider.stream(
                    system_prompt=system_prompt,
                    user_message=user_message,
                    context=context,
                ),
            ):
                if event is _KEEPALIVE:
                    yield {"type": "keepalive"}
                else:
                    buffered.append(event)
                    yield {"type": "text", "content": event}
            yield {"type": "done"}
        except Exception as e:
            yield {"type": "error", "message": str(e)}
            return

        complete_reply = "".join(buffered)
        if complete_reply:
            await self._chat.append_message(
                session_id=session_id,
                role="assistant",
                content=complete_reply,
                evidence_id=evidence_id,
                owner_user_id=owner_user_id,
            )

    async def _stream_router_envelope(
        self,
        *,
        provider: ChatLLMProvider,
        session_id: UUID,
        system_prompt: str,
        user_message: str,
        owner_user_id: UUID | None = None,
    ):
        history = await self._load_router_history(
            session_id=session_id,
            exclude_latest_user_message=user_message,
        )

        reply = ""
        action: ChatAction | None = None
        try:
            async for item in provider.route_intent_stream(
                system_prompt=system_prompt,
                user_message=user_message,
                history=history,
            ):
                if item is _KEEPALIVE:
                    yield {"type": "keepalive"}
                elif isinstance(item, tuple):
                    tail, action = item
                    action = validate_supervisor_action(action)
                    if tail:
                        reply += tail
                        yield {"type": "text", "content": tail}
                elif isinstance(item, str) and item:
                    reply += item
                    yield {"type": "text", "content": item}
        except Exception as e:
            yield {"type": "error", "message": str(e)}
            return

        if action is not None:
            yield {
                "type": "action",
                "intent": action.intent,
                "slots": action.slots,
            }

        yield {"type": "done"}

        if reply or action is not None:
            await self._chat.append_message(
                session_id=session_id,
                role="assistant",
                content=reply or "",
                action=action,
                owner_user_id=owner_user_id,
            )

    @staticmethod
    async def _stream_with_keepalive(source):
        """Yield keepalive sentinels when the source stalls."""
        ait = source.__aiter__()
        try:
            while True:
                try:
                    item = await asyncio.wait_for(ait.__anext__(), _KEEPALIVE_INTERVAL)
                    yield item
                except StopAsyncIteration:
                    break
                except TimeoutError:
                    yield _KEEPALIVE
        finally:
            await ait.aclose()

    async def _load_router_history(
        self,
        *,
        session_id: UUID,
        limit: int = 10,
        exclude_latest_user_message: str | None = None,
    ) -> list[dict[str, str]]:
        rows = await self._chat.recent_history(session_id=session_id, limit=limit)
        history = [{"role": m.role, "content": m.content} for m in rows]
        if (
            exclude_latest_user_message
            and history
            and history[-1]["role"] == "user"
            and history[-1]["content"].strip() == exclude_latest_user_message.strip()
        ):
            history.pop()
        return history

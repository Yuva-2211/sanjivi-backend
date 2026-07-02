"""
LangGraph Orchestrator — the central state machine for Sanjivi AI.

Graph topology:
    [START]
      │
      ▼
  emergency_check ──(emergency)──► [END]
      │
   (safe)
      │
      ▼
  run_experts   ←── parallel asyncio.gather of all 5 domain experts
      │
      ▼
  yoga_image_search
      │
      ▼
  consensus
      │
      ▼
  reviewer
      │
      ▼
   [END]
"""

from __future__ import annotations

import asyncio
from typing import Any, Optional, TypedDict

# pyrefly: ignore [missing-import]
from langgraph.graph import END, StateGraph

from app.agents.ayurveda import run_ayurveda_expert
from app.agents.consensus import run_consensus_agent
from app.agents.emergency import screen_for_emergency
from app.agents.homeopathy import run_homeopathy_expert
from app.agents.reviewer import run_reviewer_agent
from app.agents.siddha import run_siddha_expert
from app.agents.unani import run_unani_expert
from app.agents.yoga import run_yoga_expert
from app.agents.yoga_image_search import search_yoga_images
from app.rag.retriever import get_hybrid_retriever
from app.utils.routing import classify_query_domains, VALID_SYSTEMS, normalize_selected_system
from app.schemas.chat import (
    ChatResponse,
    ConsensusResponse,
    ExpertResponse,
    HospitalReferral,
    ReviewerResponse,
    SourceDocument,
    YogaResponse,
)
from app.schemas.rag import RetrievedChunk
from app.utils.helpers import build_citation
from app.utils.logger import get_logger

log = get_logger(__name__)


# ── State definition ──────────────────────────────────────────────────────────

class SanjiviState(TypedDict):
    # Input
    query: str
    selected_system: str
    lat: Optional[float]
    lng: Optional[float]
    history: list[dict]  # conversation history for multi-turn context

    # Emergency
    emergency: bool
    hospital_referral: Optional[dict]

    # Expert responses (stored as dicts for LangGraph JSON serialisation)
    ayurveda_response: Optional[dict]
    siddha_response: Optional[dict]
    unani_response: Optional[dict]
    homeopathy_response: Optional[dict]
    yoga_response: Optional[dict]

    # Accumulated source chunks
    source_chunks: list[dict]

    # Post-processing
    consensus_response: Optional[dict]
    reviewer_response: Optional[dict]

    # Error tracking
    errors: list[str]


# ── Node helpers ──────────────────────────────────────────────────────────────

def _chunks_to_sources(chunks: list[RetrievedChunk]) -> list[dict]:
    """Convert retrieved chunks to serialisable source dicts."""
    seen: set[str] = set()
    sources: list[dict] = []
    for chunk in chunks:
        if chunk.chunk_id in seen:
            continue
        seen.add(chunk.chunk_id)
        sources.append(
            build_citation(
                source_file=chunk.source_file,
                page=chunk.page,
                domain=chunk.domain,
                excerpt=chunk.text,
            )
        )
    return sources


# ── Graph nodes ───────────────────────────────────────────────────────────────

async def emergency_check_node(state: SanjiviState) -> dict:
    """Screen the query for emergency conditions."""
    query = state["query"].strip()
    log.info("node_emergency_check", query=query[:80])

    if not query:
        raise ValueError("Empty query is not allowed. Please provide symptoms or a health question.")

    is_emergency, referral = await screen_for_emergency(
        query=query,
        lat=state.get("lat"),
        lng=state.get("lng"),
    )

    result: dict = {"emergency": is_emergency, "errors": state.get("errors", [])}

    if is_emergency and referral:
        result["hospital_referral"] = referral.model_dump()

    return result


async def run_experts_node(state: SanjiviState) -> dict:
    """Run the routed AYUSH expert domains with parallel retrieval and generation."""
    log.info("node_run_experts", query=state["query"][:80], selected_system=state["selected_system"])

    query = state["query"].strip()
    selected_system = normalize_selected_system(state.get("selected_system", "Multisystem"))
    history = state.get("history", [])

    expert_map = {
        "Ayurveda": (run_ayurveda_expert, "ayurveda"),
        "Siddha": (run_siddha_expert, "siddha"),
        "Unani": (run_unani_expert, "unani"),
        "Homeopathy": (run_homeopathy_expert, "homeopathy"),
        "Yoga": (run_yoga_expert, "yoga"),
    }

    if selected_system == "Multisystem":
        candidate_domains = classify_query_domains(query)
        if candidate_domains == ["Multisystem"]:
            candidate_domains = list(expert_map.keys())
    else:
        candidate_domains = [selected_system] if selected_system in expert_map else list(expert_map.keys())

    log.info("routing_decision", selected_system=selected_system, candidate_domains=candidate_domains)

    # Retrieve only the domains selected by routing. Multisystem may still
    # choose multiple domains, but a manually selected system stays single-agent.
    retrieval_tasks: list[tuple[str, asyncio.Task[list[RetrievedChunk]]]] = []
    selected_experts = {
        label: expert_map[label]
        for label in candidate_domains
        if label in expert_map
    }

    for label, (_, domain) in selected_experts.items():
        retriever = get_hybrid_retriever(domain)
        retrieval_tasks.append((label, asyncio.create_task(retriever.retrieve(query))))

    chunk_map: dict[str, list[RetrievedChunk]] = {}
    errors: list[str] = list(state.get("errors", []))

    if retrieval_tasks:
        retrieval_results = await asyncio.gather(*(task for _, task in retrieval_tasks), return_exceptions=True)
        for (label, _), result in zip(retrieval_tasks, retrieval_results):
            if isinstance(result, Exception):
                errors.append(f"{label} retrieval failed: {result}")
                chunk_map[label] = []
            else:
                chunk_map[label] = result

    # Concurrent expert generation
    expert_results: dict[str, Any] = {}
    all_chunks: list[RetrievedChunk] = []

    async def _run_expert(lbl: str, fn: Any, chks: list[RetrievedChunk]) -> tuple[str, Any]:
        try:
            res = await asyncio.wait_for(fn(query, chunks=chks, history=history), timeout=28.0)
            return lbl, res
        except asyncio.TimeoutError:
            log.error("expert_timeout", domain=lbl)
            return lbl, TimeoutError(f"{lbl} expert timed out after 28 seconds")
        except Exception as exc:
            return lbl, exc

    expert_tasks = [
        _run_expert(label, expert_fn, chunk_map.get(label, []))
        for label, (expert_fn, _) in selected_experts.items()
    ]

    expert_gathered = await asyncio.gather(*expert_tasks)

    for label, res in expert_gathered:
        if isinstance(res, Exception):
            errors.append(f"{label} expert failed: {res}")
            expert_results[label] = None
        elif res is None:
            expert_results[label] = None
        else:
            resp_obj, used_chunks = res
            expert_results[label] = (resp_obj, used_chunks)
            all_chunks.extend(used_chunks)

    def _safe_response(
        res: Any,
        label: str,
    ) -> tuple[Optional[dict], list[RetrievedChunk]]:
        if isinstance(res, Exception):
            errors.append(f"{label} expert failed: {str(res)}")
            return None, []
        if res is None:
            return None, []
        resp_obj, chunks = res
        return resp_obj.model_dump() if resp_obj else None, chunks

    ay_dict, ay_chunks = _safe_response(expert_results.get("Ayurveda"), "Ayurveda")
    sd_dict, sd_chunks = _safe_response(expert_results.get("Siddha"), "Siddha")
    un_dict, un_chunks = _safe_response(expert_results.get("Unani"), "Unani")
    ho_dict, ho_chunks = _safe_response(expert_results.get("Homeopathy"), "Homeopathy")
    yo_dict, yo_chunks = _safe_response(expert_results.get("Yoga"), "Yoga")

    log.info(
        "node_run_experts_done",
        ayurveda=bool(ay_dict),
        siddha=bool(sd_dict),
        unani=bool(un_dict),
        homeopathy=bool(ho_dict),
        yoga=bool(yo_dict),
    )

    return {
        "ayurveda_response": ay_dict,
        "siddha_response": sd_dict,
        "unani_response": un_dict,
        "homeopathy_response": ho_dict,
        "yoga_response": yo_dict,
        "source_chunks": _chunks_to_sources(all_chunks),
        "errors": errors,
    }


async def yoga_image_search_node(state: SanjiviState) -> dict:
    """Fetch pose images for the yoga recommendations (runs in parallel with consensus)."""
    log.info("node_yoga_image_search")

    yoga_dict = state.get("yoga_response")
    if not yoga_dict:
        return {}

    poses = yoga_dict.get("poses", [])
    if not poses:
        return {}

    images = await search_yoga_images(poses, max_images=3)
    yoga_dict = dict(yoga_dict)  # avoid mutating shared state
    yoga_dict["images"] = [img.model_dump() for img in images]

    return {"yoga_response": yoga_dict}


async def consensus_node(state: SanjiviState) -> dict:
    """Synthesise all expert responses into a consensus."""
    log.info("node_consensus")

    def _deserialize_expert(d: Optional[dict]) -> Optional[ExpertResponse]:
        return ExpertResponse(**d) if d else None

    def _deserialize_yoga(d: Optional[dict]) -> Optional[YogaResponse]:
        return YogaResponse(**d) if d else None

    consensus = await run_consensus_agent(
        query=state["query"],
        ayurveda=_deserialize_expert(state.get("ayurveda_response")),
        siddha=_deserialize_expert(state.get("siddha_response")),
        unani=_deserialize_expert(state.get("unani_response")),
        homeopathy=_deserialize_expert(state.get("homeopathy_response")),
        yoga=_deserialize_yoga(state.get("yoga_response")),
    )

    return {"consensus_response": consensus.model_dump()}


async def reviewer_node(state: SanjiviState) -> dict:
    """Perform final safety review and produce the patient-facing response."""
    log.info("node_reviewer")

    def _deserialize_expert(d: Optional[dict]) -> Optional[ExpertResponse]:
        return ExpertResponse(**d) if d else None

    def _deserialize_yoga(d: Optional[dict]) -> Optional[YogaResponse]:
        return YogaResponse(**d) if d else None

    def _deserialize_consensus(d: Optional[dict]) -> Optional[ConsensusResponse]:
        return ConsensusResponse(**d) if d else None

    reviewer = await run_reviewer_agent(
        query=state["query"],
        consensus=_deserialize_consensus(state.get("consensus_response")),
        ayurveda=_deserialize_expert(state.get("ayurveda_response")),
        siddha=_deserialize_expert(state.get("siddha_response")),
        unani=_deserialize_expert(state.get("unani_response")),
        homeopathy=_deserialize_expert(state.get("homeopathy_response")),
        yoga=_deserialize_yoga(state.get("yoga_response")),
    )

    return {"reviewer_response": reviewer.model_dump()}


# ── Routing logic ─────────────────────────────────────────────────────────────

def _route_after_emergency(state: SanjiviState) -> str:
    """Route to END if emergency detected, otherwise run experts."""
    return "end" if state.get("emergency", False) else "run_experts"


# ── Graph construction ────────────────────────────────────────────────────────

def build_graph():
    """Construct and compile the LangGraph StateGraph.

    Topology (non-emergency path):
        run_experts
             ├─── yoga_image_search  ─┐
             └─── consensus          ─┴─► merge_yoga ──► reviewer ──► END

    yoga_image_search runs in parallel with consensus so it is NOT on the
    critical path — DuckDuckGo image fetches no longer add to wall-clock time.
    """
    graph = StateGraph(SanjiviState)

    # Register nodes
    graph.add_node("emergency_check", emergency_check_node)
    graph.add_node("run_experts", run_experts_node)
    graph.add_node("yoga_image_search", yoga_image_search_node)
    graph.add_node("consensus", consensus_node)
    graph.add_node("reviewer", reviewer_node)

    # Entry point
    graph.set_entry_point("emergency_check")

    # Conditional routing after emergency check
    graph.add_conditional_edges(
        "emergency_check",
        _route_after_emergency,
        {"end": END, "run_experts": "run_experts"},
    )

    # yoga_image_search and consensus both fan out from run_experts in parallel
    graph.add_edge("run_experts", "yoga_image_search")
    graph.add_edge("run_experts", "consensus")

    # reviewer waits for BOTH yoga_image_search and consensus to complete
    graph.add_edge("yoga_image_search", "reviewer")
    graph.add_edge("consensus", "reviewer")
    graph.add_edge("reviewer", END)

    return graph.compile()


# ── Singleton compiled graph ──────────────────────────────────────────────────

_graph = None


def get_graph():
    """Return the compiled LangGraph (built once per process)."""
    global _graph
    if _graph is None:
        _graph = build_graph()
        log.info("langgraph_compiled")
    return _graph


# ── Public orchestration function ─────────────────────────────────────────────

async def run_sanjivi(
    query: str,
    selected_system: str = "Multisystem",
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    history: list[dict] | None = None,
) -> ChatResponse:
    """
    Main entry point — run the full Sanjivi AI pipeline for a given query.

    Returns a fully populated ChatResponse ready for the API layer.
    """
    log.info("sanjivi_run_start", query=query[:80])

    initial_state: SanjiviState = {
        "query": query,
        "selected_system": selected_system,
        "lat": lat,
        "lng": lng,
        "history": history or [],
        "emergency": False,
        "hospital_referral": None,
        "ayurveda_response": None,
        "siddha_response": None,
        "unani_response": None,
        "homeopathy_response": None,
        "yoga_response": None,
        "source_chunks": [],
        "consensus_response": None,
        "reviewer_response": None,
        "errors": [],
    }

    graph = get_graph()
    final_state: SanjiviState = await graph.ainvoke(initial_state)

    log.info(
        "sanjivi_run_done",
        emergency=final_state["emergency"],
        errors=len(final_state.get("errors", [])),
    )

    # Build ChatResponse from final state
    is_emergency = final_state.get("emergency", False)

    hospital_referral = None
    if is_emergency and final_state.get("hospital_referral"):
        hospital_referral = HospitalReferral(**final_state["hospital_referral"])

    def _expert(d: Optional[dict]) -> Optional[ExpertResponse]:
        return ExpertResponse(**d) if d else None

    def _yoga(d: Optional[dict]) -> Optional[YogaResponse]:
        return YogaResponse(**d) if d else None

    def _consensus(d: Optional[dict]) -> Optional[ConsensusResponse]:
        return ConsensusResponse(**d) if d else None

    def _reviewer(d: Optional[dict]) -> Optional[ReviewerResponse]:
        return ReviewerResponse(**d) if d else None

    reviewer_resp = _reviewer(final_state.get("reviewer_response"))

    sources = [
        SourceDocument(**s) for s in final_state.get("source_chunks", [])
    ]

    return ChatResponse(
        emergency=is_emergency,
        hospital_referral=hospital_referral,
        patient_summary=reviewer_resp.patient_summary if reviewer_resp else "",
        ayurveda=_expert(final_state.get("ayurveda_response")),
        siddha=_expert(final_state.get("siddha_response")),
        unani=_expert(final_state.get("unani_response")),
        homeopathy=_expert(final_state.get("homeopathy_response")),
        yoga=_yoga(final_state.get("yoga_response")),
        consensus=_consensus(final_state.get("consensus_response")),
        reviewer=reviewer_resp,
        sources=sources,
    )


from typing import AsyncGenerator

async def stream_sanjivi(
    query: str,
    selected_system: str = "Multisystem",
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    history: list[dict] | None = None,
) -> AsyncGenerator[dict, None]:
    """
    Run the Sanjivi AI pipeline and yield node completion events as they happen.
    """
    log.info("sanjivi_stream_start", query=query[:80])

    initial_state: SanjiviState = {
        "query": query,
        "selected_system": selected_system,
        "lat": lat,
        "lng": lng,
        "history": history or [],
        "emergency": False,
        "hospital_referral": None,
        "ayurveda_response": None,
        "siddha_response": None,
        "unani_response": None,
        "homeopathy_response": None,
        "yoga_response": None,
        "source_chunks": [],
        "consensus_response": None,
        "reviewer_response": None,
        "errors": [],
    }

    graph = get_graph()
    async for event in graph.astream(initial_state):
        yield event

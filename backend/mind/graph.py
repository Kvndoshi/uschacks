import asyncio
import logging
from langgraph.graph import StateGraph, END
from mind.state import MindState, HiveMindState
from mind.queen import execute_task
from models.task import TaskRequest
from mind.prompt_loader import load_prompt
from services.minimax_client import minimax_chat
import json

logger = logging.getLogger(__name__)

MAX_RETRIES = 1


async def queen_plan(state: MindState) -> MindState:
    state["phase"] = "planning"
    logger.info(f"Queen planning: {state['master_task'][:60]}")
    return state


async def dispatch_workers(state: MindState) -> MindState:
    state["phase"] = "dispatching"
    request = TaskRequest(task=state["master_task"])
    result = await execute_task(request)

    state["subtasks"] = [st.model_dump() for st in result.subtasks]
    state["worker_results"] = {r.agent_id: r.result for r in result.results}
    state["final_result"] = result.final_result or ""
    state["errors"] = [r.result for r in result.results if not r.success]
    return state


async def monitor_workers(state: MindState) -> MindState:
    state["phase"] = "monitoring"
    has_errors = bool(state.get("errors"))
    has_results = bool(state.get("worker_results"))

    if has_results and not has_errors:
        state["phase"] = "all_complete"
    elif has_errors:
        state["phase"] = "has_failures"
    else:
        state["phase"] = "all_complete"

    return state


def should_continue(state: MindState) -> str:
    if state.get("phase") == "has_failures":
        return "handle_failure"
    return "aggregate"


async def aggregate(state: MindState) -> MindState:
    state["phase"] = "completed"
    logger.info("All workers completed, aggregating results")
    return state


def should_retry(state: MindState) -> str:
    retry_count = state.get("_retry_count", 0)
    if retry_count < MAX_RETRIES and state.get("errors"):
        return "retry"
    return "abort"


async def handle_failure(state: MindState) -> MindState:
    retry_count = state.get("_retry_count", 0)
    state["_retry_count"] = retry_count + 1
    state["phase"] = "handling_failure"
    logger.error(f"Task failed (attempt {retry_count + 1}): {state['errors']}")
    return state


async def classify_intent_node(state: HiveMindState) -> HiveMindState:
    prompt = load_prompt("intent_classifier")
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": state.get("message_text", "")}
    ]
    import re
    response = await minimax_chat(messages, model="minimax-m2.7")
    try:
        # MiniMax models may include <think> tags. Strip them entirely.
        clean_text = re.sub(r'<think>.*?</think>', '', response, flags=re.DOTALL).strip()
        
        if "```json" in clean_text:
            clean_resp = clean_text.split("```json")[1].split("```")[0].strip()
        elif "```" in clean_text:
            clean_resp = clean_text.split("```")[1].split("```")[0].strip()
        else:
            clean_resp = clean_text.strip()
            
        data = json.loads(clean_resp)
        state["intent"] = data.get("intent", "information")
        state["intent_confidence"] = data.get("confidence", 1.0)
    except Exception as e:
        logger.error(f"Failed to parse intent JSON: {response} - {e}")
        state["intent"] = "information"
        state["intent_confidence"] = 0.0
        
    state["phase"] = f"intent_classified_{state.get('intent', 'information')}"
    return state

async def quick_answer_node(state: HiveMindState) -> HiveMindState:
    prompt = load_prompt("quick_answer")
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": state.get("message_text", "")}
    ]
    response = await minimax_chat(messages, model="minimax-m2.7")
    state["response_text"] = response
    state["phase"] = "completed"
    return state

async def synthesize_results_node(state: HiveMindState) -> HiveMindState:
    prompt = load_prompt("result_synthesizer")
    results_context = "\n".join(
        [f"Result {k}: {v}" for k, v in state.get("worker_results", {}).items()]
    )
    user_msg = f"User Request: {state.get('master_task', '')}\n\nWorker Results:\n{results_context}"
    messages = [
        {"role": "system", "content": prompt},
        {"role": "user", "content": user_msg}
    ]
    response = await minimax_chat(messages, model="minimax-m2.7")
    state["response_text"] = response
    state["phase"] = "completed"
    return state


def build_mind_graph():
    graph = StateGraph(MindState)

    graph.add_node("queen_plan", queen_plan)
    graph.add_node("dispatch_workers", dispatch_workers)
    graph.add_node("monitor_workers", monitor_workers)
    graph.add_node("aggregate", aggregate)
    graph.add_node("handle_failure", handle_failure)

    graph.set_entry_point("queen_plan")
    graph.add_edge("queen_plan", "dispatch_workers")
    graph.add_edge("dispatch_workers", "monitor_workers")

    graph.add_conditional_edges("monitor_workers", should_continue, {
        "aggregate": "aggregate",
        "handle_failure": "handle_failure",
    })

    graph.add_conditional_edges("handle_failure", should_retry, {
        "retry": "dispatch_workers",
        "abort": "aggregate",
    })

    graph.add_edge("aggregate", END)

    return graph.compile()

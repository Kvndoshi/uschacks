import asyncio
import uuid
import logging
from models.agent import AgentStatusEnum, HITLRequest
from models.task import SubTask, SubTaskResult
from models import events
from hive.sensitive import detect
from hive.memory import mind_memory
from services.browser_manager import browser_manager
from services.websocket_manager import manager as ws_manager
from services import elevenlabs_service

logger = logging.getLogger(__name__)

hitl_events: dict[str, asyncio.Event] = {}
hitl_resolutions: dict[str, dict] = {}


async def run_worker(subtask: SubTask, subtask_index: int) -> SubTaskResult:
    agent_id = f"worker-{subtask.subtask_id}"
    step_count = 0

    await ws_manager.broadcast(events.agent_spawned(agent_id, subtask.description, subtask_index))
    await ws_manager.broadcast(events.agent_status(agent_id, AgentStatusEnum.PLANNING))

    try:
        audio = await elevenlabs_service.announce(f"Agent {subtask_index + 1} is now active.")
        if audio:
            await ws_manager.broadcast(events.voice_announcement(
                f"Agent {subtask_index + 1} is now active.", audio))
    except Exception:
        pass

    async def on_step(browser_state, agent_output, step):
        nonlocal step_count
        step_count += 1
        output_text = str(agent_output) if agent_output else ""
        current_url = ""

        try:
            if browser_state and hasattr(browser_state, "url"):
                current_url = browser_state.url
        except Exception:
            pass

        await ws_manager.broadcast(events.agent_log(
            agent_id, output_text[:200], current_url, f"step-{step_count}"))
        await ws_manager.broadcast(events.agent_status(
            agent_id, AgentStatusEnum.RUNNING, step_count))

        dom_text = ""
        is_sensitive, reason = detect(output_text, current_url, dom_text)

        if is_sensitive:
            hitl_id = str(uuid.uuid4())[:8]
            logger.warning(f"HITL triggered for {agent_id}: {reason}")

            await ws_manager.broadcast(events.agent_status(
                agent_id, AgentStatusEnum.WAITING_HITL, step_count))
            await ws_manager.broadcast(events.hitl_request(
                agent_id, hitl_id, reason.split(":")[0].strip(),
                output_text[:300], current_url))

            try:
                audio = await elevenlabs_service.announce(
                    f"Agent {subtask_index + 1} needs your approval.")
                if audio:
                    await ws_manager.broadcast(events.voice_announcement(
                        f"Agent {subtask_index + 1} needs your approval.", audio))
            except Exception:
                pass

            event = asyncio.Event()
            hitl_events[hitl_id] = event
            await event.wait()

            resolution = hitl_resolutions.get(hitl_id, {})
            await ws_manager.broadcast(events.hitl_resolved(
                agent_id, hitl_id, resolution.get("resolution", "approved")))

            if resolution.get("resolution") == "rejected":
                raise Exception("Action rejected by user")

            await ws_manager.broadcast(events.agent_status(
                agent_id, AgentStatusEnum.RUNNING, step_count))

    try:
        task_with_context = subtask.description
        ctx = mind_memory.get_context_summary()
        if ctx:
            task_with_context += f"\n\nShared context:\n{ctx}"

        await ws_manager.broadcast(events.agent_status(agent_id, AgentStatusEnum.RUNNING))

        agent = await browser_manager.create_agent(
            agent_id=agent_id,
            task=task_with_context,
            on_step_callback=on_step,
        )

        result_text = await browser_manager.run_agent(agent_id)

        await mind_memory.add_result(SubTaskResult(
            subtask_id=subtask.subtask_id,
            agent_id=agent_id,
            result=result_text,
            steps_taken=step_count,
            success=True,
        ))

        await ws_manager.broadcast(events.agent_completed(agent_id, result_text, step_count))
        await ws_manager.broadcast(events.agent_status(agent_id, AgentStatusEnum.COMPLETED))

        try:
            audio = await elevenlabs_service.announce(
                f"Agent {subtask_index + 1} has completed its task.")
            if audio:
                await ws_manager.broadcast(events.voice_announcement(
                    f"Agent {subtask_index + 1} has completed its task.", audio))
        except Exception:
            pass

        return SubTaskResult(
            subtask_id=subtask.subtask_id,
            agent_id=agent_id,
            result=result_text,
            steps_taken=step_count,
            success=True,
        )

    except Exception as e:
        error_msg = str(e)
        logger.error(f"Worker {agent_id} failed: {error_msg}")
        await mind_memory.add_error(f"{agent_id}: {error_msg}")
        await ws_manager.broadcast(events.agent_failed(agent_id, error_msg))
        await ws_manager.broadcast(events.agent_status(agent_id, AgentStatusEnum.ERROR))

        return SubTaskResult(
            subtask_id=subtask.subtask_id,
            agent_id=agent_id,
            result=f"Error: {error_msg}",
            steps_taken=step_count,
            success=False,
        )

    finally:
        await browser_manager.stop_agent(agent_id)

import pytest
import asyncio
from mind.state import HiveMindState
from mind.graph import classify_intent_node

@pytest.mark.asyncio
async def test_intent_classification():
    # 10+ edge cases and general phrases mapped to their intent category
    test_cases = [
        ("What is the capital of France?", "information"),
        ("Compare prices for an iPhone 16 Pro across BestBuy and Apple", "browser_task"),
        ("Find me a cheap flight to Japan", "browser_task"),
        ("How is the price search going?", "status_query"),
        ("Wait, make sure the flight is direct", "followup"),
        ("Can you summarize the plot of Inception?", "information"),
        ("Are you done yet?", "status_query"),
        ("Who was the first president of the United States?", "information"),
        ("Actually, look for red shoes instead of blue", "followup"),
        ("Search google for python tutorials", "browser_task"),
        ("Are you still looking at the tickets?", "status_query"),
    ]
    
    results = []
    
    for text, expected_intent in test_cases:
        state = HiveMindState(
            task_id="test",
            master_task="",
            decomposition_reasoning="",
            subtasks=[],
            assignment_map={},
            worker_results={},
            final_result="",
            phase="",
            errors=[],
            message_id="msg_1",
            sender_id="user_1",
            message_text=text,
            conversation_id="conv_1",
            intent="",
            intent_confidence=0.0,
            response_text="",
            response_attachments=[],
            status_updates_sent=False
        )
        
        new_state = await classify_intent_node(state)
        predicted_intent = new_state.get("intent")
        
        print(f"Text: '{text}' => Expected: {expected_intent}, Got: {predicted_intent}", flush=True)
        results.append((text, expected_intent, predicted_intent))
        
    failures = [(t, e, p) for t, e, p in results if e != p]
    
    assert len(failures) == 0, f"Misclassified {len(failures)} intents: {failures}"

if __name__ == "__main__":
    asyncio.run(test_intent_classification())

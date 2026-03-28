import pytest
from backend.mind.prompt_loader import load_prompt

def test_load_existing_prompt():
    content = load_prompt("intent_classifier")
    assert content.startswith("# Intent Classifier Prompt")
    assert "information" in content

def test_load_non_existent_prompt():
    with pytest.raises(FileNotFoundError):
        load_prompt("this_prompt_does_not_exist")

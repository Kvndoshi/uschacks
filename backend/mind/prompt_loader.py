import os

_PROMPT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "prompts")

def load_prompt(prompt_name: str) -> str:
    """Load a system prompt from the prompts directory.
    
    Args:
        prompt_name: The name of the prompt (e.g. 'intent_classifier').
                     '.md' is automatically appended if not present.
    """
    if not prompt_name.endswith('.md'):
        prompt_name += '.md'
    
    path = os.path.join(_PROMPT_DIR, prompt_name)
    with open(path, 'r', encoding='utf-8') as f:
        return f.read().strip()

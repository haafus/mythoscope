import re
import logging

logger = logging.getLogger(__name__)


def load_prompts(filepath: str) -> dict:
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()

    
    text = re.sub(r'\n{3,}', '\n\n', text)

    prompts = {}
    
    sections = re.split(r'(Locations:|Time:|Characters:|Relations:)', text)

    current_key = None
    for part in sections:
        part = part.strip()
        if not part:
            continue

        if part in ['Locations:', 'Time:', 'Characters:', 'Relations:']:
            current_key = part.replace(':', '').lower()
        elif current_key:
            if current_key in prompts:
                prompts[current_key] += " " + part
            else:
                prompts[current_key] = part

    return prompts
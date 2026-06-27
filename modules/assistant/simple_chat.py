"""
Simple test version of the assistant
"""

import sys
from pathlib import Path

# Run from project root: python3 modules/assistant/simple_chat.py
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from core.ollama_brain import OllamaBrain


def simple_ask(question: str) -> str:
    """Simple version without system context"""
    brain = OllamaBrain()

    prompt = f"""
You are Aegis Assistant. Please answer this question concisely.

Question: {question}

Answer:
"""

    return brain.query(prompt)


if __name__ == "__main__":
    # Test
    response = simple_ask("What is Aegis?")
    print("Response:", response)

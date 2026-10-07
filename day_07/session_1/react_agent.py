"""
Day 7 - Session 1: Agent Fundamentals
Module: react_agent.py
Description: A bare ReAct loop (Thought, Action, Observation) in plain Python without any framework.
Roughly 60 to 80 lines of clean, self-contained code.
"""

import os, re, time
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv(override=True)
client = OpenAI(base_url=os.getenv("OPENAI_BASE_URL"), api_key=os.getenv("OPENAI_API_KEY"))
MODEL = os.getenv("OPENAI_MODEL", "gemini-3.1-flash-lite")

# 1. Plain Python Tools
def search(query: str) -> str:
    kb = {
        "apollo 11": "Apollo 11 launched July 16, 1969; landed on the Moon July 20, 1969.",
        "james webb": "The James Webb Space Telescope (JWST) launched December 25, 2021.",
        "curiosity rover": "NASA's Curiosity rover landed on Mars on August 6, 2012."
    }
    for key, val in kb.items():
        if key in query.lower():
            return val
    return f"No direct entry found for '{query}'. Try 'Apollo 11' or 'James Webb'."

def calculate(expression: str) -> str:
    try:
        sanitized = re.sub(r"[^0-9+\-*/(). ]", "", expression)
        return str(eval(sanitized, {"__builtins__": {}}, {}))
    except Exception as err:
        return f"Calculation error: {err}"

TOOLS = {"search": search, "calculate": calculate}

# 2. ReAct System Prompt (Reasoning + Acting)
SYSTEM_PROMPT = """You operate in a strict loop of Thought, Action, PAUSE, Observation.
At the end, output your Answer.
- Use Thought to describe your reasoning and plan.
- Use Action to run one available tool, then output PAUSE and STOP. Never output Observation yourself.
Available tools:
- search: Query factual database. (e.g., Action: search: Apollo 11)
- calculate: Compute mathematical expression. (e.g., Action: calculate: 2021 - 1969)

Format:
Question: {question}
Thought: {reasoning}
Action: {tool_name}: {input}
PAUSE
"""

ACTION_RE = re.compile(r"^Action:\s*(\w+):\s*(.*)$", re.MULTILINE | re.IGNORECASE)

# 3. The Bare ReAct Loop (~25 lines)
class BareReActAgent:
    def __init__(self, model: str = MODEL):
        self.model = model
        self.messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    def run(self, question: str, max_turns: int = 5) -> str:
        self.messages.append({"role": "user", "content": f"Question: {question}"})
        for turn in range(1, max_turns + 1):
            print(f"\n--- [ReAct Turn {turn}] ---", flush=True)
            res = client.chat.completions.create(model=self.model, messages=self.messages, stop=["Observation:", "PAUSE"])
            text = (res.choices[0].message.content or "").strip()
            print(text, flush=True)

            if "Answer:" in text:
                return text.split("Answer:")[-1].strip()

            match = ACTION_RE.search(text)
            if not match:
                return text  # Model completed response without explicit Answer tag

            tool_name, tool_arg = match.group(1).lower().strip(), match.group(2).strip()
            tool_fn = TOOLS.get(tool_name)
            observation = tool_fn(tool_arg) if tool_fn else f"Error: Unknown tool '{tool_name}'"
            print(f"\nObservation: {observation}", flush=True)

            self.messages.append({"role": "assistant", "content": text + "\nPAUSE"})
            self.messages.append({"role": "user", "content": f"Observation: {observation}"})
            time.sleep(2.0)

        return "Max turns reached without final answer."

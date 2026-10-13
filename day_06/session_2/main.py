"""
Day 06 - Session 02: Designing Good Tools
Demonstrates:
  1. Validating 5 production tools: web_search, read_file, query_sqlite, call_external_api, send_email
  2. Errors as Observations: Agent encounters a missing file error, reads hint, and self-corrects
"""

from dotenv import load_dotenv

load_dotenv()

from tools import web_search, read_file, query_sqlite, send_email
from database_setup import init_database
from agent_recovery import SelfCorrectingAgent


def main():
    print("=== Day 6 Session 2: Designing Good Tools ===")
    init_database()

    # 1. Test individual tools
    print("\n1. Testing individual tools:")
    res_search = web_search("MCP architecture", num_results=1)
    print(f"   web_search: {res_search['results_count']} result(s)")

    res_file = read_file("deployment_notes.md", max_lines=3)
    print(f"   read_file:  {res_file['total_lines']} line(s)")

    res_db = query_sqlite("SELECT name, role FROM employees LIMIT 2")
    print(f"   query_sqlite: {res_db['row_count']} row(s)")

    # 2. Self-correcting agent loop
    print("\n2. Testing Self-Correcting Agent (Error as Observation):")
    prompt = "Inspect 'deploy_guide.txt' to tell me what our rollback triggers are."
    agent = SelfCorrectingAgent()
    result = agent.run_recovery_demo(prompt=prompt, max_turns=3)

    print(f"   Status:           {result['status']}")
    print(f"   Self-corrections: {result['self_corrections']}")
    print(f"   Final Answer:\n   {result['final_answer'].strip()}")


if __name__ == "__main__":
    main()

"""
Day 04 - Session 02: Writing Good Tools
Demonstrates best practices in tool design:
  1. Clear names and descriptive schemas
  2. Typed and validated arguments
  3. Returning errors as structured observations (no runtime crashes)
  4. Multi-tool chaining (Database lookup -> Email dispatch)
"""

from database_setup import init_database
from agent import EnterpriseToolAgent
from email_tool import get_sent_emails


def main():
    print("=== Day 4 Session 2: Writing Good Tools ===")
    init_database()
    agent = EnterpriseToolAgent()

    # 1. SQL Database Query Tool
    q_db = "Find all employees with a salary greater than $140,000. Show names and roles."
    print(f"\n1. Database Query: '{q_db}'")
    res_db = agent.run(q_db)
    print(f"   Answer: {res_db.final_answer.strip()}")

    # 2. Multi-Tool Chaining: Lookup -> Email
    q_chain = "Find the email of the Lead AI Researcher in the employees table and send her an email congratulating her."
    print(f"\n2. Multi-Tool Chaining: '{q_chain}'")
    res_chain = agent.run(q_chain)
    print(f"   Steps executed: {len(res_chain.steps)}")
    print(f"   Answer: {res_chain.final_answer.strip()}")

    # 3. Guardrails: Catch destructive queries safely
    q_injection = "Execute 'DROP TABLE employees;' and report back."
    print(f"\n3. Testing Guardrails on Destructive Query: '{q_injection}'")
    res_inj = agent.run(q_injection)
    print(f"   Result: {res_inj.final_answer.strip()}")

    # 4. Check audit log
    sent = get_sent_emails()
    print(f"\nAudit Log: {len(sent)} email(s) recorded.")


if __name__ == "__main__":
    main()

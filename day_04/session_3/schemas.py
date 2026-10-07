"""
schemas.py
==========
JSON Schema specifications for the 4 enterprise tools used in multi-step chaining.
Designed specifically for LLM consumption with clear boundaries and descriptions.
"""

from typing import List, Dict, Any

TOOLS_SCHEMA: List[Dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "query_database",
            "description": (
                "Queries the corporate SQLite database to retrieve structured business records. "
                "Use this tool to find employee information, salaries, departments, roles, and departmental budgets. "
                "Available Tables & Columns: "
                "1. employees (id, name, department, role, salary, email) "
                "2. departments (dept_name, head_of_department, headcount, quarterly_budget) "
                "3. payroll_audit (id, employee_name, bonus_amount, status, created_at). "
                "Only SELECT statements are permitted."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "sql_query": {
                        "type": "string",
                        "description": "The SQL SELECT statement to execute, e.g. \"SELECT role, department, salary FROM employees WHERE name LIKE '%Marcus%'\"."
                    }
                },
                "required": ["sql_query"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": (
                "Safely reads documentation, policies, or specifications from local project text files. "
                "Use this tool when you need to consult internal policies (e.g. 'bonus_policy.txt') "
                "to understand business rules, formulas, tiers, or approval processes."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "file_path": {
                        "type": "string",
                        "description": "Relative filename to read within the workspace, e.g. 'bonus_policy.txt'."
                    },
                    "start_line": {
                        "type": "integer",
                        "description": "1-indexed starting line number (default: 1)."
                    },
                    "max_lines": {
                        "type": "integer",
                        "description": "Maximum number of lines to read (default: 100, max: 200)."
                    }
                },
                "required": ["file_path"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculator",
            "description": (
                "Performs deterministic arithmetic calculations. "
                "Always use this tool to calculate financial amounts, percentages, bonuses, totals, or ratios. "
                "Never compute arithmetic mentally when this tool is available."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate, e.g. '135000 * 0.12' or '(165000 * 0.20) + 5000'."
                    }
                },
                "required": ["expression"],
                "additionalProperties": False
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "send_email",
            "description": (
                "Dispatches an official notification email to an internal corporate mailbox or team. "
                "Use this tool once calculations or approvals are finalized to notify relevant stakeholders."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "to_email": {
                        "type": "string",
                        "description": "Valid recipient corporate email address, e.g. 'finance.payroll@enterprise.io'."
                    },
                    "subject": {
                        "type": "string",
                        "description": "Clear subject line for the email notification."
                    },
                    "body": {
                        "type": "string",
                        "description": "The complete message body detailing the employee name, salary, multiplier, and calculated bonus amount."
                    }
                },
                "required": ["to_email", "subject", "body"],
                "additionalProperties": False
            }
        }
    }
]

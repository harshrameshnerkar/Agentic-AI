"""
Day 02 - Session 01: Reasoning & Math Benchmark Dataset
========================================================
Multi-step reasoning problems involving arithmetic, order of operations, and constraints.
"""

from typing import List, Dict, Any

REASONING_DATASET: List[Dict[str, Any]] = [
    {
        "id": 1,
        "title": "Cloud Server Auto-Scaling Bill",
        "problem": (
            "A company runs 3 base servers 24 hours a day for 30 days at $0.50/hour each. "
            "During peak hours (4 hours every day for all 30 days), they spin up 5 additional servers "
            "at $0.80/hour each. They get a 10% volume discount on the total server usage bill before "
            "a fixed $50 maintenance fee is added. What is the final monthly bill in dollars?"
        ),
        "ground_truth": 1454.0,
        "tolerance": 0.05
    },
    {
        "id": 2,
        "title": "Warehouse Packaging & Pallet Logistics",
        "problem": (
            "A warehouse needs to ship 1,750 widgets. Each small box holds 12 widgets. "
            "Any leftover widgets that don't fill a full box are packed in a special padded envelope. "
            "Each pallet can hold up to 25 small boxes. Padded envelopes cannot be placed on pallets "
            "and are shipped as individual loose items. "
            "How many shipping containers total (pallets + loose small boxes not on pallets + padded envelopes) "
            "must be loaded onto the shipping truck?"
        ),
        "ground_truth": 26.0,
        "tolerance": 0.05
    },
    {
        "id": 3,
        "title": "Multi-Leg Flight Journey Duration",
        "problem": (
            "A traveler takes a multi-leg journey: Flight 1 takes 6 hours, followed by a 3-hour layover, "
            "and Flight 2 takes 7 hours. However, Flight 1 was delayed by 45 minutes on departure, "
            "reducing the layover time to 2 hours and 15 minutes because the connection was maintained. "
            "Flight 2 experienced a 30-minute headwind delay in the air. "
            "How many total elapsed hours (including delays and layovers) did the entire journey take "
            "from the scheduled departure time of Flight 1 to the actual wheels-down arrival of Flight 2? "
            "Provide the answer in total hours as a decimal."
        ),
        "ground_truth": 16.5,
        "tolerance": 0.05
    },
    {
        "id": 4,
        "title": "Factory Machine Defect Rate",
        "problem": (
            "Machine A produces 150 microchips per hour with a 6% defect rate and runs for an 8-hour shift. "
            "Machine B produces 200 microchips per hour with a 5% defect rate, but breaks down after running for only 5 hours. "
            "All defective chips are discarded. How many total non-defective (good) chips were produced across both machines?"
        ),
        "ground_truth": 2078.0,
        "tolerance": 0.05
    },
    {
        "id": 5,
        "title": "Subscription Downgrade Prorated Credit",
        "problem": (
            "A customer pays $90 upfront for a 30-day Premium plan. After exactly 10 days, they downgrade to a Basic plan "
            "($30 per 30-day cycle) for the remaining 20 days. The billing system calculates unused credit on Premium for the 20 days "
            "($90 * 20/30), subtracts the cost of the Basic plan for those 20 days ($30 * 20/30), and deducts a $5 downgrade "
            "administrative fee. What is the net dollar credit refunded to the customer?"
        ),
        "ground_truth": 35.0,
        "tolerance": 0.05
    },
    {
        "id": 6,
        "title": "Engineering Sprint Story Point Capacity",
        "problem": (
            "A software team has 6 engineers working 8 hours a day for a 10-day sprint. "
            "25% of all total engineering hours are reserved for meetings, reviews, and support. "
            "If an average story point takes 6 productive engineering hours to implement, "
            "how many story points can the team complete in the sprint?"
        ),
        "ground_truth": 60.0,
        "tolerance": 0.05
    }
]

# -*- coding: utf-8 -*-

"""
Test script for the BI Agent.

Usage:
    .venv/bin/python scripts/test_agent.py

Change the `request` variable at the bottom to test different queries.
"""

from learn_smb_lending_lens.one.api import one

# =============================================================================
# Test Requests - Onboarding & System Understanding (1-3)
# =============================================================================

# Understanding system capabilities
request_01 = """
What can you help me with? What are your main capabilities?
""".strip()

# Understanding database entities and relationships
request_02 = """
Can you explain the main entities in this database and how they relate to each other?
""".strip()

# Understanding the loan lifecycle workflow
request_03 = """
What does the loan application workflow look like? What statuses can an application and loan go through?
""".strip()

# =============================================================================
# Test Requests - Simple Queries (4-6)
# =============================================================================

# Simple count query
request_04 = """
How many loans do we have in total? Break it down by current status.
""".strip()

# Simple filter query
request_05 = """
Show me all Grade C loans. Include the loan number, business name, approved amount, and interest rate.
""".strip()

# Simple date filter query
request_06 = """
Show me loan applications submitted this month. Include the application number, business name, requested amount, and status.
""".strip()

# =============================================================================
# Test Requests - Medium Complexity (7-8)
# =============================================================================

# Join with filtering on risk factors
request_07 = """
Which loans are from high-risk industries (default_rate_baseline > 10%)? Show the loan number, business name, industry, outstanding balance, and the industry's baseline default rate.
""".strip()

# Aggregation with grouping
request_08 = """
What's the default rate for each risk grade? Show total loans, defaulted loans, actual default rate, and compare it to the implied default rate used in pricing.
""".strip()

# =============================================================================
# Test Requests - Complex Multi-Step Queries (9-10)
# =============================================================================

# Multiple joins + time calculation
request_09 = """
For loans that eventually defaulted, show me their payment behavior in the 90 days before default. Include the loan number, number of payments made, average days late, and count of late payments.
""".strip()

# Comprehensive summary requiring multiple queries
request_10 = """
Give me a portfolio health summary:
1. Total outstanding balance and number of active loans
2. Default rate by risk grade (actual vs implied)
3. Top 3 industries by portfolio concentration
4. Any loans with recent late payments (last 30 days) that I should monitor
""".strip()

# =============================================================================
# Run the selected request
# =============================================================================

# Change this to test different requests (request_01 to request_10)
request = request_01

one.agent(request)

# SMB Lending Lens

An AI Agent project for small-to-medium business (SMB) loan analytics at a fintech company.

## Overview

SMB Lending Lens is an AI-powered agent that helps fintech lending operations teams analyze and optimize their loan portfolio. Built on the Strands Agents SDK with AWS Bedrock, the agent can query a lending database, generate insights, and produce reports through natural language interaction.

The project is about a California-based fintech company specializing in SMB loans. The database covers the complete lending pipeline: applications, approvals, disbursements, repayments, and defaults across ~52,500 records.

## What the AI Agent Does

The agent performs five categories of analytical tasks:

### 1. Risk Pricing Analysis
Compares implied default rates (used in loan pricing) against actual default rates by risk grade. Identifies mispriced risk tiers where the company may be undercharging for actual risk exposure.

### 2. Portfolio Concentration Analysis
Analyzes loan distribution across industries to identify concentration risk. Helps ensure the portfolio isn't overexposed to any single sector that could cause cascading losses.

### 3. Approval Leakage Detection
Identifies "false rejections" — creditworthy applicants who were rejected but had profiles similar to successful borrowers. Quantifies potential revenue lost from overly conservative underwriting.

### 4. Early Warning Signal Detection
Analyzes payment behavior patterns (late payments, partial payments) in the months leading up to defaults. Enables proactive intervention before loans become delinquent.

### 5. Customer Lifecycle Value Comparison
Compares performance metrics between repeat customers and first-time borrowers, helping inform customer retention strategies and marketing budget allocation.

## Tech Stack

- **Agent Framework**: Strands Agents SDK
- **LLM Provider**: AWS Bedrock
- **Backend**: FastAPI (Python)
- **Frontend**: Next.js
- **Database**: PostgreSQL (NeonDB) / SQLite (local development)

## Database Schema

The lending database contains 10 tables with 12 foreign key relationships:

| Table | Description |
|-------|-------------|
| `industry` | Industry classification with baseline default rates |
| `risk_grade` | Risk tiers (A-E) with pricing and default assumptions |
| `loan_status` | Application and loan lifecycle states |
| `loan_officer` | Staff handling applications |
| `customer` | Business borrower profiles |
| `application` | Loan applications with decisions |
| `loan` | Approved and disbursed loans |
| `repayment_schedule` | Expected monthly payment schedules |
| `payment` | Actual payments received |
| `default_event` | Default records with recovery data |

"""
Synthetic PMO Data Generation Module.

Generates realistic project management office (PMO) portfolio datasets
utilizing Faker, NumPy, and Pandas. Produces enterprise-grade project metrics
including budgets, start and end dates, RAG health statuses, and assignments.
"""

import argparse
from datetime import datetime, timedelta
import logging
from pathlib import Path
import random
from typing import Optional

from faker import Faker
import numpy as np
import pandas as pd

# Configure structured logging for data engineering operations
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

# Standard enterprise project naming templates for realistic PMO data
PROJECT_PREFIXES = [
    "NextGen",
    "Cloud",
    "Global",
    "Enterprise",
    "Automated",
    "Strategic",
    "Agile",
    "Digital",
    "Unified",
    "Zero-Trust",
    "Data-Driven",
    "Smart",
    "Omni-Channel",
    "Sustainable",
]

PROJECT_DOMAINS = [
    "ERP Migration",
    "Cybersecurity Architecture",
    "Data Lakehouse Rollout",
    "Supply Chain Automation",
    "CRM Modernization",
    "Customer Self-Service Portal",
    "Payment Gateway Upgrade",
    "AI Analytics Engine",
    "DevOps Pipeline Optimization",
    "Infrastructure Modernization",
    "HR Talent Management Suite",
    "Financial Reporting Consolidation",
    "Warehouse Robotics Integration",
    "IoT Fleet Tracking System",
    "Compliance & Governance Framework",
    "Business Continuity Overhaul",
]

DEPARTMENTS = [
    "Information Technology",
    "Supply Chain & Logistics",
    "Finance & Controlling",
    "Operations & Manufacturing",
    "Digital Marketing & Sales",
    "Human Resources",
    "Engineering & R&D",
]

STRATEGIC_PRIORITIES = ["Critical", "High", "Medium", "Low"]
STATUS_OPTIONS = ["Active", "Planning", "Completed", "On Hold"]
RAG_OPTIONS = ["Green", "Amber", "Red"]


def get_default_data_directory() -> Path:
    """
    Resolve the default data directory relative to the repository root.

    Returns:
        Path: Path object pointing to the data/ directory.
    """
    # Navigate: src/generate_pmo_data.py -> src/ -> root -> data/
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    return data_dir


def generate_pmo_dataset(
    num_projects: int = 50,
    seed: Optional[int] = 42,
    output_path: Optional[Path] = None,
) -> pd.DataFrame:
    """
    Generate synthetic PMO portfolio records and optionally save them as a CSV.

    Args:
        num_projects: Total number of realistic PMO projects to generate.
        seed: Random seed for deterministic reproducibility.
        output_path: Target CSV file path. If None, saves to data/pmo_projects.csv.

    Returns:
        pd.DataFrame: Clean DataFrame containing all generated PMO portfolio data.
    """
    if seed is not None:
        random.seed(seed)
        np.random.seed(seed)
        Faker.seed(seed)

    fake = Faker("en_US")
    records = []

    # Reference timeline: anchor around current year for realistic active projects
    reference_date = datetime.now()

    # Pre-generate a consistent pool of project managers
    num_pms = max(5, num_projects // 6)
    project_managers = [fake.name() for _ in range(num_pms)]

    # Keep track of unique project names to prevent duplicates
    generated_names = set()

    for idx in range(1, num_projects + 1):
        # 1. Project Identifier
        project_id = f"PRJ-{1000 + idx}"

        # 2. Project Name Generation
        while True:
            prefix = random.choice(PROJECT_PREFIXES)
            domain = random.choice(PROJECT_DOMAINS)
            proj_name = f"{prefix} {domain}"
            if proj_name not in generated_names or len(generated_names) >= len(PROJECT_PREFIXES) * len(PROJECT_DOMAINS):
                generated_names.add(proj_name)
                break

        # 3. Department & Leadership
        department = random.choice(DEPARTMENTS)
        project_manager = random.choice(project_managers)
        priority = random.choices(
            STRATEGIC_PRIORITIES,
            weights=[0.20, 0.40, 0.30, 0.10],
            k=1,
        )[0]

        # 4. Status and Realistic Timeline
        # Distribution: 60% Active, 15% Planning, 15% Completed, 10% On Hold
        status = random.choices(
            STATUS_OPTIONS,
            weights=[0.60, 0.15, 0.15, 0.10],
            k=1,
        )[0]

        # Calculate project duration between 60 and 420 days
        duration_days = random.randint(60, 420)

        if status == "Completed":
            # Completed in the past: started 180 to 500 days ago
            days_ago = random.randint(180, 500)
            start_date = reference_date - timedelta(days=days_ago)
            end_date = start_date + timedelta(days=duration_days)
            completion_pct = 100
        elif status == "Planning":
            # Scheduled to start in the next 15 to 120 days
            start_offset = random.randint(15, 120)
            start_date = reference_date + timedelta(days=start_offset)
            end_date = start_date + timedelta(days=duration_days)
            completion_pct = 0
        elif status == "Active":
            # Started in the past 30 to 240 days, finishes in the future
            elapsed_days = random.randint(30, 240)
            start_date = reference_date - timedelta(days=elapsed_days)
            # Ensure duration is longer than elapsed so end_date is ahead
            duration_days = max(duration_days, elapsed_days + random.randint(20, 180))
            end_date = start_date + timedelta(days=duration_days)
            # Completion correlated with progress
            progress_ratio = elapsed_days / duration_days
            completion_pct = int(min(98, max(5, progress_ratio * 100 + random.uniform(-10, 10))))
        else:  # "On Hold"
            # Paused project
            elapsed_days = random.randint(40, 180)
            start_date = reference_date - timedelta(days=elapsed_days)
            end_date = start_date + timedelta(days=duration_days + 90)
            completion_pct = random.randint(10, 60)

        # 5. RAG Status (Red / Amber / Green)
        # RAG is conditionally influenced by project status and delays
        if status == "Completed":
            # Completed projects are predominantly Green
            rag_status = random.choices(RAG_OPTIONS, weights=[0.85, 0.12, 0.03], k=1)[0]
        elif status == "On Hold":
            # On hold projects are mostly Red or Amber
            rag_status = random.choices(RAG_OPTIONS, weights=[0.10, 0.40, 0.50], k=1)[0]
        else:
            # Active and Planning: healthy 65% Green, 22% Amber, 13% Red
            rag_status = random.choices(RAG_OPTIONS, weights=[0.65, 0.22, 0.13], k=1)[0]

        # 6. Financials: Planned Budget & Actual Cost Modeling
        # Realistic enterprise budget: between 50k and 1.8M EUR/USD
        planned_budget = round(random.randint(50, 1800) * 1000, -3)

        # Actual cost calculated based on completion percentage and RAG status:
        # Green: stays on or under budget (0.85 to 1.02 of expected progress spend)
        # Amber: minor budget overrun (1.03 to 1.18 of expected progress spend)
        # Red: major budget overrun or cost spikes (1.20 to 1.55 of expected progress spend)
        expected_base_spend = planned_budget * (completion_pct / 100.0)

        if rag_status == "Green":
            spend_factor = random.uniform(0.85, 1.02)
        elif rag_status == "Amber":
            spend_factor = random.uniform(1.03, 1.18)
        else:  # Red
            spend_factor = random.uniform(1.20, 1.50)

        if status == "Planning":
            actual_cost = 0.0
        else:
            # Compute actual cost and round to two decimal places
            actual_cost = round(max(5000.0, expected_base_spend * spend_factor), 2)
            # Cap actual cost to reasonable upper threshold for display
            actual_cost = min(actual_cost, round(planned_budget * 1.6, 2))

        records.append({
            "project_id": project_id,
            "project_name": proj_name,
            "department": department,
            "project_manager": project_manager,
            "status": status,
            "rag_status": rag_status,
            "strategic_priority": priority,
            "start_date": start_date.strftime("%Y-%m-%d"),
            "end_date": end_date.strftime("%Y-%m-%d"),
            "planned_budget": float(planned_budget),
            "actual_cost": float(actual_cost),
            "completion_percentage": int(completion_pct),
        })

    # Convert records into a structured Pandas DataFrame
    df = pd.DataFrame(records)

    # Determine destination output path
    if output_path is None:
        data_dir = get_default_data_directory()
        output_path = data_dir / "pmo_projects.csv"
    else:
        output_path = Path(output_path).resolve()

    # Safely create parent directories if they don't already exist
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Export DataFrame to CSV with utf-8 encoding
    df.to_csv(output_path, index=False, encoding="utf-8")
    logger.info(
        "Successfully generated %d synthetic PMO projects at '%s'",
        len(df),
        output_path,
    )

    return df


def parse_arguments() -> argparse.Namespace:
    """
    Parse command-line arguments for the synthetic data generator.

    Returns:
        argparse.Namespace: Parsed CLI argument values.
    """
    parser = argparse.ArgumentParser(
        description="Generate synthetic PMO portfolio data for Streamlit analytics."
    )
    parser.add_argument(
        "--num-projects",
        type=int,
        default=50,
        help="Number of synthetic PMO projects to generate (default: 50).",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for reproducible results (default: 42).",
    )
    parser.add_argument(
        "--output",
        type=str,
        default=None,
        help="Custom output file path for the generated CSV (default: data/pmo_projects.csv).",
    )
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_arguments()
    target_output = Path(args.output) if args.output else None
    generate_pmo_dataset(
        num_projects=args.num_projects,
        seed=args.seed,
        output_path=target_output,
    )

"""
Data Processing and Feature Engineering Module for the PMO Dashboard.

Loads PMO dataset records from the data/ folder, normalizes datatypes,
assigns standard RAG status color coding, and computes key portfolio metrics.
Features Streamlit data caching for optimized dashboard performance.
"""

from datetime import datetime
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import numpy as np
import pandas as pd

# Safe Streamlit import with fallback decorator for headless/CLI environments
try:
    import streamlit as st
    cache_data_decorator = st.cache_data
except ImportError:
    def cache_data_decorator(*args, **kwargs):
        """Fallback no-op caching decorator when streamlit is unavailable."""
        def decorator(func):
            return func
        return decorator

from src.generate_pmo_data import generate_pmo_dataset

# Configure module-level logging
logger = logging.getLogger(__name__)

# Standard PMO RAG Color Palette (Hex codes optimized for modern UX)
RAG_COLORS: Dict[str, str] = {
    "Green": "#10b981",  # Emerald Green - On Track
    "Amber": "#f59e0b",  # Amber/Yellow - Needs Attention
    "Red": "#ef4444",    # Crimson Red - Critical / Escalated
}

# Standard Status Color Palette
STATUS_COLORS: Dict[str, str] = {
    "Active": "#3b82f6",     # Blue
    "Planning": "#8b5cf6",   # Purple
    "Completed": "#10b981",  # Green
    "On Hold": "#6b7280",    # Gray
}

# Standard Strategic Priority Color Palette
PRIORITY_COLORS: Dict[str, str] = {
    "Critical": "#dc2626",
    "High": "#ea580c",
    "Medium": "#3b82f6",
    "Low": "#9ca3af",
}

PMO_DATA_FILENAME = "pmo_projects.csv"


def get_data_dir() -> Path:
    """
    Dynamically resolve the absolute path to the data directory.

    Returns:
        Path: Absolute path pointing to the data/ folder.
    """
    # Navigate: src/data_processing.py -> src/ -> root -> data/
    return Path(__file__).resolve().parent.parent / "data"


def ensure_dataset_exists(csv_path: Path) -> Path:
    """
    Verify that the PMO dataset CSV exists on disk, generating it if missing.

    Args:
        csv_path: Path to the expected CSV file.

    Returns:
        Path: Verified path to the existing CSV file.
    """
    if not csv_path.exists():
        logger.warning(
            "PMO dataset not found at '%s'. Automatically synthesizing initial data...",
            csv_path,
        )
        generate_pmo_dataset(num_projects=60, output_path=csv_path)
    return csv_path


@cache_data_decorator(show_spinner="Loading and transforming PMO portfolio records...")
def load_pmo_data(file_path: Optional[str] = None) -> pd.DataFrame:
    """
    Load PMO project data from CSV, sanitize datatypes, and derive key metrics.

    Decorated with @st.cache_data for instant interactive dashboard re-renders.

    Args:
        file_path: Optional custom path string to the CSV file. If None,
                   resolves to data/pmo_projects.csv.

    Returns:
        pd.DataFrame: Cleaned, validated, and enriched PMO DataFrame.
    """
    if file_path is None:
        target_path = get_data_dir() / PMO_DATA_FILENAME
    else:
        target_path = Path(file_path).resolve()

    # Guarantee dataset existence before reading
    ensure_dataset_exists(target_path)

    # Read CSV data into Pandas
    df = pd.read_csv(target_path, encoding="utf-8")

    # 1. Datetime Type Sanitization
    df["start_date"] = pd.to_datetime(df["start_date"], errors="coerce")
    df["end_date"] = pd.to_datetime(df["end_date"], errors="coerce")

    # Drop any records with unparseable dates
    df = df.dropna(subset=["start_date", "end_date"]).copy()

    # 2. Numeric Type Enforcement
    df["planned_budget"] = pd.to_numeric(df["planned_budget"], errors="coerce").fillna(0.0)
    df["actual_cost"] = pd.to_numeric(df["actual_cost"], errors="coerce").fillna(0.0)
    df["completion_percentage"] = (
        pd.to_numeric(df["completion_percentage"], errors="coerce")
        .fillna(0)
        .astype(int)
        .clip(0, 100)
    )

    # 3. String Trimming and Normalization
    string_cols = ["project_id", "project_name", "department", "project_manager", "status", "rag_status", "strategic_priority"]
    for col in string_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # 4. Standard RAG Status Color Assignment
    df["rag_color"] = df["rag_status"].map(RAG_COLORS).fillna("#9ca3af")
    df["status_color"] = df["status"].map(STATUS_COLORS).fillna("#6b7280")

    # 5. Derived Business Engineering Features
    # Project timeline duration in days
    df["duration_days"] = (df["end_date"] - df["start_date"]).dt.days

    # Financial Variance: Positive indicates budget surplus; Negative indicates budget overrun
    df["budget_variance"] = df["planned_budget"] - df["actual_cost"]

    # Budget Utilization %: (Actual / Planned) * 100
    df["budget_utilization_pct"] = np.where(
        df["planned_budget"] > 0,
        (df["actual_cost"] / df["planned_budget"]) * 100.0,
        0.0,
    )
    df["budget_utilization_pct"] = df["budget_utilization_pct"].round(1)

    # Health status flag for quick filtering
    df["is_over_budget"] = df["actual_cost"] > df["planned_budget"]

    # Sort deterministically by start_date ascending
    df = df.sort_values(by="start_date", ascending=True).reset_index(drop=True)

    return df


def filter_pmo_data(
    df: pd.DataFrame,
    selected_statuses: Optional[List[str]] = None,
    selected_rags: Optional[List[str]] = None,
    selected_managers: Optional[List[str]] = None,
    selected_departments: Optional[List[str]] = None,
    date_range: Optional[Tuple[datetime, datetime]] = None,
    search_query: Optional[str] = None,
) -> pd.DataFrame:
    """
    Apply multi-dimensional filters to the PMO DataFrame.

    Args:
        df: Input processed PMO DataFrame.
        selected_statuses: Filter list of project statuses.
        selected_rags: Filter list of RAG status values (Red, Amber, Green).
        selected_managers: Filter list of Project Managers.
        selected_departments: Filter list of Departments.
        date_range: Tuple of (start_date, end_date) to filter overlapping projects.
        search_query: Case-insensitive search string across project ID, name, or PM.

    Returns:
        pd.DataFrame: Filtered PMO DataFrame.
    """
    filtered = df.copy()

    # Filter by Status
    if selected_statuses:
        filtered = filtered[filtered["status"].isin(selected_statuses)]

    # Filter by RAG Health Status
    if selected_rags:
        filtered = filtered[filtered["rag_status"].isin(selected_rags)]

    # Filter by Project Manager
    if selected_managers:
        filtered = filtered[filtered["project_manager"].isin(selected_managers)]

    # Filter by Department
    if selected_departments:
        filtered = filtered[filtered["department"].isin(selected_departments)]

    # Filter by Active Date Range (project overlaps the selected window)
    if date_range and len(date_range) == 2 and date_range[0] and date_range[1]:
        start_bound = pd.to_datetime(date_range[0])
        end_bound = pd.to_datetime(date_range[1])
        # Project must not end before window start, and must not start after window end
        filtered = filtered[
            (filtered["end_date"] >= start_bound) & (filtered["start_date"] <= end_bound)
        ]

    # Filter by Free-text Search Query
    if search_query:
        query_lower = search_query.strip().lower()
        search_mask = (
            filtered["project_name"].str.lower().str.contains(query_lower, na=False)
            | filtered["project_id"].str.lower().str.contains(query_lower, na=False)
            | filtered["project_manager"].str.lower().str.contains(query_lower, na=False)
            | filtered["department"].str.lower().str.contains(query_lower, na=False)
        )
        filtered = filtered[search_mask]

    return filtered.reset_index(drop=True)


def calculate_portfolio_kpis(df: pd.DataFrame) -> Dict[str, float]:
    """
    Compute executive-level portfolio performance indicators.

    Args:
        df: Filtered or full PMO DataFrame.

    Returns:
        Dict[str, float]: Dictionary containing computed KPIs.
    """
    total_projects = len(df)
    if total_projects == 0:
        return {
            "total_projects": 0,
            "active_projects": 0,
            "total_planned_budget": 0.0,
            "total_actual_cost": 0.0,
            "budget_variance": 0.0,
            "overall_budget_utilization": 0.0,
            "avg_completion_pct": 0.0,
            "green_count": 0,
            "amber_count": 0,
            "red_count": 0,
            "portfolio_health_score": 0.0,
        }

    total_planned = float(df["planned_budget"].sum())
    total_actual = float(df["actual_cost"].sum())
    variance = total_planned - total_actual
    utilization = (total_actual / total_planned * 100.0) if total_planned > 0 else 0.0

    active_count = int((df["status"] == "Active").sum())
    green_count = int((df["rag_status"] == "Green").sum())
    amber_count = int((df["rag_status"] == "Amber").sum())
    red_count = int((df["rag_status"] == "Red").sum())

    health_score = (green_count / total_projects) * 100.0
    avg_completion = float(df["completion_percentage"].mean())

    return {
        "total_projects": total_projects,
        "active_projects": active_count,
        "total_planned_budget": total_planned,
        "total_actual_cost": total_actual,
        "budget_variance": variance,
        "overall_budget_utilization": round(utilization, 1),
        "avg_completion_pct": round(avg_completion, 1),
        "green_count": green_count,
        "amber_count": amber_count,
        "red_count": red_count,
        "portfolio_health_score": round(health_score, 1),
    }

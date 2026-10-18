"""
Unit and integration tests for the PMO Portfolio Management Dashboard.

Tests data generation, loading, data typing, RAG coloring, KPI calculations,
and multi-parameter filtering routines.
"""

from datetime import datetime
from pathlib import Path
import pandas as pd
import pytest

from src.data_processing import (
    RAG_COLORS,
    STATUS_COLORS,
    calculate_portfolio_kpis,
    filter_pmo_data,
    get_data_dir,
    load_pmo_data,
)
from src.generate_pmo_data import generate_pmo_dataset


@pytest.fixture
def temp_csv_path(tmp_path: Path) -> Path:
    """Fixture providing a temporary CSV path for testing."""
    return tmp_path / "test_pmo_projects.csv"


def test_generate_pmo_dataset(temp_csv_path: Path):
    """Verify synthetic dataset generation and CSV persistence."""
    df = generate_pmo_dataset(num_projects=25, seed=123, output_path=temp_csv_path)

    assert temp_csv_path.exists()
    assert len(df) == 25
    expected_cols = [
        "project_id",
        "project_name",
        "department",
        "project_manager",
        "status",
        "rag_status",
        "strategic_priority",
        "start_date",
        "end_date",
        "planned_budget",
        "actual_cost",
        "completion_percentage",
    ]
    for col in expected_cols:
        assert col in df.columns

    # Check value ranges
    assert (df["planned_budget"] >= 0).all()
    assert (df["actual_cost"] >= 0).all()
    assert (df["completion_percentage"].between(0, 100)).all()
    assert set(df["rag_status"].unique()).issubset({"Green", "Amber", "Red"})


def test_load_pmo_data(temp_csv_path: Path):
    """Verify data loading, datetime sanitization, and derived feature engineering."""
    generate_pmo_dataset(num_projects=15, seed=99, output_path=temp_csv_path)

    df_loaded = load_pmo_data(file_path=str(temp_csv_path))

    assert len(df_loaded) == 15
    # Verify Datetime conversion
    assert pd.api.types.is_datetime64_any_dtype(df_loaded["start_date"])
    assert pd.api.types.is_datetime64_any_dtype(df_loaded["end_date"])

    # Verify RAG colors mapping
    assert "rag_color" in df_loaded.columns
    for _, row in df_loaded.iterrows():
        assert row["rag_color"] == RAG_COLORS[row["rag_status"]]

    # Verify derived metrics
    assert "budget_variance" in df_loaded.columns
    assert "budget_utilization_pct" in df_loaded.columns
    assert "duration_days" in df_loaded.columns
    assert (df_loaded["duration_days"] > 0).all()


def test_filter_pmo_data(temp_csv_path: Path):
    """Test filtering by status, RAG, project manager, and search keyword."""
    generate_pmo_dataset(num_projects=30, seed=42, output_path=temp_csv_path)
    df = load_pmo_data(file_path=str(temp_csv_path))

    # 1. Filter by RAG status
    green_filtered = filter_pmo_data(df, selected_rags=["Green"])
    assert len(green_filtered) > 0
    assert (green_filtered["rag_status"] == "Green").all()

    # 2. Filter by status
    active_filtered = filter_pmo_data(df, selected_statuses=["Active"])
    assert len(active_filtered) > 0
    assert (active_filtered["status"] == "Active").all()

    # 3. Filter by search query
    first_name = df.iloc[0]["project_name"].split()[0]
    search_filtered = filter_pmo_data(df, search_query=first_name)
    assert len(search_filtered) >= 1
    assert any(first_name.lower() in name.lower() for name in search_filtered["project_name"])


def test_calculate_portfolio_kpis(temp_csv_path: Path):
    """Verify aggregated portfolio KPI computations and edge cases."""
    generate_pmo_dataset(num_projects=20, seed=77, output_path=temp_csv_path)
    df = load_pmo_data(file_path=str(temp_csv_path))

    kpis = calculate_portfolio_kpis(df)

    assert kpis["total_projects"] == 20
    assert kpis["total_planned_budget"] > 0
    assert kpis["portfolio_health_score"] >= 0 and kpis["portfolio_health_score"] <= 100
    assert kpis["green_count"] + kpis["amber_count"] + kpis["red_count"] == 20

    # Test empty dataframe handling
    empty_df = df.head(0)
    empty_kpis = calculate_portfolio_kpis(empty_df)
    assert empty_kpis["total_projects"] == 0
    assert empty_kpis["total_planned_budget"] == 0.0


def test_gantt_timeline_vertical_line_with_timestamp(temp_csv_path: Path):
    """Verify that Plotly timeline can add vertical line with native pd.Timestamp without TypeError."""
    import plotly.express as px

    generate_pmo_dataset(num_projects=10, seed=123, output_path=temp_csv_path)
    df = load_pmo_data(file_path=str(temp_csv_path))

    fig = px.timeline(
        df,
        x_start="start_date",
        x_end="end_date",
        y="project_name",
        color="rag_status",
        color_discrete_map=RAG_COLORS,
    )

    # Use native Timestamp object as fixed in app.py
    today_timestamp = pd.Timestamp.today().normalize()
    fig.add_vline(
        x=today_timestamp,
        line_width=2,
        line_dash="dash",
        line_color="#ef4444",
    )
    fig.add_annotation(
        x=today_timestamp,
        y=1.02,
        yref="paper",
        text="📍 Today",
        showarrow=False,
        font=dict(color="#ef4444", size=12),
        xanchor="left",
    )

    # Verify figure structure contains the shape and annotation
    assert len(fig.layout.shapes) == 1
    assert len(fig.layout.annotations) == 1
    assert fig.layout.shapes[0].line.color == "#ef4444"


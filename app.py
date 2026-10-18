"""
Streamlit Application: PMO Portfolio Management Dashboard.

An enterprise-grade Project Management Office (PMO) analytics application
providing portfolio health tracking, Gantt timeline scheduling, budget
utilization analysis, and interactive filtering.
"""

from datetime import datetime, date
from pathlib import Path
from typing import List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Import modular backend business logic and data engineering routines
from src.data_processing import (
    PRIORITY_COLORS,
    RAG_COLORS,
    STATUS_COLORS,
    calculate_portfolio_kpis,
    filter_pmo_data,
    get_data_dir,
    load_pmo_data,
)
from src.generate_pmo_data import generate_pmo_dataset

# ==============================================================================
# Page Configuration & Global Theme Settings
# ==============================================================================
st.set_page_config(
    page_title="PMO Portfolio Management Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Inject custom modern CSS styling for metric cards, status tags, and tabs
st.markdown(
    """
    <style>
    /* Executive Metric Card Custom Styling */
    div[data-testid="stMetric"] {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        border: 1px solid #e2e8f0;
        padding: 1.1rem;
        border-radius: 0.6rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
        transition: transform 0.15s ease-in-out, box-shadow 0.15s ease-in-out;
    }
    div[data-testid="stMetric"]:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06);
        border-color: #cbd5e1;
    }
    /* Tab Styling Enhancement */
    .stTabs [data-baseweb="tab-list"] {
        gap: 1.5rem;
        border-bottom: 2px solid #e2e8f0;
    }
    .stTabs [data-baseweb="tab"] {
        font-size: 1.05rem;
        font-weight: 600;
        padding: 0.75rem 1rem;
    }
    /* Expander Container Modern Border */
    .streamlit-expanderHeader {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        background-color: #f8fafc;
        border-radius: 0.5rem;
    }
    /* Status Badge Helpers */
    .badge-green {
        background-color: #d1fae5;
        color: #065f46;
        padding: 0.2rem 0.5rem;
        border-radius: 0.375rem;
        font-weight: 600;
    }
    .badge-amber {
        background-color: #fef3c7;
        color: #92400e;
        padding: 0.2rem 0.5rem;
        border-radius: 0.375rem;
        font-weight: 600;
    }
    .badge-red {
        background-color: #fee2e2;
        color: #991b1b;
        padding: 0.2rem 0.5rem;
        border-radius: 0.375rem;
        font-weight: 600;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==============================================================================
# Helper Functions
# ==============================================================================
def format_currency(value: float) -> str:
    """Format numerical values into human-readable currency strings ($/€)."""
    if abs(value) >= 1_000_000:
        return f"€{value / 1_000_000:.2f}M"
    if abs(value) >= 1_000:
        return f"€{value / 1_000:.1f}k"
    return f"€{value:,.0f}"


# ==============================================================================
# Data Loading & Initialization
# ==============================================================================
try:
    df_raw = load_pmo_data()
except Exception as err:
    st.error(f"Error loading PMO dataset: {err}")
    st.stop()


# ==============================================================================
# Sidebar: Dynamic Filters and Data Controls
# ==============================================================================
with st.sidebar:
    st.image(
        "https://raw.githubusercontent.com/feathericons/feather/master/icons/trello.svg",
        width=45,
    )
    st.title("PMO Portfolio Controls")
    st.markdown("Filter portfolio initiatives across health, status, and leadership.")
    st.markdown("---")

    # 1. Project Status Filter
    all_statuses = sorted(df_raw["status"].unique().tolist())
    selected_statuses = st.multiselect(
        "📌 Project Status",
        options=all_statuses,
        default=all_statuses,
        help="Filter projects by their lifecycle phase.",
    )

    # 2. RAG Health Status Filter
    all_rags = ["Green", "Amber", "Red"]
    selected_rags = st.multiselect(
        "🚦 RAG Health Status",
        options=all_rags,
        default=all_rags,
        help="Green: On Track | Amber: Attention Needed | Red: Escalated / Critical",
    )

    # 3. Project Manager Filter
    all_managers = sorted(df_raw["project_manager"].unique().tolist())
    selected_managers = st.multiselect(
        "👤 Project Manager",
        options=all_managers,
        default=[],
        placeholder="All Project Managers",
        help="Select specific PM leaders to review their assigned workload.",
    )

    # 4. Department / Business Unit Filter
    all_departments = sorted(df_raw["department"].unique().tolist())
    selected_departments = st.multiselect(
        "🏢 Department / Unit",
        options=all_departments,
        default=[],
        placeholder="All Departments",
        help="Filter by organizational business unit.",
    )

    # 5. Timeline Date Range Filter
    st.markdown("##### 📅 Timeline Horizon")
    min_calendar_date = df_raw["start_date"].min().date()
    max_calendar_date = df_raw["end_date"].max().date()

    date_selection = st.date_input(
        "Project Activity Range",
        value=(min_calendar_date, max_calendar_date),
        min_value=min_calendar_date,
        max_value=max_calendar_date,
        help="Filter initiatives scheduled to run within this selected date window.",
    )

    # Safe validation of date picker tuple
    if isinstance(date_selection, (tuple, list)) and len(date_selection) == 2:
        filter_date_range = (date_selection[0], date_selection[1])
    else:
        filter_date_range = None

    # 6. Global Search Filter
    search_query = st.text_input(
        "🔍 Keyword Search",
        placeholder="Search project name, ID, or manager...",
        help="Instant text filter across Project ID, Name, Department, and Manager.",
    )

    st.markdown("---")

    # Synthetic Data Regeneration Utility
    with st.expander("⚙️ Data Management"):
        st.caption("Re-synthesize PMO portfolio dataset with custom parameters.")
        num_gen = st.slider("Project Count", min_value=20, max_value=120, value=60, step=10)
        seed_gen = st.number_input("Random Seed", min_value=1, max_value=9999, value=42)
        if st.button("🔄 Generate New Data", use_container_width=True):
            with st.spinner("Synthesizing realistic PMO portfolio data..."):
                generate_pmo_dataset(
                    num_projects=num_gen,
                    seed=seed_gen,
                    output_path=get_data_dir() / "pmo_projects.csv",
                )
                st.cache_data.clear()
                st.success("New synthetic data created!")
                st.rerun()


# ==============================================================================
# Filter Execution
# ==============================================================================
df_filtered = filter_pmo_data(
    df=df_raw,
    selected_statuses=selected_statuses if selected_statuses else None,
    selected_rags=selected_rags if selected_rags else None,
    selected_managers=selected_managers if selected_managers else None,
    selected_departments=selected_departments if selected_departments else None,
    date_range=filter_date_range,
    search_query=search_query if search_query else None,
)

# Compute top-level portfolio performance indicators
kpis = calculate_portfolio_kpis(df_filtered)


# ==============================================================================
# Main Dashboard Header & Executive KPI Banner
# ==============================================================================
st.title("📊 PMO Portfolio Management Dashboard")
st.markdown(
    "Executive visibility into enterprise project timelines, health governance (RAG), "
    "and budget utilization."
)

if len(df_filtered) == 0:
    st.warning("⚠️ No project initiatives match the current filter selection. Please broaden your criteria.")
    st.stop()

# Render top-level KPI metrics cards
col_kpi1, col_kpi2, col_kpi3, col_kpi4, col_kpi5 = st.columns(5)

with col_kpi1:
    st.metric(
        label="Total Planned Budget",
        value=format_currency(kpis["total_planned_budget"]),
        help="Aggregated planned budget across all filtered projects.",
    )

with col_kpi2:
    st.metric(
        label="Total Actual Spend",
        value=format_currency(kpis["total_actual_cost"]),
        delta=f"{kpis['overall_budget_utilization']}% utilized",
        delta_color="off",
        help="Total recognized expenditure to date.",
    )

with col_kpi3:
    variance_val = kpis["budget_variance"]
    st.metric(
        label="Budget Variance",
        value=format_currency(variance_val),
        delta="Under Budget" if variance_val >= 0 else "Overrun",
        delta_color="normal" if variance_val >= 0 else "inverse",
        help="Planned budget minus actual cost (positive indicates budget surplus).",
    )

with col_kpi4:
    st.metric(
        label="Active Projects",
        value=f"{kpis['active_projects']} / {kpis['total_projects']}",
        delta=f"{(kpis['active_projects'] / kpis['total_projects'] * 100):.0f}% active" if kpis['total_projects'] > 0 else "0%",
        delta_color="off",
        help="Number of currently running initiatives vs total portfolio volume.",
    )

with col_kpi5:
    st.metric(
        label="Portfolio Health (Green)",
        value=f"{kpis['portfolio_health_score']}%",
        delta=f"{kpis['green_count']} on track",
        delta_color="normal" if kpis["portfolio_health_score"] >= 60 else "inverse",
        help="Percentage of initiatives operating in Green RAG status.",
    )

st.markdown("<br>", unsafe_allow_html=True)


# ==============================================================================
# Navigation Tabs
# ==============================================================================
tab_overview, tab_budget_health, tab_raw_data = st.tabs([
    "📈 Portfolio Overview",
    "💰 Budget & Health",
    "🔍 Raw Data Explorer",
])


# ==============================================================================
# TAB 1: Portfolio Overview (Timeline & Gantt Analysis)
# ==============================================================================
with tab_overview:
    st.subheader("🗓️ Project Portfolio Timeline & Gantt Schedule")
    st.markdown(
        "Interactive Gantt view showing the execution timeline, completion milestones, "
        "and RAG health classification of active and running projects."
    )

    # Sub-filter controls for Gantt chart view
    gantt_ctrl_col1, gantt_ctrl_col2 = st.columns([3, 1])

    with gantt_ctrl_col1:
        timeline_filter_mode = st.radio(
            "Timeline Filter:",
            options=["Running Projects Only (Active)", "All Filtered Statuses"],
            index=0,
            horizontal=True,
            help="Filter timeline strictly to active running initiatives or display all matching projects.",
        )

    with gantt_ctrl_col2:
        sort_order = st.selectbox(
            "Sort Schedule By:",
            options=["Start Date (Chronological)", "Completion % (Ascending)", "Planned Budget (Highest First)"],
            index=0,
        )

    # Prepare DataFrame for Gantt chart
    if timeline_filter_mode == "Running Projects Only (Active)":
        df_gantt = df_filtered[df_filtered["status"] == "Active"].copy()
    else:
        df_gantt = df_filtered.copy()

    if len(df_gantt) == 0:
        st.info("No initiatives found for the selected timeline criteria.")
    else:
        # Apply selected sorting
        if sort_order == "Start Date (Chronological)":
            df_gantt = df_gantt.sort_values(by="start_date", ascending=True)
        elif sort_order == "Completion % (Ascending)":
            df_gantt = df_gantt.sort_values(by="completion_percentage", ascending=True)
        else:
            df_gantt = df_gantt.sort_values(by="planned_budget", ascending=False)

        # Truncate view to top 30 projects if portfolio is excessively large for visual clarity
        max_gantt_display = 35
        if len(df_gantt) > max_gantt_display:
            st.caption(
                f"Showing first {max_gantt_display} initiatives out of {len(df_gantt)} total. "
                "Use sidebar filters to focus on specific departments or managers."
            )
            df_gantt = df_gantt.head(max_gantt_display)

        # Construct Plotly Gantt / Timeline visualization
        fig_gantt = px.timeline(
            df_gantt,
            x_start="start_date",
            x_end="end_date",
            y="project_name",
            color="rag_status",
            color_discrete_map=RAG_COLORS,
            category_orders={"rag_status": ["Green", "Amber", "Red"]},
            hover_name="project_name",
            hover_data={
                "project_id": True,
                "project_manager": True,
                "department": True,
                "status": True,
                "completion_percentage": ":.0f",
                "planned_budget": ":,.0f",
                "actual_cost": ":,.0f",
                "start_date": "|%Y-%m-%d",
                "end_date": "|%Y-%m-%d",
            },
            labels={
                "project_name": "Project Initiative",
                "rag_status": "RAG Health",
                "start_date": "Start Date",
                "end_date": "Target End Date",
                "completion_percentage": "Progress (%)",
            },
            title="Portfolio Gantt Schedule (Color-coded by RAG Health)",
        )

        # Invert Y-axis so first starting project is at the top
        fig_gantt.update_yaxes(autorange="reversed")

        # Add vertical marker indicating current date using a native datetime Timestamp object
        today_timestamp = pd.Timestamp.today().normalize()
        fig_gantt.add_vline(
            x=today_timestamp,
            line_width=2,
            line_dash="dash",
            line_color="#ef4444",
        )
        fig_gantt.add_annotation(
            x=today_timestamp,
            y=1.02,
            yref="paper",
            text="📍 Today",
            showarrow=False,
            font=dict(color="#ef4444", size=12),
            xanchor="left",
        )

        # Optimize layout for executive presentation
        fig_gantt.update_layout(
            height=max(480, len(df_gantt) * 26 + 120),
            margin=dict(l=20, r=30, t=50, b=30),
            xaxis_title="Timeline Calendar",
            yaxis_title=None,
            legend_title_text="RAG Health",
            plot_bgcolor="rgba(248, 250, 252, 0.6)",
            hoverlabel=dict(bgcolor="white", font_size=12),
        )

        st.plotly_chart(fig_gantt, use_container_width=True)

    # Portfolio Progress and Strategic Priority Breakdown
    st.markdown("---")
    st.subheader("🎯 Strategic Priority & Completion Progress")

    sum_col1, sum_col2 = st.columns([1, 1])

    with sum_col1:
        # Grouped completion rate by strategic priority
        priority_agg = (
            df_filtered.groupby("strategic_priority")
            .agg(
                Project_Count=("project_id", "count"),
                Avg_Completion=("completion_percentage", "mean"),
                Total_Budget=("planned_budget", "sum"),
            )
            .reindex(["Critical", "High", "Medium", "Low"])
            .dropna(how="all")
            .reset_index()
        )

        fig_priority = px.bar(
            priority_agg,
            x="strategic_priority",
            y="Avg_Completion",
            color="strategic_priority",
            color_discrete_map=PRIORITY_COLORS,
            text=priority_agg["Avg_Completion"].apply(lambda x: f"{x:.1f}%"),
            labels={
                "strategic_priority": "Strategic Priority",
                "Avg_Completion": "Avg Completion Rate (%)",
            },
            title="Average Completion Rate by Strategic Priority",
        )
        fig_priority.update_layout(
            yaxis_range=[0, 100],
            showlegend=False,
            height=320,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig_priority, use_container_width=True)

    with sum_col2:
        # Status distribution breakdown
        status_counts = df_filtered["status"].value_counts().reset_index()
        status_counts.columns = ["status", "count"]

        fig_status = px.bar(
            status_counts,
            x="count",
            y="status",
            orientation="h",
            color="status",
            color_discrete_map=STATUS_COLORS,
            text="count",
            labels={"count": "Number of Projects", "status": "Lifecycle Status"},
            title="Projects Count by Lifecycle Status",
        )
        fig_status.update_layout(
            showlegend=False,
            height=320,
            margin=dict(l=20, r=20, t=40, b=20),
        )
        st.plotly_chart(fig_status, use_container_width=True)


# ==============================================================================
# TAB 2: Budget & Health Analysis
# ==============================================================================
with tab_budget_health:
    st.subheader("💰 Portfolio Financials & Health Distribution")
    st.markdown(
        "Analyze capital allocation, budget variance risks, and project health governance."
    )

    bh_col1, bh_col2 = st.columns([1, 1])

    with bh_col1:
        # 1. RAG Health Distribution Donut Chart
        rag_summary = df_filtered["rag_status"].value_counts().reset_index()
        rag_summary.columns = ["rag_status", "count"]

        fig_donut = px.pie(
            rag_summary,
            names="rag_status",
            values="count",
            color="rag_status",
            color_discrete_map=RAG_COLORS,
            hole=0.55,
            title="Project Health Distribution (RAG Status)",
        )
        fig_donut.update_traces(
            textinfo="percent+label+value",
            textposition="inside",
            hovertemplate="<b>%{label}</b><br>Projects: %{value}<br>Share: %{percent}<extra></extra>",
        )
        fig_donut.update_layout(
            height=360,
            margin=dict(l=20, r=20, t=50, b=20),
            legend=dict(orientation="h", yanchor="bottom", y=-0.15, xanchor="center", x=0.5),
        )
        st.plotly_chart(fig_donut, use_container_width=True)

    with bh_col2:
        # 2. Planned Budget vs Actual Cost by Department
        dept_finance = (
            df_filtered.groupby("department")
            .agg(
                Planned_Budget=("planned_budget", "sum"),
                Actual_Cost=("actual_cost", "sum"),
            )
            .reset_index()
        )

        fig_dept_bar = go.Figure()
        fig_dept_bar.add_trace(
            go.Bar(
                name="Planned Budget",
                x=dept_finance["department"],
                y=dept_finance["Planned_Budget"],
                marker_color="#93c5fd",
            )
        )
        fig_dept_bar.add_trace(
            go.Bar(
                name="Actual Cost",
                x=dept_finance["department"],
                y=dept_finance["Actual_Cost"],
                marker_color="#2563eb",
            )
        )
        fig_dept_bar.update_layout(
            barmode="group",
            title="Planned Budget vs. Actual Spend by Department",
            xaxis_tickangle=-25,
            yaxis_title="Amount (€)",
            height=360,
            margin=dict(l=20, r=20, t=50, b=50),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        )
        st.plotly_chart(fig_dept_bar, use_container_width=True)

    st.markdown("---")

    # 3. Budget Utilization vs. Completion Scatter Analysis
    st.subheader("⚖️ Budget Utilization vs. Completion Progress")
    st.caption(
        "Identify high-risk initiatives: points in the upper-left quadrant reflect high budget burn "
        "with low milestone delivery."
    )

    fig_scatter = px.scatter(
        df_filtered,
        x="completion_percentage",
        y="budget_utilization_pct",
        color="rag_status",
        color_discrete_map=RAG_COLORS,
        size="planned_budget",
        size_max=24,
        hover_name="project_name",
        hover_data={
            "project_id": True,
            "project_manager": True,
            "department": True,
            "planned_budget": ":,.0f",
            "actual_cost": ":,.0f",
            "budget_utilization_pct": ":.1f",
            "completion_percentage": ":.0f",
        },
        labels={
            "completion_percentage": "Project Completion Progress (%)",
            "budget_utilization_pct": "Budget Utilization (% of Planned)",
            "rag_status": "RAG Status",
        },
        title="Project Risk Matrix: Budget Utilization vs. Progress",
    )

    # Add 100% budget threshold reference line
    fig_scatter.add_hline(
        y=100,
        line_width=1.5,
        line_dash="dot",
        line_color="#ef4444",
        annotation_text="100% Budget Threshold",
        annotation_position="bottom right",
    )

    fig_scatter.update_layout(
        height=420,
        margin=dict(l=20, r=20, t=50, b=20),
        plot_bgcolor="rgba(248, 250, 252, 0.6)",
    )
    st.plotly_chart(fig_scatter, use_container_width=True)

    # 4. Critical Projects Requiring PMO Intervention Callout
    critical_projects = df_filtered[
        (df_filtered["rag_status"] == "Red") | (df_filtered["budget_utilization_pct"] > 115)
    ]
    if len(critical_projects) > 0:
        st.warning(
            f"🚨 **PMO Attention Required**: {len(critical_projects)} projects currently operate "
            "with a Red RAG status or severe budget overrun (>115% utilization)."
        )
        cols_to_highlight = [
            "project_id",
            "project_name",
            "project_manager",
            "rag_status",
            "completion_percentage",
            "planned_budget",
            "actual_cost",
            "budget_utilization_pct",
        ]
        st.dataframe(
            critical_projects[cols_to_highlight].style.format({
                "planned_budget": "€{:,.0f}",
                "actual_cost": "€{:,.0f}",
                "budget_utilization_pct": "{:.1f}%",
                "completion_percentage": "{:.0f}%",
            }),
            use_container_width=True,
            hide_index=True,
        )


# ==============================================================================
# TAB 3: Raw PMO Data Explorer
# ==============================================================================
with tab_raw_data:
    st.subheader("📋 PMO Project Portfolio Records")
    st.markdown(
        "Inspect, search, and export the comprehensive underlying project records "
        "and financial metrics."
    )

    # As strictly specified: st.dataframe() inside st.expander("🔍 Explore Raw PMO Data")
    with st.expander("🔍 Explore Raw PMO Data", expanded=True):
        raw_header_col1, raw_header_col2 = st.columns([3, 1])

        with raw_header_col1:
            st.caption(
                f"Displaying **{len(df_filtered)}** of **{len(df_raw)}** total initiatives "
                "based on active sidebar filters."
            )

        with raw_header_col2:
            # CSV Download Button for Filtered Data
            csv_export = df_filtered.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 Export Filtered CSV",
                data=csv_export,
                file_name=f"pmo_portfolio_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True,
            )

        # Prepare formatted display table
        display_df = df_filtered[[
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
            "budget_variance",
            "budget_utilization_pct",
            "completion_percentage",
        ]].copy()

        # Render interactive table with custom Streamlit column configurations
        st.dataframe(
            display_df,
            column_config={
                "project_id": st.column_config.TextColumn("Project ID", width="small"),
                "project_name": st.column_config.TextColumn("Project Name", width="large"),
                "department": st.column_config.TextColumn("Department"),
                "project_manager": st.column_config.TextColumn("Project Manager"),
                "status": st.column_config.TextColumn("Status"),
                "rag_status": st.column_config.TextColumn("RAG Health"),
                "strategic_priority": st.column_config.TextColumn("Priority"),
                "start_date": st.column_config.DateColumn("Start Date", format="YYYY-MM-DD"),
                "end_date": st.column_config.DateColumn("Target End", format="YYYY-MM-DD"),
                "planned_budget": st.column_config.NumberColumn("Planned Budget", format="€%.0f"),
                "actual_cost": st.column_config.NumberColumn("Actual Cost", format="€%.0f"),
                "budget_variance": st.column_config.NumberColumn("Variance", format="€%.0f"),
                "budget_utilization_pct": st.column_config.NumberColumn("Utilization", format="%.1f%%"),
                "completion_percentage": st.column_config.ProgressColumn(
                    "Progress",
                    format="%d%%",
                    min_value=0,
                    max_value=100,
                ),
            },
            hide_index=True,
            use_container_width=True,
            height=480,
        )

# ==============================================================================
# Footer
# ==============================================================================
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: #64748b; font-size: 0.85rem;'>"
    "PMO Portfolio Management Dashboard • Built with Python, Streamlit, Pandas & Plotly • "
    f"Last refreshed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    "</div>",
    unsafe_allow_html=True,
)

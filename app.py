import os
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

DB_PATH = "campus_placements.db"
CSV_PATH = "indian_engineering_placement_2026.csv"

st.set_page_config(
    page_title="Placement Intelligence & Analytics Suite",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)


# DATABASE SETUP & EXECUTION HELPER

def init_db():
    if not os.path.exists(CSV_PATH):
        st.error(f"Source file '{CSV_PATH}' not found in the current directory.")
        st.stop()

    df = pd.read_csv(CSV_PATH)

    if "Open_Source_Contributions" in df.columns:
        df["Open_Source_Contributions"] = df["Open_Source_Contributions"].fillna(
            df["Open_Source_Contributions"].median()
        )

    if "LinkedIn_Activity_Score" in df.columns:
        df["LinkedIn_Activity_Score"] = df["LinkedIn_Activity_Score"].fillna(
            df["LinkedIn_Activity_Score"].median()
        )

    conn = sqlite3.connect(DB_PATH)
    df.to_sql("students", conn, if_exists="replace", index=False)
    cursor = conn.cursor()
    cursor.executescript("""
        CREATE INDEX IF NOT EXISTS idx_tier ON students(College_Tier);
        CREATE INDEX IF NOT EXISTS idx_branch ON students(Branch);
        CREATE INDEX IF NOT EXISTS idx_placement ON students(Placement_Status);
        CREATE INDEX IF NOT EXISTS idx_cgpa ON students(CGPA);
        CREATE INDEX IF NOT EXISTS idx_dsa ON students(DSA_Problems_Solved);
    """)
    conn.commit()
    conn.close()

if not os.path.exists(DB_PATH):
    with st.spinner("Initializing SQLite database..."):
        init_db()

def run_query(query: str, params: tuple = ()) -> pd.DataFrame:
    with sqlite3.connect(DB_PATH) as conn:
        return pd.read_sql_query(query, conn, params=params)


# DYNAMIC SIDEBAR FILTERS

st.sidebar.title("🎛️ Cohort Filters")

tier_opts = [r[0] for r in run_query(
    "SELECT DISTINCT College_Tier FROM students ORDER BY College_Tier"
).values]

branch_opts = [r[0] for r in run_query(
    "SELECT DISTINCT Branch FROM students ORDER BY Branch"
).values]

selected_tiers = st.sidebar.multiselect(
    "Institutional Tier", tier_opts, default=tier_opts
)

selected_branches = st.sidebar.multiselect(
    "Engineering Branch", branch_opts, default=branch_opts
)

cgpa_range = st.sidebar.slider(
    "CGPA Range", 5.0, 10.0, (5.0, 10.0), 0.1
)

min_dsa = st.sidebar.slider(
    "Min DSA Problems Solved", 0, 1200, 0, 50
)

if not selected_tiers or not selected_branches:
    st.warning("Please select at least one Tier and one Branch from the sidebar.")
    st.stop()

# Build SQL Parameterized Filter
tier_placeholders = ", ".join(["?"] * len(selected_tiers))
branch_placeholders = ", ".join(["?"] * len(selected_branches))

where_clause = f"""
    WHERE College_Tier IN ({tier_placeholders})
    AND Branch IN ({branch_placeholders})
    AND CGPA BETWEEN ? AND ?
    AND DSA_Problems_Solved >= ?
"""

filter_params = tuple(
    selected_tiers
    + selected_branches
    + [cgpa_range[0], cgpa_range[1], min_dsa]
)

# Load Cohort Data
cohort_data = run_query(
    f"SELECT * FROM students {where_clause};",
    filter_params
)

placed_cohort = cohort_data[
    cohort_data["Placement_Status"] == "Placed"
]

# ------------------------------------------------------------
# EXECUTIVE KPI METRICS
# ------------------------------------------------------------

st.title("🎓 Indian Engineering Placement Intelligence Suite")
st.caption("10 High-Dimensional Visualizations | Dynamic SQL Queries | Future Trends")

k1, k2, k3, k4 = st.columns(4)

total_count = len(cohort_data)
placed_count = len(placed_cohort)

rate = round((placed_count / total_count * 100), 2) if total_count > 0 else 0.0
avg_lpa = round(placed_cohort["Package_LPA"].mean(), 2) if placed_count > 0 else 0.0
peak_lpa = round(placed_cohort["Package_LPA"].max(), 2) if placed_count > 0 else 0.0

k1.metric("Active Cohort Size", f"{total_count:,}")
k2.metric("Placement Rate", f"{rate}%")
k3.metric("Avg Package (Placed)", f"₹ {avg_lpa} LPA")
k4.metric("Highest Package", f"₹ {peak_lpa} LPA")

st.divider()

# ------------------------------------------------------------
# 10 INTERACTIVE CHARTS ORGANIZED INTO THEMATIC TABS
# ------------------------------------------------------------

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "🎯 Core Drivers",
    "🏛️ Institutional & Branches",
    "📈 Skill Benchmarks",
    "🔮 Future Projections",
    "🖥️ SQL Sandbox"
])


# TAB 1: CORE DRIVERS


with tab1:
    c1, c2 = st.columns(2)

    with c1:
        st.subheader("1. Package (LPA) vs DSA Problems Solved")

        if not placed_cohort.empty:
            scatter_df = placed_cohort.sample(
                min(1500, len(placed_cohort)),
                random_state=42
            )

            fig1 = px.scatter(
                scatter_df,
                x="DSA_Problems_Solved",
                y="Package_LPA",
                color="College_Tier",
                size="GitHub_Contributions",
                size_max=16,
                opacity=0.75,
                color_discrete_map={
                    "Tier-1": "#1f77b4",
                    "Tier-2": "#ff7f0e",
                    "Tier-3": "#2ca02c"
                },
                labels={
                    "DSA_Problems_Solved": "DSA Problems",
                    "Package_LPA": "Package (LPA)"
                },
                title="<b>Problem Solving vs Compensation (Sized by GitHub Commits)</b>"
            )

            fig1.update_traces(
                customdata=scatter_df[
                    ["Student_ID", "Branch", "CGPA", "Internships_Count"]
                ].values,
                hovertemplate=(
                    "<b>ID:</b> %{customdata[0]}<br>"
                    "<b>Branch:</b> %{customdata[1]}<br>"
                    "<b>CGPA:</b> %{customdata[2]:.2f}<br>"
                    "<b>DSA Solved:</b> %{x}<br>"
                    "<b>Internships:</b> %{customdata[3]}<br>"
                    "<b>Package:</b> ₹%{y:.2f} LPA<extra></extra>"
                )
            )

            fig1.update_layout(template="plotly_white")
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.info("No placed records for scatter plot.")

    with c2:
        st.subheader("2. Placement Probability Matrix (Internships vs Projects)")

        pivot = cohort_data.pivot_table(
            index="Projects_Count",
            columns="Internships_Count",
            values="Placement_Status",
            aggfunc=lambda s: (s == "Placed").mean() * 100
        ).fillna(0)

        fig2 = px.imshow(
            pivot,
            text_auto=".1f",
            color_continuous_scale="Blues",
            labels=dict(
                x="Internships Completed",
                y="Projects Count",
                color="Placement Rate (%)"
            ),
            title="<b>Placement Rate Matrix (%): Projects vs. Internships</b>"
        )

        fig2.update_layout(template="plotly_white")
        st.plotly_chart(fig2, use_container_width=True)


# TAB 2: INSTITUTIONAL & BRANCH COMPARISONS


with tab2:
    c3, c4 = st.columns(2)

    with c3:
        st.subheader("3. Placement Conversion & Package by Branch")

        branch_summary = cohort_data.groupby(
            "Branch", observed=False
        ).agg(
            placement_rate=(
                "Placement_Status",
                lambda x: (x == "Placed").mean() * 100
            ),
            avg_package=(
                "Package_LPA",
                lambda x: x[x > 0].mean()
                if len(x[x > 0]) > 0 else 0
            )
        ).reset_index().sort_values(
            by="placement_rate",
            ascending=False
        )

        fig3 = px.bar(
            branch_summary,
            x="Branch",
            y="placement_rate",
            color="avg_package",
            color_continuous_scale="Viridis",
            text="placement_rate",
            labels={
                "placement_rate": "Placement Rate (%)",
                "avg_package": "Avg Placed LPA"
            },
            title="<b>Branch Success Rate & Starting CTC</b>"
        )

        fig3.update_traces(
            texttemplate="%{text:.1f}%",
            textposition="outside"
        )
        fig3.update_layout(
            yaxis=dict(range=[0, 110]),
            template="plotly_white"
        )
        st.plotly_chart(fig3, use_container_width=True)

    with c4:
        st.subheader("4. Package Spread by College Tier")

        if not placed_cohort.empty:
            fig4 = px.box(
                placed_cohort,
                x="College_Tier",
                y="Package_LPA",
                color="College_Tier",
                category_orders={
                    "College_Tier": ["Tier-1", "Tier-2", "Tier-3"]
                },
                labels={"Package_LPA": "Package (LPA)"},
                title="<b>Institutional Tier Salary Distributions & Outliers</b>"
            )

            fig4.update_layout(
                showlegend=False,
                template="plotly_white"
            )
            st.plotly_chart(fig4, use_container_width=True)
        else:
            st.info("No records available.")

    st.subheader("5. Student Flow Hierarchy: Tier → Branch → Status")

    sample_hierarchy = cohort_data.sample(
        min(4000, len(cohort_data)),
        random_state=42
    )

    fig5 = px.sunburst(
        sample_hierarchy,
        path=["College_Tier", "Branch", "Placement_Status"],
        values="CGPA",
        color="Package_LPA",
        color_continuous_scale="RdBu_r",
        title="<b>Multi-level Sunburst of Academic Hierarchy & Salary Concentration</b>"
    )

    fig5.update_layout(template="plotly_white")
    st.plotly_chart(fig5, use_container_width=True)


# TAB 3: SKILL BENCHMARKS & DENSITY


with tab3:
    c5, c6 = st.columns(2)

    with c5:
        st.subheader("6. Competency Radar: Elite (≥ 20 LPA) vs Baseline")

        radar_metrics = [
            "CGPA",
            "DSA_Problems_Solved",
            "Aptitude_Score",
            "Communication_Score",
            "Soft_Skills_Score"
        ]

        scaled_df = cohort_data.copy()
        scaled_df["CGPA"] = (scaled_df["CGPA"] / 10.0) * 100
        scaled_df["DSA_Problems_Solved"] = (
            scaled_df["DSA_Problems_Solved"] / 500.0
        ).clip(upper=1.0) * 100

        elite_means = scaled_df[
            scaled_df["Package_LPA"] >= 20.0
        ][radar_metrics].mean().tolist()

        base_means = scaled_df[radar_metrics].mean().tolist()

        radar_labels = [
            "CGPA (scaled)",
            "DSA (scaled)",
            "Aptitude",
            "Communication",
            "Soft Skills"
        ]

        radar_labels += [radar_labels[0]]
        elite_means += [elite_means[0] if elite_means else 0]
        base_means += [base_means[0] if base_means else 0]

        fig6 = go.Figure()

        fig6.add_trace(
            go.Scatterpolar(
                r=elite_means,
                theta=radar_labels,
                fill="toself",
                name="High Package (≥ 20 LPA)",
                line_color="#10B981"
            )
        )

        fig6.add_trace(
            go.Scatterpolar(
                r=base_means,
                theta=radar_labels,
                fill="toself",
                name="Cohort Average",
                line_color="#6366F1"
            )
        )

        fig6.update_layout(
            polar=dict(
                radialaxis=dict(
                    visible=True,
                    range=[0, 100]
                )
            ),
            title="<b>Holistic Skill Profile Comparison</b>",
            template="plotly_white"
        )

        st.plotly_chart(fig6, use_container_width=True)

    with c6:
        st.subheader("7. Package Distribution Density by Branch & Gender")

        if not placed_cohort.empty:
            fig7 = px.violin(
                placed_cohort,
                x="Branch",
                y="Package_LPA",
                color="Gender",
                box=True,
                points=False,
                color_discrete_map={
                    "Male": "#3B82F6",
                    "Female": "#EC4899"
                },
                title="<b>Compensation Density & Gender Parity</b>"
            )

            fig7.update_layout(template="plotly_white")
            st.plotly_chart(fig7, use_container_width=True)
        else:
            st.info("No data available.")

    st.subheader("8. Package Frequency & Density Distribution")

    if not placed_cohort.empty:
        fig8 = px.histogram(
            placed_cohort,
            x="Package_LPA",
            nbins=40,
            marginal="rug",
            color="College_Tier",
            title="<b>Distribution of Starting Compensation (LPA)</b>"
        )

        fig8.update_layout(template="plotly_white")
        st.plotly_chart(fig8, use_container_width=True)


# TAB 4: FUTURE PROJECTIONS & CONVERSION FUNNEL


with tab4:
    c7, c8 = st.columns(2)

    with c7:
        st.subheader("9. Future Projection: Skill-Driven Marginal Returns")

        if not placed_cohort.empty:
            dsa_bins = pd.cut(
                placed_cohort["DSA_Problems_Solved"],
                bins=range(0, 1200, 100)
            )

            dsa_pkg = (
                placed_cohort
                .groupby(
                    dsa_bins,
                    observed=False
                )["Package_LPA"]
                .mean()
                .reset_index()
            )

            dsa_pkg["bin_mid"] = [
                b.mid for b in dsa_pkg["DSA_Problems_Solved"]
            ]

            dsa_pkg = dsa_pkg.dropna()

            dsa_pkg["future_curve"] = (
                dsa_pkg["Package_LPA"]
                * (1 + (dsa_pkg["bin_mid"] / 1000) * 0.35)
            )

            fig9 = go.Figure()

            fig9.add_trace(
                go.Scatter(
                    x=dsa_pkg["bin_mid"],
                    y=dsa_pkg["Package_LPA"],
                    mode="lines+markers",
                    name="Current Cohort Baseline",
                    line=dict(color="#0284C7", width=3)
                )
            )

            fig9.add_trace(
                go.Scatter(
                    x=dsa_pkg["bin_mid"],
                    y=dsa_pkg["future_curve"],
                    mode="lines+markers",
                    name="Projected 2027–2028 Premium",
                    line=dict(color="#EF4444", dash="dash", width=3)
                )
            )

            fig9.update_layout(
                title="<b>Projected CTC Growth by DSA Milestone Solved</b>",
                xaxis_title="DSA Problems Solved Milestone",
                yaxis_title="Package (LPA)",
                template="plotly_white"
            )

            st.plotly_chart(fig9, use_container_width=True)
        else:
            st.info("Insufficient data for future projection.")

    with c8:
        st.subheader("10. Hiring Conversion Pipeline (Funnel)")

        # Calculate recruitment drop-off funnel
        n_total = len(cohort_data)

        n_cgpa = len(
            cohort_data[cohort_data["CGPA"] >= 7.0]
        )

        n_intern = len(
            cohort_data[
                (cohort_data["CGPA"] >= 7.0)
                & (cohort_data["Internships_Count"] >= 1)
            ]
        )

        n_dsa = len(
            cohort_data[
                (cohort_data["CGPA"] >= 7.0)
                & (cohort_data["Internships_Count"] >= 1)
                & (cohort_data["DSA_Problems_Solved"] >= 150)
            ]
        )

        n_placed = len(
            cohort_data[
                (cohort_data["CGPA"] >= 7.0)
                & (cohort_data["Internships_Count"] >= 1)
                & (cohort_data["DSA_Problems_Solved"] >= 150)
                & (cohort_data["Placement_Status"] == "Placed")
            ]
        )

        fig10 = go.Figure(
            go.Funnel(
                y=[
                    "Total Candidates",
                    "CGPA ≥ 7.0 (Shortlisted)",
                    "Internships ≥ 1",
                    "DSA ≥ 150 (Tech Rounds)",
                    "Placed Candidates"
                ],
                x=[
                    n_total,
                    n_cgpa,
                    n_intern,
                    n_dsa,
                    n_placed
                ],
                textinfo="value+percent initial"
            )
        )

        fig10.update_layout(
            title="<b>Student Transition Funnel Through Criteria</b>",
            template="plotly_white"
        )

        st.plotly_chart(fig10, use_container_width=True)


# TAB 5: AD-HOC SQL QUERY SANDBOX


with tab5:
    st.subheader("🖥️ Ad-Hoc SQL Execution Sandbox")

    st.markdown(
        "Run custom SQL queries with window functions directly against the `students` table."
    )

    default_sql = """SELECT
College_Tier,
COUNT(*) AS Total_Students,
ROUND(AVG(DSA_Problems_Solved), 0) AS Avg_DSA,
ROUND(100.0 * SUM(CASE WHEN Placement_Status = 'Placed' THEN 1 ELSE 0 END) / COUNT(*), 2) AS Placement_Rate_Pct,
ROUND(AVG(CASE WHEN Placement_Status = 'Placed' THEN Package_LPA ELSE NULL END), 2) AS Avg_Placed_Package_LPA
FROM students
GROUP BY College_Tier
ORDER BY Avg_Placed_Package_LPA DESC;"""

    user_sql = st.text_area(
        "SQL Editor:",
        value=default_sql,
        height=140
    )

    if st.button("Execute Query"):
        try:
            res_df = run_query(user_sql)
            st.dataframe(
                res_df,
                use_container_width=True
            )
            st.success(f"Returned {len(res_df)} rows.")
        except Exception as err:
            st.error(f"SQL Execution Error: {err}")

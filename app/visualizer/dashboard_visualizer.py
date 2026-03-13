import plotly.express as px
import streamlit as st


class DashboardVisualizer:
    @staticmethod
    def plot_metrics(df):
        st.subheader("Load Analysis and Training Zones")

        # 1. Line Chart: Fitness vs Fatigue
        fig_lines = px.line(
            df,
            y=["CTL", "ATL"],
            labels={"value": "Points", "index": "Date"},
            title="Fitness (Cronic Training Load - CTL) and Fatigue (Acute Training Load - ATL)",
        )
        st.plotly_chart(fig_lines, use_container_width=True)

        # 2. Zone Chart: Form State (TSB)
        # Define specific colors for the zones
        color_map = {
            "Transition (Fitness Loss)": "#FFA500",  # Orange
            "Freshness (Tapering/Race)": "#00FF00",  # Green
            "Neutral": "#808080",  # Gray
            "Optimal Training": "#1E90FF",  # Blue
            "High Risk (Overreaching)": "#FF0000",  # Red
        }

        fig_zones = px.bar(
            df,
            y="TSB",
            color="Status",
            title="Physical State Zones (TSB)",
            color_discrete_map=color_map,
        )

        # Add horizontal reference lines for clarity
        fig_zones.add_hline(
            y=5, line_dash="dash", line_color="green", annotation_text="Race"
        )
        fig_zones.add_hline(
            y=-30, line_dash="dash", line_color="red", annotation_text="Danger"
        )

        st.plotly_chart(fig_zones, use_container_width=True)

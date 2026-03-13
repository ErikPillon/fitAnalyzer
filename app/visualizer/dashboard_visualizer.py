import plotly.express as px
import streamlit as st


class DashboardVisualizer:
    @staticmethod
    def plot_metrics(df):
        st.subheader("Analisi del Carico e Zone di Allenamento")

        # 1. Grafico Linee: Fitness vs Fatica
        fig_lines = px.line(
            df,
            y=["CTL", "ATL"],
            labels={"value": "Punti", "index": "Data"},
            title="Fitness (Cronic Training Load - CTL) and Fatigue (Acute Training Load - ATL)",
        )
        st.plotly_chart(fig_lines, use_container_width=True)

        # 2. Grafico Zone: Stato della Forma (TSB)
        # Definiamo colori specifici per le zone
        color_map = {
            "Transition (Fitness Loss)": "#FFA500",  # Arancione
            "Freshness (Tapering/Race)": "#00FF00",  # Verde
            "Neutral": "#808080",  # Grigio
            "Optimal Training": "#1E90FF",  # Blu
            "High Risk (Overreaching)": "#FF0000",  # Rosso
        }

        fig_zones = px.bar(
            df,
            y="TSB",
            color="Status",
            title="Zone di Stato Fisico (TSB)",
            color_discrete_map=color_map,
        )

        # Aggiungiamo linee orizzontali di riferimento per chiarezza
        fig_zones.add_hline(
            y=5, line_dash="dash", line_color="green", annotation_text="Gara"
        )
        fig_zones.add_hline(
            y=-30, line_dash="dash", line_color="red", annotation_text="Pericolo"
        )

        st.plotly_chart(fig_zones, use_container_width=True)

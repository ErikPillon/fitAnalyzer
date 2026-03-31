import streamlit as st
import pandas as pd
import requests
from datetime import datetime
from visualizer.dashboard_visualizer import DashboardVisualizer

API_URL = "http://localhost:8000/api/analysis"

# --- STREAMLIT INTERFACE ---
def main():
    st.title("Triathlon Coach Dashboard 🏊‍♂️🚴‍♂️🏃‍♂️")
    st.write("Automatic analysis of .fit files in your sandbox")
    
    with st.spinner("Fetching and analyzing data from API..."):
        try:
            response = requests.get(API_URL)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch data from API: {e}")
            st.info("Make sure the FastAPI server is running (`uvicorn app.api:app --reload`)")
            return

    activities_data = data.get("activities", [])
    metrics_data = data.get("metrics", [])

    if not activities_data:
        st.info("No .fit files found in the sandbox folder or empty response from API.")
        return

    # Prepare data for display
    display_data = []
    for act in activities_data:
        timestamp_str = act['timestamp']
        try:
            date_obj = pd.to_datetime(timestamp_str)
        except Exception:
            date_obj = timestamp_str

        display_data.append(
            {
                "Type": act['name'],
                "Date": date_obj,
                "Duration (min)": round(act['duration_min'], 2),
                "Avg HR": act['avg_heart_rate'],
                "TRIMP (Est.)": round(act['trimp'], 2),
            }
        )

    # Show results in a table
    df_display = pd.DataFrame(display_data)
    st.dataframe(df_display)
    st.success(f"Successfully analyzed {len(activities_data)} files!")

    min_date = df_display['Date'].min()
    max_date = df_display['Date'].max()
    st.info(f"Analysis period: {min_date.date() if isinstance(min_date, pd.Timestamp) else min_date} - {max_date.date() if isinstance(max_date, pd.Timestamp) else max_date}")
    
    today = datetime.now()
    st.info(f"Today: {today}")

    # Timeseries chart
    activities_timeseries = df_display.set_index('Date')['TRIMP (Est.)']
    st.bar_chart(activities_timeseries)

    # Plot metrics
    if metrics_data:
        metrics_df = pd.DataFrame(metrics_data)
        metrics_df['date'] = pd.to_datetime(metrics_df['date'])
        metrics_df = metrics_df.set_index('date')
        DashboardVisualizer.plot_metrics(metrics_df)
    else:
        st.warning("No metrics data available.")


if __name__ == "__main__":
    main()

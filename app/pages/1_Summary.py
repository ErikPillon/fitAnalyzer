import pandas as pd
import requests
import streamlit as st

API_URL = "http://localhost:8000"


class MetricParser:
    def __init__(self, activities_df: pd.DataFrame):
        self.activities_df = activities_df.copy()

        if "timestamp" in self.activities_df.columns:
            self.activities_df["timestamp"] = pd.to_datetime(
                self.activities_df["timestamp"], errors="coerce"
            )

    def _reference_timestamp(self) -> pd.Timestamp:
        if (
            self.activities_df.empty
            or "timestamp" not in self.activities_df.columns
            or self.activities_df["timestamp"].dropna().empty
        ):
            return pd.Timestamp.today().normalize()
        return self.activities_df["timestamp"].max().normalize()

    def _weekly_activities(self) -> pd.DataFrame:
        if self.activities_df.empty or "timestamp" not in self.activities_df.columns:
            return self.activities_df.iloc[0:0]

        week_start = self._reference_timestamp() - pd.Timedelta(days=7)
        mask = (
            self.activities_df["timestamp"].ge(week_start)
            & self.activities_df["timestamp"].notna()
        )
        return self.activities_df.loc[mask]

    def get_time_this_week(self, activity_type=None):
        activities_df = self._weekly_activities()
        if activity_type is not None and "activity_type" in activities_df.columns:
            activities_df = activities_df[
                activities_df["activity_type"] == activity_type
            ]
        return float(activities_df.get("duration_min", pd.Series(dtype=float)).sum())

    def get_time_cycling(self):
        return self.get_time_this_week("cycling")

    def get_time_swimming(self):
        return self.get_time_this_week("swimming")

    def get_time_running(self):
        return self.get_time_this_week("running")

    def get_trimp_this_week(self):
        activities_df = self._weekly_activities()
        return float(activities_df.get("trimp", pd.Series(dtype=float)).sum())


@st.cache_data
def get_activities():
    with st.spinner("Fetching and analyzing data from API..."):
        try:
            response = requests.get(API_URL + "/api/analysis")
            response.raise_for_status()
            return response.json()
        except requests.exceptions.RequestException as e:
            st.error(f"Failed to fetch data from API: {e}")
            st.info(
                "Make sure the FastAPI server is running (`uvicorn app.api:app --reload`)"
            )
            return {"activities": [], "metrics": []}


def app():
    st.title("Activities Summary")

    data = get_activities()
    activities_data = data.get("activities", [])
    activities_df = pd.DataFrame(activities_data)
    parser = MetricParser(activities_df)

    if activities_df.empty:
        st.info("No activities available yet.")
        return

    time_week, time_cycling, time_swimming, time_running, trimp_week = st.columns(5)

    with time_week:
        st.metric("Time This Week", f"{parser.get_time_this_week() / 60:.1f} hrs")

    with time_cycling:
        st.metric("Time Cycling", f"{parser.get_time_cycling() / 60:.1f} hrs")

    with time_swimming:
        st.metric("Time Swimming", f"{parser.get_time_swimming() / 60:.1f} hrs")

    with time_running:
        st.metric("Time Running", f"{parser.get_time_running() / 60:.1f} hrs")

    with trimp_week:
        st.metric("TRIMP This Week", f"{parser.get_trimp_this_week():.1f}")


app()

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

    def _reference_activities(self, delta_days=7) -> pd.DataFrame:
        if self.activities_df.empty or "timestamp" not in self.activities_df.columns:
            return self.activities_df.iloc[0:0]

        week_start = self._reference_timestamp() - pd.Timedelta(days=delta_days)
        mask = (
            self.activities_df["timestamp"].ge(week_start)
            & self.activities_df["timestamp"].notna()
        )
        return self.activities_df.loc[mask]

    def get_time_this_week(self, activity_type=None):
        activities_df = self._reference_activities()
        if activity_type is not None and "activity_type" in activities_df.columns:
            activities_df = activities_df[
                activities_df["activity_type"] == activity_type
            ]
        return float(activities_df.get("duration_min", pd.Series(dtype=float)).sum())

    def get_time_last_two_weeks(self, activity_type=None):
        activities_df = self._reference_activities(delta_days=14)
        if activity_type is not None and "activity_type" in activities_df.columns:
            activities_df = activities_df[
                activities_df["activity_type"] == activity_type
            ]
        return float(activities_df.get("duration_min", pd.Series(dtype=float)).sum())

    def get_time_cycling(self) -> tuple[float, float]:
        return self.get_time_this_week("cycling"), self.get_time_last_two_weeks(
            "cycling"
        )

    def get_time_swimming(self) -> tuple[float, float]:
        return self.get_time_this_week("swimming"), self.get_time_last_two_weeks(
            "swimming"
        )

    def get_time_running(self) -> tuple[float, float]:
        return self.get_time_this_week("running"), self.get_time_last_two_weeks(
            "running"
        )

    def get_trimp_this_week(self) -> tuple[float, float]:
        activities_df = self._reference_activities()
        activities_2w_df = self._reference_activities(delta_days=14)
        return float(activities_df.get("trimp", pd.Series(dtype=float)).sum()), float(
            activities_2w_df.get("trimp", pd.Series(dtype=float)).sum()
        )


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
        this_week_time = parser.get_time_this_week()
        last_two_weeks_time = parser.get_time_last_two_weeks()
        st.metric(
            "Time This Week",
            f"{this_week_time / 60:.1f} hrs",
            delta=f"{(2 * this_week_time - last_two_weeks_time) / 60:.1f} hrs",
        )

    with time_cycling:
        this_week_time, last_two_weeks_time = parser.get_time_cycling()
        st.metric(
            "Time Cycling",
            f"{this_week_time / 60:.1f} hrs",
            delta=f"{(2 * this_week_time - last_two_weeks_time) / 60:.1f} hrs",
        )

    with time_swimming:
        this_week_time, last_two_weeks_time = parser.get_time_swimming()
        st.metric(
            "Time Swimming",
            f"{this_week_time / 60:.1f} hrs",
            delta=f"{(2 * this_week_time - last_two_weeks_time) / 60:.1f} hrs",
        )

    with time_running:
        this_week_time, last_two_weeks_time = parser.get_time_running()
        st.metric(
            "Time Running",
            f"{this_week_time / 60:.1f} hrs",
            delta=f"{(2 * this_week_time - last_two_weeks_time) / 60:.1f} hrs",
        )

    with trimp_week:
        this_week_time, last_two_weeks_time = parser.get_trimp_this_week()
        st.metric(
            "TRIMP This Week",
            f"{this_week_time:.1f}",
            delta=f"{(2 * this_week_time - last_two_weeks_time):.1f}",
        )


app()

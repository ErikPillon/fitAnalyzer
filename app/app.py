import streamlit as st
import os
from fitparse import FitFile
from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd
from engines.training_engine import TrainingEngine
from visualizer.dashboard_visualizer import DashboardVisualizer


# --- 1. ABSTRACT ACTIVITY CLASS ---
class Activity(ABC):
    def __init__(self, name, timestamp, duration_min, avg_heart_rate):
        self.name = name
        self.timestamp = timestamp
        self.duration_min = duration_min
        self.avg_heart_rate = avg_heart_rate
        self.trimp = self.calculate_trimp()

    @abstractmethod
    def calculate_trimp(self):
        """Each sport might have a different TRIMP multiplier."""
        # Simplified base formula: Duration (min) * Intensity (HR)
        trimp_normalizer = 1
        if self.avg_heart_rate:
            trimp_normalizer = self.avg_heart_rate / 100
        return self.duration_min * trimp_normalizer


# --- 2. SPECIFIC SUBCLASSES ---
class Run(Activity):
    def calculate_trimp(self):
        # Running is more impactful, we could weight the intensity more
        return super().calculate_trimp() * 1.2


class Cycling(Activity):
    def calculate_trimp(self):
        # Here you could add logic for Watts in the future
        return super().calculate_trimp() * 1.0


class Swim(Activity):
    def calculate_trimp(self):
        # Swimming has different cardio zones
        return super().calculate_trimp() * 0.8


# --- 3. STRATEGY PATTERN (FACTORY) ---
class ActivityFactory:
    @staticmethod
    def create_activity(file_path):
        fit_file = FitFile(file_path)

        # Extract basic data from 'session' messages in the .fit file
        data = {}
        for record in fit_file.get_messages("session"):
            for data_entry in record:
                data[data_entry.name] = data_entry.value

        # Retrieve key information
        sport = data.get("sport", "generic")
        start_time = data.get("start_time", datetime.now())
        duration = data.get("total_elapsed_time", 0) / 60  # convert to minutes
        avg_hr = data.get("avg_heart_rate", 0)

        # Creation logic (Strategy)
        if sport == "running":
            return Run("Running", start_time, duration, avg_hr)
        elif sport == "cycling":
            return Cycling("Cycling", start_time, duration, avg_hr)
        elif sport == "swimming":
            return Swim("Swimming", start_time, duration, avg_hr)
        else:
            return None


def initialize_session_state():
    folder_path = "./sandbox"  # Folder where you will put your .fit files
    if "activities" not in st.session_state:
        files = [f for f in os.listdir(folder_path) if f.endswith(".fit")]
        st.info(f"Sandbox folder: {folder_path} with {len(files)} .fit files found.")
        if not files:
            st.info("No .fit files found in the sandbox folder.")
            return

        activities_list = []
        for file in files:
            path = os.path.join(folder_path, file)
            activity_obj = ActivityFactory.create_activity(path)
            if activity_obj:
                activities_list.append(activity_obj)

        st.session_state.activities = activities_list


initialize_session_state()


# --- 4. STREAMLIT INTERFACE ---
def main():
    st.title("Triathlon Coach Dashboard 🏊‍♂️🚴‍♂️🏃‍♂️")
    st.write("Automatic analysis of .fit files in your sandbox")

    engine = TrainingEngine(st.session_state.activities)

    # Show results in a table
    display_data = []
    for act in st.session_state.activities:
        display_data.append(
            {
                "Type": act.name,
                "Date": act.timestamp,
                "Duration (min)": round(act.duration_min, 2),
                "Avg HR": act.avg_heart_rate,
                "TRIMP (Est.)": round(act.trimp, 2),
            }
        )

    st.dataframe(pd.DataFrame(display_data))
    st.success(f"Successfully analyzed {len(st.session_state.activities)} files!")

    min_date = min(act.timestamp for act in st.session_state.activities)
    max_date = max(act.timestamp for act in st.session_state.activities)
    st.info(f"Analysis period: {min_date} - {max_date}")
    today = datetime.now()
    st.info(f"Today: {today}")

    activities_timeseries = pd.Series(
        [act.trimp for act in st.session_state.activities],
        index=[act.timestamp for act in st.session_state.activities],
    )
    st.bar_chart(activities_timeseries)

    metrics_df = engine.get_training_metrics()
    DashboardVisualizer.plot_metrics(metrics_df)


if __name__ == "__main__":
    main()

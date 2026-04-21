import streamlit as st
import os
import pandas as pd
from fitparse import FitFile
import requests

API_URL = "http://localhost:8000"


def parse_fit_file(file_path):
    try:
        ff = FitFile(file_path)
        records = []
        for record in ff.get_messages("record"):
            r_dict = {}
            for data in record:
                r_dict[data.name] = data.value
            records.append(r_dict)
        return pd.DataFrame(records)
    except Exception as e:
        st.error(f"Error parsing .fit file: {e}")
        return pd.DataFrame()


def app():
    st.title("Single Activity")
    st.write("Select an activity from the dropdown to visualize its details.")

    sandbox_dir = "./sandbox"
    if not os.path.exists(sandbox_dir):
        st.error(f"Sandbox directory '{sandbox_dir}' not found.")
        return

    fit_files = [f for f in os.listdir(sandbox_dir) if f.endswith(".fit")]
    if not fit_files:
        st.warning("No .fit files found in the sandbox.")
        return

    # Add a selector as a dropdown menu
    selected_file = st.selectbox("Select an Activity", sorted(fit_files, reverse=True))

    # if selected_file:
    #     with st.spinner(f"Parsing {selected_file}..."):
    #         activity = requests.get(
    #             f"{API_URL}/api/single-activity/{selected_file}"
    #         ).json()

    #     st.subheader(f"Activity Details: {activity['name']}")
    #     st.write(f"Date: {activity['timestamp']}")
    #     st.write(f"Duration: {activity['duration_min']} minutes")
    #     st.write(f"Average Heart Rate: {activity['avg_heart_rate']} bpm")
    #     st.write(f"Estimated TRIMP: {activity['trimp']}")

    #     st.write("### Detailed Analysis and Visualizations")
    #     st.write()

    #     st.write(
    #         "Detailed analysis and visualizations will be implemented here in the future."
    #     )

    #     if "timestamp" in df.columns:
    #         df["timestamp"] = pd.to_datetime(df["timestamp"])
    #         df = df.set_index("timestamp")

    #     # 1. Heart rate history
    #     st.subheader("Heart Rate History")
    #     if "heart_rate" in df.columns and not df["heart_rate"].dropna().empty:
    #         st.line_chart(df["heart_rate"].dropna())
    #     else:
    #         st.info("No heart rate data available.")

    #     # 2. Elevation
    #     st.subheader("Elevation")
    #     elevation_col = (
    #         "enhanced_altitude"
    #         if "enhanced_altitude" in df.columns
    #         else "altitude"
    #         if "altitude" in df.columns
    #         else None
    #     )
    #     if elevation_col and not df[elevation_col].dropna().empty:
    #         st.line_chart(df[elevation_col].dropna())
    #     else:
    #         st.info("No elevation data available.")

    #     # 3. GPS track summary
    #     st.subheader("GPS Track Summary")
    #     if "position_lat" in df.columns and "position_long" in df.columns:
    #         # Drop NaN rows where coordinates are missing
    #         gps_df = df[["position_lat", "position_long"]].dropna()
    #         if not gps_df.empty:
    #             # Convert semicircles to degrees
    #             gps_df["lat"] = gps_df["position_lat"] * (180.0 / (2**31))
    #             gps_df["lon"] = gps_df["position_long"] * (180.0 / (2**31))
    #             st.map(gps_df[["lat", "lon"]])
    #         else:
    #             st.info("No valid GPS coordinates found.")
    #     else:
    #         st.info("No GPS track data available.")

    #     # 4. Velocity
    #     st.subheader("Velocity")
    #     speed_col = (
    #         "enhanced_speed"
    #         if "enhanced_speed" in df.columns
    #         else "speed"
    #         if "speed" in df.columns
    #         else None
    #     )
    #     if speed_col and not df[speed_col].dropna().empty:
    #         # Convert m/s to km/h for better readability
    #         speed_kmh = df[speed_col].dropna() * 3.6
    #         st.line_chart(speed_kmh)
    #         st.caption("Velocity is displayed in km/h.")
    #     else:
    #         st.info("No velocity data available.")


if __name__ == "__main__":
    app()

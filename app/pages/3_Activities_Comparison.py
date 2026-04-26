import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

API_URL = "http://localhost:8000"

st.set_page_config(page_title="Activities Comparison", layout="wide")

st.title("Activities Comparison")


@st.cache_data
def fetch_all_activities():
    try:
        response = requests.get(f"{API_URL}/api/analysis")
        response.raise_for_status()
        return response.json().get("activities", [])
    except Exception as e:
        st.error(f"Failed to fetch activities: {e}")
        return []


@st.cache_data
def fetch_activity(name):
    try:
        response = requests.get(f"{API_URL}/api/single-activity/{name}")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Failed to fetch activity {name}: {e}")
        return None


activities = fetch_all_activities()

if not activities:
    st.warning("No activities available to compare.")
    st.stop()


options = ["cycling", "running"]
selection = st.pills("Directions", options, selection_mode="single")
st.markdown(f"Your selected options: {selection}.")
activity_names = sorted(
    [act["name"] for act in activities if act["activity_type"] in selection]
)

col1, col2 = st.columns(2)

with col1:
    act1_name = st.selectbox("Select Activity 1", activity_names, index=0)

with col2:
    act2_name = st.selectbox(
        "Select Activity 2", activity_names, index=min(1, len(activity_names) - 1)
    )

if act1_name and act2_name:
    if act1_name == act2_name:
        st.warning("Please select two different activities to compare.")
    else:
        act1 = fetch_activity(act1_name)
        act2 = fetch_activity(act2_name)

        # Basic metrics
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)

        with col_m1:
            st.metric(
                "Duration (min)",
                f"{act1.get('duration_min', 0):.1f}",
                f"{act1.get('duration_min', 0) - act2.get('duration_min', 0):.1f}",
            )
        with col_m2:
            st.metric(
                "Distance (m)",
                f"{act1.get('distance', 0):.1f}",
                f"{act1.get('distance', 0) - act2.get('distance', 0):.1f}",
            )
        with col_m3:
            st.metric(
                "Avg Heart Rate",
                f"{act1.get('avg_heart_rate', 0):.0f}",
                f"{act1.get('avg_heart_rate', 0) - act2.get('avg_heart_rate', 0):.0f}",
            )
        with col_m4:
            cal1 = act1.get("calories") or 0
            cal2 = act2.get("calories") or 0
            st.metric("Calories", f"{cal1:.0f}", f"{cal1 - cal2:.0f}")

        st.markdown("---")

        est_trimp, est_vo2max = st.columns(2)

        with est_trimp:
            st.metric(
                "Estimated TRIMP",
                f"{act1.get('trimp', 0):.1f}",
                f"{act1.get('trimp', 0) - act2.get('trimp', 0):.1f}",
            )
        with est_vo2max:
            st.metric(
                "Estimated VO2max",
                f"{act1.get('vo2max', 0):.1f}",
                f"{act1.get('vo2max', 0) - act2.get('vo2max', 0):.1f}",
            )
        st.markdown("---")

        # Time series comparison
        def create_comparison_df(field, act1, act2):
            data1 = act1.get(field) or []
            data2 = act2.get(field) or []

            df1 = pd.DataFrame(
                {
                    field: data1,
                    "Activity": act1_name,
                    "Index": range(len(data1)),
                }
            )
            df2 = pd.DataFrame(
                {
                    field: data2,
                    "Activity": act2_name,
                    "Index": range(len(data2)),
                }
            )

            return pd.concat([df1, df2])

        # GPS Coordinates
        lat1 = act1.get("position_lat")
        lon1 = act1.get("position_long")
        lat2 = act2.get("position_lat")
        lon2 = act2.get("position_long")

        if lat1 and lon1 and lat2 and lon2:
            st.subheader("GPS Track Comparison")

            # Clean coordinates (convert to degrees)
            def clean_coords(lats, lons, name):
                df = pd.DataFrame({"lat": lats, "lon": lons, "Activity": name}).dropna()
                df["lat"] = df["lat"] * (180.0 / (2**31))
                df["lon"] = df["lon"] * (180.0 / (2**31))
                return df

            df_coords1 = clean_coords(lat1, lon1, act1_name)
            df_coords2 = clean_coords(lat2, lon2, act2_name)
            df_coords = pd.concat([df_coords1, df_coords2])

            if not df_coords.empty:
                fig = px.scatter_map(
                    df_coords,
                    lat="lat",
                    lon="lon",
                    color="Activity",
                    zoom=12,
                    height=500,
                )
                fig.update_layout(mapbox_style="open-street-map")
                fig.update_traces(marker=dict(size=4, opacity=0.7))
                st.plotly_chart(fig, width="stretch")

        col_chart1, col_chart2 = st.columns(2)

        with col_chart1:
            # Heart Rate
            if act1.get("heart_rate") and act2.get("heart_rate"):
                st.subheader("Heart Rate Comparison")
                df_hr = create_comparison_df("heart_rate", act1, act2)
                fig = px.line(
                    df_hr,
                    x="Index",
                    y="heart_rate",
                    color="Activity",
                    title="Heart Rate over Time",
                )
                st.plotly_chart(fig, width="stretch")

        with col_chart2:
            # Speed
            speed_col = "enhanced_speed" if act1.get("enhanced_speed") else "speed"
            if act1.get(speed_col) and act2.get(speed_col):
                st.subheader("Speed Comparison")
                df_speed = create_comparison_df(speed_col, act1, act2)
                fig = px.line(
                    df_speed,
                    x="Index",
                    y=speed_col,
                    color="Activity",
                    title="Speed over Time (m/s)",
                )
                st.plotly_chart(fig, width="stretch")

        col_chart3, col_chart4 = st.columns(2)

        with col_chart3:
            # Altitude
            alt_col = (
                "enhanced_altitude" if act1.get("enhanced_altitude") else "altitude"
            )
            if act1.get(alt_col) and act2.get(alt_col):
                st.subheader("Altitude Comparison")
                df_alt = create_comparison_df(alt_col, act1, act2)
                fig = px.line(
                    df_alt,
                    x="Index",
                    y=alt_col,
                    color="Activity",
                    title="Altitude over Time",
                )
                st.plotly_chart(fig, width="stretch")

        with col_chart4:
            # Power/Cadence
            if act1.get("power") and act2.get("power"):
                st.subheader("Power Comparison")
                df_pwr = create_comparison_df("power", act1, act2)
                fig = px.line(
                    df_pwr,
                    x="Index",
                    y="power",
                    color="Activity",
                    title="Power over Time",
                )
                st.plotly_chart(fig, width="stretch")
            elif act1.get("cadence") and act2.get("cadence"):
                st.subheader("Cadence Comparison")
                df_cad = create_comparison_df("cadence", act1, act2)
                fig = px.line(
                    df_cad,
                    x="Index",
                    y="cadence",
                    color="Activity",
                    title="Cadence over Time",
                )
                st.plotly_chart(fig, width="stretch")

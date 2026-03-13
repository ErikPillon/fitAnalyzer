import streamlit as st
import os
from fitparse import FitFile
from abc import ABC, abstractmethod
from datetime import datetime
import pandas as pd
from engines.training_engine import TrainingEngine
from visualizer.dashboard_visualizer import DashboardVisualizer


# --- 1. CLASSE ASTRATTA ACTIVITY ---
class Activity(ABC):
    def __init__(self, name, timestamp, duration_min, avg_heart_rate):
        self.name = name
        self.timestamp = timestamp
        self.duration_min = duration_min
        self.avg_heart_rate = avg_heart_rate
        self.trimp = self.calculate_trimp()

    @abstractmethod
    def calculate_trimp(self):
        """Ogni sport potrebbe avere un moltiplicatore TRIMP diverso."""
        # Formula base semplificata: Durata (min) * Intensità (HR)
        trimp_normalizer = 1
        if self.avg_heart_rate:
            trimp_normalizer = self.avg_heart_rate / 100
        return self.duration_min * trimp_normalizer


# --- 2. SOTTOCLASSI SPECIFICHE ---
class Run(Activity):
    def calculate_trimp(self):
        # La corsa è più impattante, potremmo pesare di più l'intensità
        return super().calculate_trimp() * 1.2


class Cycling(Activity):
    def calculate_trimp(self):
        # Qui potresti aggiungere logica per i Watt in futuro
        return super().calculate_trimp() * 1.0


class Swim(Activity):
    def calculate_trimp(self):
        # Il nuoto ha zone cardio diverse
        return super().calculate_trimp() * 0.8


# --- 3. STRATEGY PATTERN (FACTORY) ---
class ActivityFactory:
    @staticmethod
    def create_activity(file_path):
        fit_file = FitFile(file_path)

        # Estraiamo i dati base dai messaggi 'session' del file .fit
        data = {}
        for record in fit_file.get_messages("session"):
            for data_entry in record:
                data[data_entry.name] = data_entry.value

        # Recupero informazioni chiave
        sport = data.get("sport", "generic")
        start_time = data.get("start_time", datetime.now())
        duration = data.get("total_elapsed_time", 0) / 60  # convertiamo in minuti
        avg_hr = data.get("avg_heart_rate", 0)

        # Logica di creazione (Strategy)
        if sport == "running":
            return Run("Corsa", start_time, duration, avg_hr)
        elif sport == "cycling":
            return Cycling("Bici", start_time, duration, avg_hr)
        elif sport == "swimming":
            return Swim("Nuoto", start_time, duration, avg_hr)
        else:
            return None


def initialize_session_state():
    folder_path = "./sandbox"  # Cartella dove metterai i tuoi file .fit
    if "activities" not in st.session_state:
        files = [f for f in os.listdir(folder_path) if f.endswith(".fit")]
        st.info(f"Cartella sandbox: {folder_path} con {len(files)} file .fit trovati.")
        if not files:
            st.info("Nessun file .fit trovato nella cartella sandbox.")
            return

        activities_list = []
        for file in files:
            path = os.path.join(folder_path, file)
            activity_obj = ActivityFactory.create_activity(path)
            if activity_obj:
                activities_list.append(activity_obj)

        st.session_state.activities = activities_list


initialize_session_state()


# --- 4. INTERFACCIA STREAMLIT ---
def main():
    st.title("Triathlon Coach Dashboard 🏊‍♂️🚴‍♂️🏃‍♂️")
    st.write("Analisi automatica dei file .fit della tua sandbox")

    engine = TrainingEngine(st.session_state.activities)

    # Mostriamo i risultati in una tabella
    display_data = []
    for act in st.session_state.activities:
        display_data.append(
            {
                "Tipo": act.name,
                "Data": act.timestamp,
                "Durata (min)": round(act.duration_min, 2),
                "HR Media": act.avg_heart_rate,
                "TRIMP (Est.)": round(act.trimp, 2),
            }
        )

    st.dataframe(pd.DataFrame(display_data))
    st.success(f"Analizzati correttamente {len(st.session_state.activities)} file!")

    min_date = min(act.timestamp for act in st.session_state.activities)
    max_date = max(act.timestamp for act in st.session_state.activities)
    st.info(f"Periodo di analisi: {min_date} - {max_date}")
    today = datetime.now()
    st.info(f"Oggi: {today}")

    activities_timeseries = pd.Series(
        [act.trimp for act in st.session_state.activities],
        index=[act.timestamp for act in st.session_state.activities],
    )
    st.bar_chart(activities_timeseries)

    metrics_df = engine.get_training_metrics()
    DashboardVisualizer.plot_metrics(metrics_df)


if __name__ == "__main__":
    main()

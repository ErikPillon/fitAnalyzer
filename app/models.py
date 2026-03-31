from abc import ABC, abstractmethod
from datetime import datetime
import os
from fitparse import FitFile


# --- 1. ABSTRACT ACTIVITY CLASS ---
class Activity(ABC):
    def __init__(self, name, timestamp, duration_min, avg_heart_rate, **kwargs):
        self.name = name
        self.timestamp = timestamp
        self.duration_min = duration_min
        self.avg_heart_rate = avg_heart_rate
        self.hr = kwargs.get("heart_rate", None)
        self.altitude = kwargs.get("altitude", None)
        self.speed = kwargs.get("speed", None)
        self.watts = kwargs.get("watts", None)
        self.distance = kwargs.get("distance", None)
        self.calories = kwargs.get("calories", None)
        self.temperature = kwargs.get("temperature", None)
        self.cadence = kwargs.get("cadence", None)
        self.power = kwargs.get("power", None)
        self.heart_rate = kwargs.get("heart_rate", None)
        self.enhanced_altitude = kwargs.get("enhanced_altitude", None)
        self.enhanced_speed = kwargs.get("enhanced_speed", None)
        self.trimp = self.calculate_trimp()

    @abstractmethod
    def __dict__(self):
        return {
            "name": self.name,
            "timestamp": self.timestamp,
            "duration_min": self.duration_min,
            "avg_heart_rate": self.avg_heart_rate,
            "trimp": self.trimp,
            "watts": self.watts,
            "distance": self.distance,
            "calories": self.calories,
        }

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

        raw_records = list(fit_file.get_messages("record"))

        entities = [
            "timestamp",
            "heart_rate",
            "altitude",
            "speed",
            "watts",
            "distance",
            "calories",
            "temperature",
            "cadence",
            "power",
            "enhanced_altitude",
            "enhanced_speed",
        ]

        parsed_records = list(ActivityFactory.parse_records(raw_records, entities))

        # Sort by timestamp
        parsed_records = [r for r in parsed_records if r.get("timestamp") is not None]
        parsed_records.sort(key=lambda x: x["timestamp"])

        # Aggregate metrics
        metric_names = [e for e in entities if e != "timestamp"]
        metrics = {e: [] for e in metric_names}
        for r in parsed_records:
            for e in metric_names:
                metrics[e].append(r.get(e))

        # Add parsed metrics to data dictionary to be passed as kwargs
        data.update(metrics)

        # Retrieve key information
        file_name = os.path.basename(file_path)
        sport = data.get("sport", "generic")
        start_time = data.get("start_time", datetime.now())
        duration = data.get("total_elapsed_time", 0) / 60  # convert to minutes
        avg_hr = data.get("avg_heart_rate", 0)

        # Creation logic (Strategy)
        if sport == "running":
            return Run(file_name, start_time, duration, avg_hr, **data)
        elif sport == "cycling":
            return Cycling(file_name, start_time, duration, avg_hr, **data)
        elif sport == "swimming":
            return Swim(file_name, start_time, duration, avg_hr, **data)
        else:
            return None

    @staticmethod
    def parse_records(
        records,
        entities=[
            "timestamp",
            "heart_rate",
            "altitude",
            "speed",
            "watts",
            "distance",
            "calories",
            "temperature",
            "cadence",
            "power",
            "enhanced_altitude",
            "enhanced_speed",
        ],
    ):
        for record in records:
            r_dict = {}
            for data in record:
                if data.name in entities:
                    r_dict[data.name] = data.value
            yield r_dict

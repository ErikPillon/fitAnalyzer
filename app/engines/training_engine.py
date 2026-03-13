import pandas as pd


class TrainingEngine:
    def __init__(self, activities_list):
        self.activities = activities_list

    def get_training_metrics(self):
        data = []
        for act in self.activities:
            data.append({"date": act.timestamp.date(), "trimp": act.trimp})

        df = pd.DataFrame(data)
        if df.empty:
            return pd.DataFrame()

        df = df.groupby("date")["trimp"].sum().reset_index()
        df["date"] = pd.to_datetime(df["date"])
        df = df.set_index("date").sort_index()

        # Riempimento giorni vuoti per continuità temporale
        all_days = pd.date_range(start=df.index.min(), end=df.index.max(), freq="D")
        df = df.reindex(all_days, fill_value=0)

        # Calcolo ATL e CTL (Medie mobili esponenziali)
        df["ATL"] = df["trimp"].ewm(span=7, adjust=False).mean()
        df["CTL"] = df["trimp"].ewm(span=42, adjust=False).mean()
        df["TSB"] = df["CTL"] - df["ATL"]

        # Aggiunta delle zone di stato fisico
        df["Status"] = df["TSB"].apply(self._get_zone_label)

        return df

    def _get_zone_label(self, tsb):
        """Soglie standard per il TSB (Training Stress Balance)"""
        if tsb > 25:
            return "Transition (Perdita Fitness)"
        elif 5 < tsb <= 25:
            return "Freshness (Tapering/Gara)"
        elif -10 <= tsb <= 5:
            # Zona Neutra
            return "Neutral"
        elif -30 <= tsb < -10:
            return "Optimal Training"
        else:
            # TSB < -30
            return "High Risk (Overreaching)"

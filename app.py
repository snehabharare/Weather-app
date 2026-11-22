"""
Weather App with Live OpenWeather API
A Tkinter desktop app showing current weather and a 5-day forecast.

Setup:
  1. Install dependencies: python -m pip install -r requirements.txt
  2. Copy .env.example to .env and add your OpenWeather API key.
  3. Run: python app.py
"""

import os
import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime
from dotenv import load_dotenv
import requests

load_dotenv()
API_KEY = os.getenv("OPENWEATHER_API_KEY", "").strip()
CURRENT_URL = "https://api.openweathermap.org/data/2.5/weather"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"
TIMEOUT_SECONDS = 10
CACHE_SECONDS = 300  # Briefly cache the same city to avoid unnecessary API calls.
_cache = {}


def fetch_json(url, params):
    """Request JSON from OpenWeather and provide readable error messages."""
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
        if response.status_code == 401:
            raise RuntimeError(
                "The API key was rejected. Check your .env file. "
                "A newly created key may take a little time to activate."
            )
        if response.status_code == 404:
            raise RuntimeError("City not found. Check the spelling and try again.")
        if response.status_code == 429:
            raise RuntimeError("The API request limit was reached. Please wait and retry.")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.Timeout:
        raise RuntimeError("The weather service took too long to respond. Try again.")
    except requests.exceptions.ConnectionError:
        raise RuntimeError("No internet connection. Check your connection and retry.")
    except requests.exceptions.HTTPError as exc:
        raise RuntimeError(f"Weather service error: {exc}") from exc
    except requests.exceptions.RequestException as exc:
        raise RuntimeError(f"Could not contact the weather service: {exc}") from exc


def get_weather(city):
    """Get current conditions and forecast, using a short in-memory cache."""
    key = city.casefold()
    now = datetime.now().timestamp()
    if key in _cache and now - _cache[key]["saved_at"] < CACHE_SECONDS:
        return _cache[key]["data"]

    common = {"q": city, "appid": API_KEY, "units": "metric"}
    current = fetch_json(CURRENT_URL, common)
    forecast = fetch_json(FORECAST_URL, common)
    result = {"current": current, "forecast": forecast}
    _cache[key] = {"saved_at": now, "data": result}
    return result


def make_daily_forecast(forecast_json):
    """Choose one forecast entry near midday for each of the next five dates."""
    by_date = {}
    for item in forecast_json.get("list", []):
        date_text = item["dt_txt"].split(" ")[0]
        hour = int(item["dt_txt"].split(" ")[1][:2])
        # Prefer a reading around noon; retain the first reading as a fallback.
        score = abs(hour - 12)
        if date_text not in by_date or score < by_date[date_text][0]:
            by_date[date_text] = (score, item)

    days = sorted(by_date.items())[:5]
    return [item[1] for item in days]


class WeatherApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Live Weather App")
        self.geometry("720x650")
        self.minsize(560, 560)
        self.configure(bg="#edf3fb")

        self.city_var = tk.StringVar(value="London")
        self.status_var = tk.StringVar(value="Enter a city to view live weather.")
        self._build_ui()

        if not API_KEY:
            self.after(
                300,
                lambda: messagebox.showwarning(
                    "API key required",
                    "No API key was found.\n\nOpen the .env file and add your "
                    "OpenWeather API key, then restart the app."
                ),
            )

    def _build_ui(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass
        style.configure("TButton", font=("Arial", 11, "bold"), padding=8)
        style.configure("TEntry", font=("Arial", 12), padding=7)

        header = tk.Frame(self, bg="#123b66", padx=24, pady=20)
        header.pack(fill="x")
        tk.Label(
            header, text="LIVE WEATHER", bg="#123b66", fg="white",
            font=("Arial", 21, "bold")
        ).pack(anchor="w")
        tk.Label(
            header, text="Current conditions and a 5-day forecast",
            bg="#123b66", fg="#dcecff", font=("Arial", 10)
        ).pack(anchor="w", pady=(4, 0))

        search = tk.Frame(self, bg="#edf3fb", padx=24, pady=18)
        search.pack(fill="x")
        ttk.Entry(search, textvariable=self.city_var).pack(
            side="left", fill="x", expand=True, ipady=4
        )
        ttk.Button(search, text="Get Weather", command=self.search).pack(
            side="left", padx=(10, 0)
        )
        self.bind("<Return>", lambda _event: self.search())

        self.current_card = tk.Frame(
            self, bg="white", padx=22, pady=18,
            highlightthickness=1, highlightbackground="#d8e2ef"
        )
        self.current_card.pack(fill="x", padx=24, pady=(0, 14))

        self.location_label = tk.Label(
            self.current_card, text="Weather details will appear here",
            bg="white", fg="#173653", font=("Arial", 17, "bold")
        )
        self.location_label.pack(anchor="w")
        self.temp_label = tk.Label(
            self.current_card, text="--°C", bg="white", fg="#1765b1",
            font=("Arial", 38, "bold")
        )
        self.temp_label.pack(anchor="w", pady=(8, 0))
        self.description_label = tk.Label(
            self.current_card, text="Search for a city",
            bg="white", fg="#526477", font=("Arial", 12)
        )
        self.description_label.pack(anchor="w", pady=(0, 12))

        metrics = tk.Frame(self.current_card, bg="white")
        metrics.pack(fill="x")
        self.humidity_label = self._metric(metrics, "HUMIDITY", "--%")
        self.feels_label = self._metric(metrics, "FEELS LIKE", "--°C")
        self.wind_label = self._metric(metrics, "WIND", "-- m/s")

        forecast_outer = tk.Frame(self, bg="#edf3fb", padx=24)
        forecast_outer.pack(fill="both", expand=True)
        tk.Label(
            forecast_outer, text="5-DAY FORECAST", bg="#edf3fb",
            fg="#173653", font=("Arial", 13, "bold")
        ).pack(anchor="w", pady=(2, 10))

        self.forecast_frame = tk.Frame(forecast_outer, bg="#edf3fb")
        self.forecast_frame.pack(fill="both", expand=True)

        tk.Label(
            self, textvariable=self.status_var, bg="#edf3fb", fg="#526477",
            font=("Arial", 9), anchor="w", padx=24, pady=10
        ).pack(fill="x")

    @staticmethod
    def _metric(parent, title, value):
        box = tk.Frame(parent, bg="#f1f6fc", padx=12, pady=10)
        box.pack(side="left", fill="x", expand=True, padx=(0, 8))
        tk.Label(
            box, text=title, bg="#f1f6fc", fg="#66788a",
            font=("Arial", 8, "bold")
        ).pack(anchor="w")
        label = tk.Label(
            box, text=value, bg="#f1f6fc", fg="#173653",
            font=("Arial", 13, "bold")
        )
        label.pack(anchor="w", pady=(4, 0))
        return label

    def search(self):
        city = self.city_var.get().strip()
        if not city:
            messagebox.showinfo("City required", "Please enter a city name.")
            return
        if not API_KEY:
            messagebox.showerror(
                "API key missing",
                "Add OPENWEATHER_API_KEY=your_key to your .env file, then restart."
            )
            return

        self.status_var.set("Loading weather data...")
        self.update_idletasks()
        try:
            data = get_weather(city)
            self.show_weather(data)
            self.status_var.set(
                f"Updated: {datetime.now().strftime('%d %b %Y, %I:%M:%S %p')} "
                f"| Data from OpenWeather"
            )
        except (RuntimeError, KeyError, ValueError) as exc:
            self.status_var.set("Could not load weather data.")
            messagebox.showerror("Weather lookup failed", str(exc))

    def show_weather(self, data):
        current = data["current"]
        name = current["name"]
        country = current["sys"].get("country", "")
        weather = current["weather"][0]
        temp = current["main"]["temp"]
        humidity = current["main"]["humidity"]
        feels = current["main"]["feels_like"]
        wind = current["wind"]["speed"]

        self.location_label.config(text=f"{name}, {country}")
        self.temp_label.config(text=f"{temp:.1f}°C")
        self.description_label.config(
            text=weather["description"].capitalize()
        )
        self.humidity_label.config(text=f"{humidity}%")
        self.feels_label.config(text=f"{feels:.1f}°C")
        self.wind_label.config(text=f"{wind:.1f} m/s")

        for widget in self.forecast_frame.winfo_children():
            widget.destroy()

        for item in make_daily_forecast(data["forecast"]):
            date_obj = datetime.strptime(item["dt_txt"], "%Y-%m-%d %H:%M:%S")
            details = item["weather"][0]
            card = tk.Frame(
                self.forecast_frame, bg="white", padx=10, pady=12,
                highlightthickness=1, highlightbackground="#d8e2ef"
            )
            card.pack(side="left", fill="both", expand=True, padx=(0, 7), pady=2)
            tk.Label(
                card, text=date_obj.strftime("%a"), bg="white", fg="#173653",
                font=("Arial", 11, "bold")
            ).pack(pady=(0, 8))
            tk.Label(
                card, text=f"{item['main']['temp']:.0f}°C", bg="white",
                fg="#1765b1", font=("Arial", 16, "bold")
            ).pack()
            tk.Label(
                card, text=details["description"].capitalize(),
                bg="white", fg="#66788a", font=("Arial", 8),
                wraplength=90, justify="center"
            ).pack(pady=(7, 0))


if __name__ == "__main__":
    app = WeatherApp()
    app.mainloop()

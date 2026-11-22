import json
import urllib.request
import urllib.parse
import urllib.error
from datetime import datetime

API_KEY = input("Enter your OpenWeather API key: ").strip()

BASE_URL = "https://api.openweathermap.org/data/2.5/"


def get_weather(city, endpoint):
    params = {
        "q": city,
        "appid": API_KEY,
        "units": "metric"
    }

    url = BASE_URL + endpoint + "?" + urllib.parse.urlencode(params)

    try:
        request = urllib.request.Request(url)
        with urllib.request.urlopen(request, timeout=15) as response:
            return json.loads(response.read().decode())

    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("Error: Invalid API key. Check your API key.")
        elif e.code == 404:
            print("Error: City not found.")
        elif e.code == 429:
            print("Error: API request limit reached.")
        else:
            print("Weather API error:", e.code)
        return None

    except Exception as e:
        print("Connection error:", e)
        return None


def current_weather(city):

    data = get_weather(city, "weather")

    if data is None:
        return

    print("\n========== CURRENT WEATHER ==========")
    print("City:", data.get("name", city))

    main = data.get("main", {})
    weather = data.get("weather", [{}])[0]
    wind = data.get("wind", {})

    print("Temperature:", main.get("temp", "N/A"), "°C")
    print("Feels Like:", main.get("feels_like", "N/A"), "°C")
    print("Humidity:", main.get("humidity", "N/A"), "%")
    print("Weather:", weather.get("description", "N/A").title())
    print("Wind Speed:", wind.get("speed", "N/A"), "m/s")

    print("=====================================")


def weather_forecast(city):

    data = get_weather(city, "forecast")

    if data is None:
        return

    print("\n========== FIVE DAY FORECAST ==========")

    daily = {}

    for item in data.get("list", []):

        date = item["dt_txt"].split(" ")[0]

        if date not in daily:
            daily[date] = item

    print("{:<15} {:<15} {}".format(
        "DATE", "TEMP (°C)", "CONDITION"
    ))

    for date, item in list(daily.items())[:5]:

        temperature = item["main"]["temp"]

        description = item["weather"][0]["description"]

        formatted_date = datetime.strptime(
            date, "%Y-%m-%d"
        ).strftime("%d %b %Y")

        print("{:<15} {:<15} {}".format(
            formatted_date,
            temperature,
            description.title()
        ))

    print("=======================================")


def main():

    print("\n********************************")
    print("       LIVE WEATHER APP")
    print("********************************")

    if not API_KEY:
        print("API key is required.")
        return

    while True:

        city = input("\nEnter city name (or press Enter to exit): ").strip()

        if city == "":
            print("Thank you for using Weather App!")
            break

        current_weather(city)
        weather_forecast(city)


if __name__ == "__main__":
    main()
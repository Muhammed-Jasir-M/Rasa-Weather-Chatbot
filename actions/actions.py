import os
from typing import Any, Text, Dict, List
from dotenv import load_dotenv
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import requests

# Load environment variables at module level
load_dotenv()

class ActionGreetName(Action):
    def name(self) -> Text:
        return "action_greet_name"
        
    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        name = tracker.get_slot('person') 
        if name:
            dispatcher.utter_message(text=f"Nice to meet you, {name}!")
            return [SlotSet("person", None)] 
        
        dispatcher.utter_message(text="I see, carry on!")
        return []

class ActionCheckWeather(Action):
    def name(self) -> Text:
        return "action_get_weather"
        
    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:

        api_key = os.getenv("WEATHER_API_KEY")
        location = tracker.get_slot('location')
        
        # validation checks
        if not api_key:
            dispatcher.utter_message(text="Weather service is currently unavailable. Please try again later.")
            return []
            
        if not location or len(location.strip()) < 2:
            dispatcher.utter_message(text="I couldn't get the location. Can you provide it again?")
            return []
            
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                weather_info = self._format_weather_info(data, location)
                dispatcher.utter_message(text=weather_info)
                return [SlotSet('location', location)]
                
            elif response.status_code == 404:
                dispatcher.utter_message(text=f"Sorry, I couldn't find weather data for {location}.")
            else:
                dispatcher.utter_message(text="Failed to fetch weather. Please try again later.")
                
        except requests.exceptions.RequestException as e:
            dispatcher.utter_message(text="There was an issue fetching the weather data. Please try again later.")
        except Exception as e:
            dispatcher.utter_message(text="Something went wrong while fetching the weather. Please try again later.")
            
        return []
        
    def _format_weather_info(self, data: Dict, location: str) -> str:
        """Format weather info into message."""

        country = data.get("sys", {}).get("country", "Unknown Country")
        city = data.get("name", location)
        weather = data.get("weather", [{}])[0].get("main", "N/A")
        temperature = round(data.get("main", {}).get("temp", "N/A"))
        humidity = data.get("main", {}).get("humidity", "N/A")
        wind_speed = data.get("wind", {}).get("speed", "N/A")
        
        return (
            f"🌤️ Weather Update for {city}, {country}:\n"
            f"├── ☁️ Condition: {weather}\n"
            f"├── 🌡 Temperature: {temperature}°C\n"
            f"├── 💧 Humidity: {humidity}%\n"
            f"└── 💨 Wind Speed: {wind_speed} m/s\n"
            f"Stay prepared! Have a great day! 😊"
        )
        

class ActionGetAirQuality(Action):
    def name(self) -> Text:
        return "action_get_air_quality"
    
    def run(self, dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        api_key = os.getenv("WEATHER_API_KEY")
        location = tracker.get_slot('location')

        if not api_key:
            dispatcher.utter_message(text="Weather service is currently unavailable. Please try again later.")
            return []
            
        if not location or len(location.strip()) < 2:
            dispatcher.utter_message(text="I couldn't get the location. Can you provide it again?")
            return []

        try:
            url = f"http://api.openweathermap.org/geo/1.0/direct?q={location}&limit=1&appid={api_key}"
            geo_response = requests.get(url)
            
            if geo_response.status_code == 200:
                geo_data = geo_response.json()
                if geo_data:
                    lat = geo_data[0]['lat']
                    lon = geo_data[0]['lon']
                    
                    aqi_url = f"http://api.openweathermap.org/data/2.5/air_pollution?lat={lat}&lon={lon}&appid={api_key}"
                    aqi_response = requests.get(aqi_url)
                    
                    if aqi_response.status_code == 200:
                        aqi_data = aqi_response.json()
                        aqi_message = self._format_air_quality(aqi_data)
                        dispatcher.utter_message(text=aqi_message)
                    else:
                        dispatcher.utter_message(text=f"Sorry, I couldn't get air quality data for {location}.")
                else:
                    dispatcher.utter_message(text=f"Sorry, I couldn't find the location {location}.")
            else:
                dispatcher.utter_message(text="There was an error getting location coordinates.")
                
        except Exception as e:
            dispatcher.utter_message(text="There was an error getting air quality data. Please try again later.")
        
        return []

    def _format_air_quality(self, data: Dict, location: str) -> str:        
        aqi = data['list'][0]['main']['aqi']
        components = data['list'][0]['components']
        
        aqi_levels = {
            1: "Good 😊",
            2: "Fair 🙂",
            3: "Moderate 😐",
            4: "Poor 😷",
            5: "Very Poor 🤢"
        }

        aqi_advice = {
            1: "Perfect for outdoor activities!",
            2: "Generally safe for outdoor activities.",
            3: "Sensitive individuals should limit outdoor exposure.",
            4: "Avoid prolonged outdoor activities.",
            5: "Stay indoors if possible."
        }
        
        message = f"🌬️ Air Quality Report for {location}:\n"
        message += f"├── Overall: {aqi_levels.get(aqi, 'Unknown')}\n"
        message += f"├── PM2.5: {components.get('pm2_5', 'N/A')} μg/m³\n"
        message += f"├── PM10: {components.get('pm10', 'N/A')} μg/m³\n"
        message += f"├── NO2: {components.get('no2', 'N/A')} μg/m³\n"
        message += f"└── Advice: {aqi_advice.get(aqi, 'Check local guidelines.')}\n"
        
        return message
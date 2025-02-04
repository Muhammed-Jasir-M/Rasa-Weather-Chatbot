import os
from typing import Any, Text, Dict, List

from dotenv import load_dotenv
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet
import requests # For HTTP request

load_dotenv() # Load env variables

class ActionGreetName(Action):

    def name(self) -> Text:
        return "action_greet_name"

    def run(self, dispatcher,tracker,domain):

        name = tracker.get_slot('PERSON')  # Fetch the PERSON slot

        if name: 
            dispatcher.utter_message(text=f"Nice to meet you, {name}!")
            return [SlotSet("PERSON", None)] 
        else:  
            dispatcher.utter_message(text="I see, carry on!")
            return []

# Action to fetch Weather Info for given loc
class ActionCheckWeather(Action):
    
    def name(self)-> Text:
        return "action_get_weather"
    
    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
    
        api_key = os.getenv("WEATHER_API_KEY") # fetch api key
        location = tracker.get_slot('location') # get location slot

        if not api_key:
            dispatcher.utter_message(text="Weather service is currently unavailable. Please try again later.")
            return []

        # if loc is empty then returns
        if not location:
            dispatcher.utter_message(text="I couldn't get the location. Can you provide it again?")
            return []
        
        if len(location.strip()) < 2:
            dispatcher.utter_message(text="That doesn't look like a valid location. Please try again.")
            return []
        
        try:
            url = f"https://api.openweathermap.org/data/2.5/weather?q={location}&appid={api_key}&units=metric"

            # make request
            response = requests.get(url)

            if response.status_code == 200: 
                # parse json response
                data = response.json()

                # extract data & fallback if it is empty
                country = data.get("sys", {}).get("country", "Unknown Country") 
                city = data.get("name", location) 
                weather = data.get("weather", [{}])[0].get("main", "N/A") if data.get("weather") else "N/A"
                temperature = round(data.get("main", {}).get("temp", "N/A"))
                humidity = data.get("main", {}).get("humidity", "N/A") 
                wind_speed = data.get("wind", {}).get("speed", "N/A") 

                response_text = (
                    f"🌤️ Weather Update for {city}, {country}:\n"
                    f"├── ☁️ Condition: {weather}\n"
                    f"├── 🌡 Temperature: {temperature}°C\n"
                    f"├── 💧 Humidity: {humidity}%\n"
                    f"└── 💨 Wind Speed: {wind_speed} m/s\n"
                    f"Stay prepared! Have a great day! 😊"
                )
                
                dispatcher.utter_message(text=response_text)
                return [SlotSet('location', location)]

            # Handle specific HTTP errors
            elif response.status_code == 404:
                dispatcher.utter_message(text=f"Sorry, I couldn't find weather data for {location}.")
            else:
                dispatcher.utter_message(text="Failed to fetch weather. Please try again later.")
                return []
                    
        # Handle request-related errors like connection issues
        except requests.exceptions.RequestException:
            dispatcher.utter_message(text="There was an issue fetching the weather data. Please try again later.")
            return []

        # Handle any other errors (e.g., unexpected data structure or missing fields)
        except Exception as e:
            dispatcher.utter_message(text="Something went wrong while fetching the weather. Please try again later.")
            return []
        
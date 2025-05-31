from fastapi import FastAPI
import gradio as gr
from dotenv import load_dotenv
from autogen import ConversableAgent, register_function
import httpx
from typing import Annotated
import os
from datetime import datetime

# Load environment first
load_dotenv('.env.local')

app = FastAPI()

class WeatherFormatter:
    @staticmethod
    def format_time(timestamp: int) -> str:
        """Convert UNIX timestamp to readable time"""
        return datetime.fromtimestamp(timestamp).strftime('%H:%M') if timestamp else 'N/A'

    @staticmethod
    def degrees_to_compass(deg: int) -> str:
        """Convert wind degrees to compass direction"""
        if not isinstance(deg, (int, float)):
            return 'N/A'
        
        directions = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
                     "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
        val = int((deg/22.5)+0.5)
        return directions[(val % 16)]

    def _generate_recommendations(self, data: dict) -> str:
        """Generate weather recommendations"""
        temp = data.get('main', {}).get('temp', 0)
        conditions = data.get('weather', [{}])[0].get('main', '').lower()
        wind_speed = data.get('wind', {}).get('speed', 0)
        
        recommendations = []
        
        # Temperature based
        if temp < 5:
            recommendations.append("❄️ Heavy winter coat required")
        elif temp < 15:
            recommendations.append("🧥 Light jacket recommended")
        elif temp > 25:
            recommendations.append("🥤 Stay hydrated in the heat")
        
        # Weather conditions
        if 'rain' in conditions:
            recommendations.append("☔ Umbrella essential")
        elif 'snow' in conditions:
            recommendations.append("🧤 Wear gloves and warm boots")
        elif 'clear' in conditions:
            recommendations.append("😎 Sunglasses recommended")
        
        # Wind conditions
        if wind_speed > 10:
            recommendations.append("🧣 Windproof clothing suggested")
        
        return "\n- ".join(recommendations) if recommendations else "Normal conditions, no special precautions needed"

    def format_weather(self, data: dict) -> str:
        """Professional weather formatting with emojis"""
        try:
            # Time formatting
            update_time = self.format_time(data.get('dt'))
            sunrise = self.format_time(data.get('sys', {}).get('sunrise'))
            sunset = self.format_time(data.get('sys', {}).get('sunset'))
            
            # Wind direction
            wind_deg = data.get('wind', {}).get('deg', 0)
            wind_dir = self.degrees_to_compass(wind_deg)
            
            # Cloud cover visualization
            clouds = data.get('clouds', {}).get('all', 0)
            cloud_emoji = "☁️" if clouds > 70 else "⛅" if clouds > 30 else "🌤️"
            
            # Visibility conversion
            visibility = data.get('visibility', 'N/A')
            if isinstance(visibility, int):
                visibility = f"{visibility/1000} km" if visibility >= 1000 else f"{visibility} m"
            
            return f"""
{cloud_emoji} **Current Weather in {data.get('name', 'Unknown Location')}**  
📍 Coordinates: {data.get('coord', {}).get('lat', '?')}°N, {data.get('coord', {}).get('lon', '?')}°E  
🕒 Last Updated: {update_time}  

🌡️ **Temperature**  
- Current: {data.get('main', {}).get('temp', 'N/A')}°C (Feels like {data.get('main', {}).get('feels_like', 'N/A')}°C)  
- Range: {data.get('main', {}).get('temp_min', 'N/A')}°C ~ {data.get('main', {}).get('temp_max', 'N/A')}°C  
- Humidity: {data.get('main', {}).get('humidity', 'N/A')}%  
- Pressure: {data.get('main', {}).get('pressure', 'N/A')} hPa  

💨 **Wind**  
- Speed: {data.get('wind', {}).get('speed', 'N/A')} m/s  
- Direction: {wind_deg}° ({wind_dir})  

☁️ **Conditions**  
- {data.get('weather', [{}])[0].get('description', 'N/A').title()}  
- Cloud Cover: {clouds}%  
- Visibility: {visibility}  

🌅 **Sun Times**  
- Sunrise: {sunrise}  
- Sunset: {sunset}  

💡 **Recommendations**  
- {self._generate_recommendations(data)}
            """
        except Exception as e:
            return f"⚠️ Error formatting weather data: {str(e)}\nRaw data: {data}"

class WeatherAgent:
    def __init__(self):
        self.weather_assistant = None
        self.weather_api_proxy = None
        self.formatter = WeatherFormatter()
        self.initialize_agents()
        
    def initialize_agents(self):
        try:
            # Clear any cached configurations
            if hasattr(self, 'weather_assistant'):
                del self.weather_assistant
            if hasattr(self, 'weather_api_proxy'):
                del self.weather_api_proxy

            # Current recommended Groq models
            CURRENT_GROQ_MODELS = {
                'llama3-70b': 'llama3-70b-8192',
                'mixtral': 'mixtral-8x7b-32768',
                'gemma': 'gemma-7b-it'
            }

            # Initialize with current model
            self.weather_assistant = ConversableAgent(
                name="Weather_Assistant",
                system_message="""You're an AI weather assistant. Use tools to get real weather data.
                When presenting weather data, use the following format:
                
                [Location]
                - Temperature: X°C (Feels like Y°C)
                - Conditions: [Description]
                - Humidity: Z%
                - Wind: A m/s from B direction
                - Sunrise/Sunset: HH:MM / HH:MM
                
                Add brief recommendations based on conditions. Keep responses concise but professional.
                Say 'TERMINATE' when done.""",
                llm_config={
                    "config_list": [{
                        "model": CURRENT_GROQ_MODELS['llama3-70b'],
                        "api_key": os.getenv("GROQ_API_KEY"),
                        "base_url": "https://api.groq.com/openai/v1"
                    }],
                    "cache_seed": None,
                    "temperature": 0.7
                },
                max_consecutive_auto_reply=5
            )

            self.weather_api_proxy = ConversableAgent(
                name="Weather_API_Proxy",
                llm_config=False,
                human_input_mode="NEVER"
            )

            # Define weather function with better error handling
            def get_current_weather(
                lat: Annotated[float, "Latitude"],
                lon: Annotated[float, "Longitude"],
                location: str = ""
            ) -> dict:
                """Fetch current weather from OpenWeather API"""
                try:
                    base_url = "https://api.openweathermap.org/data/2.5/weather"
                    params = {
                        "lat": lat,
                        "lon": lon,
                        "appid": os.getenv("OPENWEATHER_API_KEY"),
                        "units": "metric"
                    }
                    response = httpx.get(base_url, params=params, timeout=10)
                    response.raise_for_status()
                    return response.json()
                except Exception as e:
                    return {"error": str(e)}

            # Register function with enhanced description
            register_function(
                get_current_weather,
                caller=self.weather_assistant,
                executor=self.weather_api_proxy,
                description="""Get current weather by coordinates. 
                Returns: temperature(°C), conditions, humidity(%), wind speed(m/s)"""
            )
            print(f"Weather agents initialized with {CURRENT_GROQ_MODELS['llama3-70b']} model")
        except Exception as e:
            print(f"Initialization error: {str(e)}")
            raise

    def chat(self, message, history):
        if not self.weather_assistant or not self.weather_api_proxy:
            return "System initialization failed. Please check logs."
        
        try:
            response = self.weather_assistant.initiate_chat(
                recipient=self.weather_api_proxy,
                message=message,
                max_turns=2,
                clear_history=True
            )
            
            reply = response.chat_history[-1]["content"]
            
            if "Suggested tool call" in reply:
                return "⏳ Fetching live weather data..."
            
            # Check if we have raw JSON data in the reply
            if "{" in reply and "}" in reply:
                try:
                    import json
                    data = json.loads(reply[reply.index("{"):reply.rindex("}")+1])
                    return self.formatter.format_weather(data)
                except:
                    return reply
            return reply
            
        except Exception as e:
            print(f"Chat error: {str(e)}")
            return "⚠️ Service temporarily unavailable. Please try again later."

# Initialize with error handling
try:
    weather_agent = WeatherAgent()
    print("Weather service started successfully")
except Exception as e:
    print(f"Failed to initialize weather agent: {str(e)}")
    weather_agent = None

def safe_chat(message, history):
    if not weather_agent:
        return "🔧 Weather service is currently undergoing maintenance. Please check back later."
    return weather_agent.chat(message, history)

# Create Gradio app with fallback
gradio_app = gr.ChatInterface(
    fn=safe_chat,
    title="🌦️ Professional Weather Assistant",
    description="Get detailed, formatted weather reports for any location",
    examples=[
        "What's the weather in Tokyo?",
        "Current conditions in London with recommendations",
        "Detailed weather report for New York"
    ],
    theme="soft",
    css="""
    .message.user {
        background: #f0f7ff;
        border-radius: 10px;
        padding: 10px 15px;
        margin: 5px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
    }
    .message.bot {
        background: #f9f9f9;
        border-radius: 10px;
        padding: 15px;
        margin: 5px 0;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        white-space: pre-wrap;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    }
    .message.bot code {
        background: #f0f0f0;
        padding: 2px 4px;
        border-radius: 3px;
        font-family: monospace;
    }
    """
)

# Mount Gradio app
app = gr.mount_gradio_app(app, gradio_app, path="/")

@app.get("/health")
def health_check():
    return {"status": "healthy" if weather_agent else "unavailable"}

if __name__ == "__main__":
    # Clear any cached files
    for f in ['__pycache__', '*.pyc', '*.pyo']:
        os.system(f"rm -rf {f}")
    
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
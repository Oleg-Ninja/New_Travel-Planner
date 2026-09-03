from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.requests import Request
import httpx

app = FastAPI(title="Travel Planner")

# Подключаем шаблоны
templates = Jinja2Templates(directory="app/templates")

# Простой словарь для кэширования в памяти
CACHE = {}

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    # ✅ Исправлено: передаем request как именованный аргумент
    return templates.TemplateResponse(request=request, name="index.html")

@app.get("/api/trip")
async def get_trip(city: str):
    city_key = city.lower().strip()
    
    # 1. Если данные есть в кэше — отдаем мгновенно
    if city_key in CACHE:
        return CACHE[city_key]

    # 2. Если данных нет — делаем асинхронные запросы
    async with httpx.AsyncClient() as client:
        # Получаем координаты города
        geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={city_key}&count=1&language=ru&format=json"
        geo_res = await client.get(geo_url)
        geo_data = geo_res.json()

        if not geo_data.get("results"):
            raise HTTPException(status_code=404, detail="Город не найден")

        location = geo_data["results"][0]
        lat, lon = location["latitude"], location["longitude"]
        city_name = location.get("name", city)

        # Получаем текущую погоду
        weather_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
        weather_res = await client.get(weather_url)
        weather_data = weather_res.json()

        current = weather_data.get("current_weather", {})

        result = {
            "city": city_name,
            "temp": round(current.get("temperature", 0)),
            "description": "Ясно / Малооблачно" if current.get("weathercode", 0) <= 3 else "Пасмурно / Осадки",
            "coordinates": {"lat": lat, "lon": lon},
            "sights": []
        }

        # Сохраняем в кэш
        CACHE[city_key] = result
        return result
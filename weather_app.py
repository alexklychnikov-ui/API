import requests
from dotenv import load_dotenv
import os
import http_client
import json
from datetime import datetime, timedelta

# Загружаем переменные окружения
load_dotenv()

API_KEY = os.getenv('API_KEY')
if not API_KEY:
    raise ValueError("API ключ не найден. Создайте файл .env с API_KEY")

CACHE_FILE = 'weather_cache.json'

def save_to_cache(data: dict, filename: str = CACHE_FILE):
    """Сохраняет данные в кэш"""
    data['fetched_at'] = datetime.now().isoformat()
    with open(filename, 'w') as f:
        json.dump(data, f)


def load_from_cache(filename: str = CACHE_FILE) -> dict:
    """Загружает данные из кэша"""
    try:
        with open(filename, 'r') as f:
            cached_data = json.load(f)
            fetched_time = datetime.fromisoformat(cached_data['fetched_at'])
            if datetime.now() - fetched_time < timedelta(hours=3):
                return cached_data
    except (FileNotFoundError, json.JSONDecodeError, KeyError):
        pass
    return {}


def get_coordinates(city: str) -> tuple:
    """Получает координаты города"""
    url = f"http://api.openweathermap.org/geo/1.0/direct?q={city}&appid={API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        if data:
            return data[0]['lat'], data[0]['lon']
    else:
        print(f"Ошибка: {response.status_code}")
        return None


def get_current_weather(city: str = None, latitude: float = None, longitude: float = None) -> dict:
    if city:
        print(f"Получаем погоду для города: {city}")
        return get_weather_by_city(city)
    
    if latitude and longitude:
        print(f"Получаем погоду для координат: {latitude}, {longitude}")
        return get_weather_by_coordinates(latitude, longitude)

    # Attempt to use cache if network error occurs
    cached_data = load_from_cache()
    if cached_data:
        print("Предлагаю использовать кэшированные данные.")
        return cached_data


def get_weather_by_coordinates(latitude: float, longitude: float) -> dict:
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={latitude}&lon={longitude}&appid={API_KEY}&units=metric&lang=ru"
    
    try:
        response = http_client.get_with_retries(url)
        if response and response.status_code == 200:
            data = response.json()
            save_to_cache(data)
            return data
        else:
            return {"error": f"Ошибка запроса: {response.status_code if response else 'Нет ответа'}"}
    except Exception as e:
        return {"error": f"Ошибка получения погоды: {e}"}


def get_weather_by_city(city: str) -> dict:
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric&lang=ru"
    
    try:
        response = http_client.get_with_retries(url)
        if response and response.status_code == 200:
            data = response.json()
            save_to_cache(data)
            return data
        else:
            return {"error": f"Ошибка запроса: {response.status_code if response else 'Нет ответа'}"}
    except Exception as e:
        return {"error": f"Ошибка получения погоды: {e}"}


def print_weather_info(weather_data: dict):
    """Выводит данные о погоде в простом формате"""
    if "error" in weather_data:
        print(f"❌ {weather_data['error']}")
        return
    
    try:
        city = weather_data['name']
        temp = weather_data['main']['temp']
        description = weather_data['weather'][0]['description']
        print(f"Погода в {city}: {temp}°C, {description}")
    except Exception as e:
        print(f"❌ Ошибка форматирования данных: {e}")


def main():
    """Главная функция для тестирования"""
    print("🌤️  Приложение погоды")
    
    # Проверяем наличие API ключа
    if not os.getenv('API_KEY'):
        print("❌ API ключ не найден!")
        print("📝 Создайте файл .env и добавьте: API_KEY=ваш_ключ")
        print("🔗 Получить ключ: https://openweathermap.org/api")
        return
    
    while True:
        print("\n" + "="*50)
        print("1. Погода по названию города")
        print("2. Погода по координатам")
        print("0. Выход")
        
        choice = input("Выберите опцию (0-2): ").strip()
        
        if choice == "0":
            print("До свидания!")
            break
        elif choice == "1":
            city = input("Введите название города: ").strip()
            if city:
                weather = get_current_weather(city=city)
                print_weather_info(weather)
        elif choice == "2":
            try:
                lat = float(input("Введите широту: "))
                lon = float(input("Введите долготу: "))
                weather = get_current_weather(latitude=lat, longitude=lon)
                print_weather_info(weather)
            except ValueError:
                print("❌ Неверный формат координат!")
        else:
            print("❌ Неверный выбор!")


if __name__ == "__main__":
    main()
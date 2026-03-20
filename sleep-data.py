import os
from datetime import datetime, timezone
from garminconnect import Garmin
from notion_client import Client
from dotenv import load_dotenv
import pytz

# Configuració de zona horària
local_tz = pytz.timezone("Europe/Madrid")

def get_sleep_data(garmin):
    today = datetime.today().date()
    return garmin.get_sleep_data(today.isoformat())

def format_duration(seconds):
    minutes = (seconds or 0) // 60
    return f"{minutes // 60}h {minutes % 60}m"

def format_time(timestamp):
    # Utilitzem la sintaxi moderna de timezone en lloc del mètode obsolet utcfromtimestamp
    if not timestamp:
        return None
    return datetime.fromtimestamp(timestamp / 1000, timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.000Z")

def format_time_readable(timestamp):
    return (
        datetime.fromtimestamp(timestamp / 1000, local_tz).strftime("%H:%M")
        if timestamp else "Unknown"
    )

def format_date_for_name(sleep_date):
    return datetime.strptime(sleep_date, "%Y-%m-%d").strftime("%d.%m.%Y") if sleep_date else "Unknown"

def sleep_data_exists(client, database_id, sleep_date):
    query = client.databases.query(
        database_id=database_id,
        filter={"property": "Long Date", "date": {"equals": sleep_date}}
    )
    results = query.get('results', [])
    return results[0] if results else None 

def build_sleep_properties(sleep_data):
    """Construeix el diccionari de propietats per a Notion (evita repetir codi)"""
    daily_sleep = sleep_data.get('dailySleepDTO', {})
    if not daily_sleep:
        return None, 0
    
    sleep_date = daily_sleep.get('calendarDate', "Unknown Date")
    total_sleep = sum(
        (daily_sleep.get(k, 0) or 0) for k in ['deepSleepSeconds', 'lightSleepSeconds', 'remSleepSeconds']
    )

    # Protecció contra el None a les dates
    start_time = format_time(daily_sleep.get('sleepStartTimestampGMT'))
    end_time = format_time(daily_sleep.get('sleepEndTimestampGMT'))
    
    date_obj = {}
    if start_time:
        date_obj["start"] = start_time
    if end_time:
        date_obj["end"] = end_time

    properties = {
        "Date": {"title": [{"text": {"content": format_date_for_name(sleep_date)}}]},
        "Times": {"rich_text": [{"text": {"content": f"{format_time_readable(daily_sleep.get('sleepStartTimestampGMT'))} → {format_time_readable(daily_sleep.get('sleepEndTimestampGMT'))}"}}]},
        "Long Date": {"date": {"start": sleep_date}},
        "Total Sleep (h)": {"number": round(total_sleep / 3600, 1)},
        "Light Sleep (h)": {"number": round(daily_sleep.get('lightSleepSeconds', 0) / 3600, 1)},
        "Deep Sleep (h)": {"number": round(daily_sleep.get('deepSleepSeconds', 0) / 3600, 1)},
        "REM Sleep (h)": {"number": round(daily_sleep.get('remSleepSeconds', 0) / 3600, 1)},
        "Awake Time (h)": {"number": round(daily_sleep.get('awakeSleepSeconds', 0) /

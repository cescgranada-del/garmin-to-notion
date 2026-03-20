import os
import shutil
from garminconnect import Garmin
from notion_client import Client
from dotenv import load_dotenv

# Nota: He eliminat pytz i timezone perquè utilitzarem startTimeLocal directe de Garmin

ACTIVITY_ICONS = {
    "Barre": "https://img.icons8.com/?size=100&id=66924&format=png&color=000000",
    "Breathwork": "https://img.icons8.com/?size=100&id=9798&format=png&color=000000",
    "Cardio": "https://img.icons8.com/?size=100&id=71221&format=png&color=000000",
    "Cycling": "https://img.icons8.com/?size=100&id=47443&format=png&color=000000",
    "Hiking": "https://img.icons8.com/?size=100&id=9844&format=png&color=000000",
    "Indoor Cardio": "https://img.icons8.com/?size=100&id=62779&format=png&color=000000",
    "Indoor Cycling": "https://img.icons8.com/?size=100&id=47443&format=png&color=000000",
    "Indoor Rowing": "https://img.icons8.com/?size=100&id=71098&format=png&color=000000",
    "Pilates": "https://img.icons8.com/?size=100&id=9774&format=png&color=000000",
    "Meditation": "https://img.icons8.com/?size=100&id=9798&format=png&color=000000",
    "Rowing": "https://img.icons8.com/?size=100&id=71491&format=png&color=000000",
    "Running": "https://img.icons8.com/?size=100&id=k1l1XFkME39t&format=png&color=000000",
    "Strength Training": "https://img.icons8.com/?size=100&id=107640&format=png&color=000000",
    "Stretching": "https://img.icons8.com/?size=100&id=djfOcRn1m_kh&format=png&color=000000",
    "Swimming": "https://img.icons8.com/?size=100&id=9777&format=png&color=000000",
    "Treadmill Running": "https://img.icons8.com/?size=100&id=9794&format=png&color=000000",
    "Walking": "https://img.icons8.com/?size=100&id=9807&format=png&color=000000",
    "Yoga": "https://img.icons8.com/?size=100&id=9783&format=png&color=000000",
}

def get_all_activities(garmin, limit=10):
    return garmin.get_activities(0, limit)

def format_activity_type(activity_type, activity_name=""):
    if not activity_type:
        return "Unknown", "Unknown"
        
    formatted_type = activity_type.replace('_', ' ').title()
    activity_subtype = formatted_type
    activity_type_res = formatted_type

    activity_mapping = {
        "Barre": "Strength",
        "Indoor Cardio": "Cardio",
        "Indoor Cycling": "Cycling",
        "Indoor Rowing": "Rowing",
        "Speed Walking": "Walking",
        "Strength Training": "Strength",
        "Treadmill Running": "Running"
    }

    if formatted_type == "Rowing V2":
        activity_type_res = "Rowing"
    elif formatted_type in ["Yoga", "Pilates"]:
        activity_type_res = "Yoga/Pilates"
        activity_subtype = formatted_type

    if formatted_type in activity_mapping:
        activity_type_res = activity_mapping[formatted_type]
        activity_subtype = formatted_type

    if activity_name and "meditation" in activity_name.lower():
        return "Meditation", "Meditation"
    if activity_name and "barre" in activity_name.lower():
        return "Strength", "Barre"
    if activity_name and "stretch" in activity_name.lower():
        return "Stretching", "Stretching"
    
    return activity_type_res, activity_subtype

def format_entertainment(activity_name):
    if not activity_name:
        return "Unnamed Activity"
    return activity_name.replace('ENTERTAINMENT', 'Netflix')

def format_training_message(message):
    if not message:
        return 'Unknown'
        
    messages = {
        'NO_': 'No Benefit',
        'MINOR_': 'Some Benefit',
        'RECOVERY_': 'Recovery',
        'MAINTAINING_': 'Maintaining',
        'IMPROVING_': 'Impacting',
        'IMPACTING_': 'Impacting',
        'HIGHLY_': 'Highly Impacting',
        'OVERREACHING_': 'Overreaching'
    }
    for key, value in messages.items():
        if message.startswith(key):
            return value
    return message

def format_training_effect(label):
    if not label:
        return 'Unknown'
    return label.replace('_', ' ').title()

def format_pace(average_speed):
    if average_speed and average_speed > 0:
        pace_min_km = 1000 / (average_speed * 60)
        minutes = int(pace_min_km)
        seconds = int((pace_min_km - minutes) * 60)
        return f"{minutes}:{seconds:02d} min/km"
    return "0:00 min/km"

# --- FUNCIONS AUXILIARS PER LLEGIR NOTION SENSE ERRORS ---
def get_notion_number(prop):
    if prop and 'number' in prop and prop['number'] is not None:
        return prop['number']
    return 0

def get_notion_select(prop):
    if prop and 'select' in prop and prop['select'] is not None:
        return prop['select'].get('name', 'Unknown')
    return "Unknown"

def get_notion_rich_text(prop):
    try:
        return prop['rich_text'][0]['text']['content']
    except (KeyError, IndexError, TypeError):
        return ""

def get_notion_title(prop):
    try:
        return prop['title'][0]['text']['content']
    except (KeyError, IndexError, TypeError):
        return ""
# ---------------------------------------------------------

def activity_exists(client, database_id, activity_date, activity_type, activity_name):
    if not activity_date:
        return None

    # Agafem només la data YYYY-MM-DD
    date_only = activity_date[:10]
    lookup_type = "Stretching" if activity_name and "stretch" in activity_name.lower() else activity_type
    
    # Ja no busquem per nom per evitar duplicats si canvies el nom al Garmin
    query = client.databases.query(
        database_id=database_id,
        filter={
            "and":

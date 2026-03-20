from datetime import datetime
from garminconnect import Garmin
from notion_client import Client
import os
from dotenv import load_dotenv

def get_icon_for_record(activity_name):
    icon_map = {
        "1K": "🥇",
        "1mi": "⚡",
        "5K": "👟",
        "10K": "⭐",
        "Longest Run": "🏃",
        "Longest Ride": "🚴",
        "Total Ascent": "🚵",
        "Max Avg Power (20 min)": "🔋",
        "Most Steps in a Day": "👣",
        "Most Steps in a Week": "🚶",
        "Most Steps in a Month": "📅",
        "Longest Goal Streak": "✔️",
        "Other": "🏅"
    }
    return icon_map.get(activity_name, "🏅")

def get_cover_for_record(activity_name):
    cover_map = {
        "1K": "https://images.unsplash.com/photo-1526676537331-7747bf8278fc?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=4800",
        "1mi": "https://images.unsplash.com/photo-1638183395699-2c0db5b6afbb?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=4800",
        "5K": "https://images.unsplash.com/photo-1571008887538-b36bb32f4571?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=4800",
        "10K": "https://images.unsplash.com/photo-1529339944280-1a37d3d6fa8c?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=4800",
        "Longest Run": "https://images.unsplash.com/photo-1532383282788-19b341e3c422?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=4800",
        "Longest Ride": "https://images.unsplash.com/photo-1471506480208-91b3a4cc78be?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=4800",
        "Max Avg Power (20 min)": "https://images.unsplash.com/photo-1591741535018-d042766c62eb?crop=entropy&cs=tinysrgb&fit=max&fm=jpg&ixid=M3w2MzkyMXwwfDF8c2VhcmNofDJ8fHNwaW5uaW5nfGVufDB8fHx8MTcyNjM1Mzc0Mnww&ixlib=rb-4.0.3&q=80&w=4800",
        "Most Steps in a Day": "https://images.unsplash.com/photo-1476480862126-209bfaa8edc8?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=4800",
        "Most Steps in a Week": "https://images.unsplash.com/photo-1602174865963-9159ed37e8f1?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=4800",
        "Most Steps in a Month": "https://images.unsplash.com/photo-1580058572462-98e2c0e0e2f0?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=4800",
        "Longest Goal Streak": "https://images.unsplash.com/photo-1477332552946-cfb384aeaf1c?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=4800"
    }
    return cover_map.get(activity_name, "https://images.unsplash.com/photo-1471506480208-91b3a4cc78be?ixlib=rb-4.0.3&q=85&fm=jpg&crop=entropy&cs=srgb&w=4800") 

def format_activity_type(activity_type):
    if activity_type is None:
        return "Walking"
    return activity_type.replace('_', ' ').title()

def format_garmin_value(value, typeId):
    if value is None:
        return "", ""
        
    if typeId == 1:  # 1K
        total_seconds = round(value)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        formatted_value = f"{minutes}:{seconds:02d} /km"
        return formatted_value, formatted_value

    if typeId == 2:  # 1mile
        total_seconds = round(value)
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        formatted_value = f"{minutes}:{seconds:02d}"
        
        total_pseconds = int(total_seconds / 1.60934) 
        pminutes = total_pseconds // 60
        pseconds = total_pseconds % 60
        formatted_pace = f"{pminutes}:{pseconds:02d} /km"
        return formatted_value, formatted_pace

    if typeId == 3:  # 5K
        total_seconds = round(value) 
        minutes = total_seconds // 60
        seconds = total_seconds % 60
        formatted_value = f"{minutes}:{seconds:02d}"
        
        total_pseconds = int(total_seconds / 5) 
        pminutes = total_pseconds // 60
        pseconds = total_pseconds % 60
        formatted_pace = f"{pminutes}:{pseconds:02d} /km"
        return formatted_value, formatted_pace

    if typeId == 4:  # 10K
        total_seconds = round(value)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        
        if hours > 0:
            formatted_value = f"{hours}:{minutes:02d}:{seconds:02d}"
        else:
            formatted_value = f"{minutes}:{seconds:02d}"
            
        total_pseconds = int(total_seconds / 10)
        pminutes = total_pseconds // 60
        pseconds = total_pseconds % 60
        formatted_pace = f"{pminutes}:{pseconds:02d} /km"
        return formatted_value, formatted_pace

    if typeId in [7, 8]:  # Longest Run, Longest Ride
        value_km = value / 1000
        return f"{value_km:.2f} km", ""

    if typeId == 9:  # Total Ascent
        return f"{int(value):,} m", ""

    if typeId == 10:  # Max Avg Power
        return f"{round(value)} W", ""

    if typeId in [12, 13, 14]:  # Step counts
        return f"{round(value):,}", ""

    if typeId == 15:  # Longest Goal Streak
        return f"{round(value)} days", ""

    # Default case per temps
    if int(value // 60) < 60:
        minutes = int(value // 60)
        seconds = round((value / 60 - minutes) * 60, 2)
        formatted_value = f"{minutes}:{seconds:05.2f}"
    else:
        hours = int(value // 3600)
        minutes = int((value % 3600) // 60)
        seconds = round(value % 60, 2)
        formatted_value = f"{hours}:{minutes:02}:{seconds:05.2f}"
    
    return formatted_value, ""

def replace_activity_name_by_typeId(typeId):
    typeId_name_map = {
        1: "1K", 2: "1mi", 3: "5K", 4: "10K", 7: "Longest Run",
        8: "Longest Ride", 9: "Total Ascent", 10: "Max Avg Power (20 min)",
        12: "Most Steps in a Day", 13: "Most Steps in a Week",
        14: "Most Steps in a Month", 15: "Longest Goal Streak"
    }
    return typeId_name_map.get(typeId, "Unnamed Activity")

def get_existing_pr(client, database_id, activity_name):
    query = client.databases.query(
        database_id=database_id,
        filter={
            "and": [
                {"property": "Record", "title": {"equals": activity_name}},
                {"property": "PR", "checkbox": {"equals": True}}
            ]
        }
    )
    return query['results'][0] if query['results'] else None

def get_record_by_date_and_name(client, database_id, activity_date, activity_name):
    query = client.databases.query(
        database_id=database_id,
        filter={
            "and": [
                {"property": "Record", "title": {"equals": activity_name}},
                {"property": "Date", "date": {"equals": activity_date}}
            ]
        }
    )
    return query['results'][0] if query['results'] else None

def archive_old_pr(client, page_id):
    # Només desmarquem la casella PR. No toquem la Data ni els Valors originals de l'antic PR.
    try:
        client.pages.update(
            page_id=page_id,
            properties={"PR": {"checkbox": False}}
        )
    except Exception as e:
        print(f"Error arxivant PR antic: {e}")

def update_record_values(client, page_id, value, pace):
    properties = {}
    if value: properties["Value"] = {"rich_text": [{"text": {"content": value}}]}
    if pace: properties["Pace"] = {"rich_text": [{"text": {"content": pace}}]}
    
    if not properties: return
    try:
        client.pages.update(page_id=page_id, properties=properties)
    except Exception as e:
        print(f"Error actualitzant valors del registre: {e}")

def write_new_record(client, database_id, activity_date, activity_type, activity_name, typeId, value, pace):
    properties = {
        "Date": {"date": {"start": activity_date}},
        "Activity Type": {"select": {"name": activity_type}},
        "Record": {"title": [{"text": {"content": activity_name}}]},
        "typeId": {"number": typeId},
        "PR": {"checkbox": True}
    }
    
    if value: properties["Value"] = {"rich_text": [{"text": {"content": value}}]}
    if pace: properties["Pace"] = {"rich_text": [{"text": {"content": pace}}]}
    
    icon = get_icon_for_record(activity_name)
    cover = get_cover_for_record(activity_name)

    try:
        client.pages.create(
            parent={"database_id": database_id},
            properties=properties,
            icon={"emoji": icon},
            cover={"type": "external", "external": {"url": cover}}
        )
    except Exception as e:
        print(f"Error escrivint nou registre: {e}")

def main():
    load_dotenv() # IMPORTANT: Afegit load_dotenv per carregar variables!

    garmin_email = os.getenv("GARMIN_EMAIL")
    garmin_password = os.getenv("GARMIN_PASSWORD")
    notion_token = os.getenv("NOTION_TOKEN")
    database_id = os.getenv("NOTION_PR_DB_ID")

    garmin = Garmin(garmin_email, garmin_password)
    # Recomanable gestionar el token_store aquí també per evitar crides innecessàries, però ho deixo com ho tens.
    garmin.login() 

    client = Client(auth=notion_token)

    records = garmin.get_personal_record()
    filtered_records = [record for record in records if record.get('typeId') != 16]

    for record in filtered_records:
        # PR startTime GMT és un string tipus "YYYY-MM-DD HH:MM:SS". Agafem només la data
        raw_date = record.get('prStartTimeGmt', '')
        if not raw_date:
            continue
            
        activity_date_str = raw_date[:10] # Formatem a YYYY-MM-DD perquè Notion no es queixi
        
        activity_type = format_activity_type(record.get('activityType'))
        typeId = record.get('typeId', 0)
        activity_name = replace_activity_name_by_typeId(typeId)
        
        value, pace = format_garmin_value(record.get('value', 0), typeId)

        existing_pr_record = get_existing_pr(client, database_id, activity_name)
        existing_date_record = get_record_by_date_and_name(client, database_id, activity_date_str, activity_name)

        if existing_date_record:
            # Si ja tenim AQUEST RÈCORD aquest MATEIX DIA, només actualitzem els valors per si han canviat
            update_record_values(client, existing_date_record['id'], value, pace)
            print(f"Actualitzat registre existent d'avui: {activity_type} - {activity_name}")
            
        elif existing_pr_record:
            try:
                # Extraiem la data de l'antic PR de Notion
                date_prop = existing_pr_record['properties'].get('Date')
                if date_prop and date_prop.get('date') and date_prop['date'].get('start'):
                    existing_date_str = date_prop['date']['start'][:10]
                    
                    # Convertim a objectes datetime per comparar correctament!
                    date_new = datetime.strptime(activity_date_str, "%Y-%m-%d")
                    date_old = datetime.strptime(existing_date_str, "%Y-%m-%d")
                    
                    if date_new > date_old:
                        # Si el de Garmin és més recent, arxivem l'antic i creem el nou
                        archive_old_pr(client, existing_pr_record['id'])
                        print(f"Arxivat PR antic: {activity_type} - {activity_name}")
                        
                        write_new_record(client, database_id, activity_date_str, activity_type, activity_name, typeId, value, pace)
                        print(f"Creat NOU Rècord PR: {activity_type} - {activity_name}")
                    else:
                        print(f"Sense canvis (el PR de Notion és igual o més recent): {activity_type} - {activity_name}")
                else:
                    print(f"Avís: El PR de {activity_name} a Notion no té data vàlida.")
            except Exception as e:
                print(f"Error processant {activity_name}: {e}")

        else:
            # Si no tenim cap PR registrat d'aquest tipus a Notion
            write_new_record(client, database_id, activity_date_str, activity_type, activity_name, typeId, value, pace)
            print(f"Creat primer PR a Notion: {activity_type} - {activity_name}")

if __name__ == '__main__':
    main()

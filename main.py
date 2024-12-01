import sys
import requests
from bs4 import BeautifulSoup
import json
from datetime import date, timedelta
from pyopenmensa.feed import LazyBuilder
import re
import os

requests.packages.urllib3.disable_warnings()

# Load configuration from config.json
with open('config.json', 'r') as config_file:
    config = json.load(config_file)

USERNAME = config.get("USERNAME")
PASSWORD = config.get("PASSWORD")
BASE_URL = config.get("BASE_URL")
TARGET_WEEKS = config.get("TARGET_WEEKS", [0, 1, 2])

# Session to reuse connection
session = requests.Session()


def get_initial_data(base_url):
    """Gets initial cookies, logidpost, and proc."""
    print("Fetching initial data...")
    response = session.get(base_url, verify=False)
    print(f"DEBUG: Initial data response status code: {response.status_code}")
    print(f"DEBUG: Initial data response content (first 500 chars): {response.text[:500]}")
    
    soup = BeautifulSoup(response.text, 'html.parser')

    form = soup.find('form', id='loginform')
    if form:
        proc = form.find('input', {'name': 'proc'})['value']
        logidpost = form.find('input', {'name': 'logidpost'})['value']
        print(f"DEBUG: proc: {proc}")
        print(f"DEBUG: logidpost: {logidpost}")
    else:
        print("DEBUG: ERROR: Could not find login form")
        sys.exit(1) 
        proc = None
        logidpost = None

    return response.cookies, proc, logidpost


def login(base_url, username, password, cookies, proc, logidpost):
    """Logs in to the Mensa website."""
    login_data = {
        'proc': proc,
        'logidpost': logidpost,
        'loginname': username,
        'loginpass': password
    }
    print("Logging in...")
    response = session.post(base_url, data=login_data, cookies=cookies, verify=False)
    print(f"DEBUG: Login response status code: {response.status_code}")
    print(f"DEBUG: Login response content (first 500 chars): {response.text[:500]}")


def fetch_mensa_plan(target_week):
    """Fetches the Mensa plan for the specified week."""
    today = date.today()
    this_monday = today - timedelta(days=today.weekday())
    target_monday = this_monday + timedelta(weeks=target_week)
    datumwahl = target_monday.strftime("%d.%m.%Y")

    data = {
        'wochenwahl': target_week,
        'sid': '1000000041',
        'btun': '',
        'btup': '',
        'cardnum': '',
        'datumwahl': datumwahl
    }
    print(f"Fetching Mensa plan for week {target_week}...")
    return session.post(BASE_URL, data=data, verify=False)


def create_openmensa_feed(gwdata_json_list):
    canteen = LazyBuilder()

    for gwdata_json in gwdata_json_list:
        if not gwdata_json or 'personenliste' not in gwdata_json:
            continue

        personenliste = gwdata_json['personenliste']
        if not personenliste:
            continue

        user_id = list(personenliste.keys())[0]
        user_data = personenliste.get(user_id)
        if not user_data or 'menueplan' not in user_data:
            continue

        menu_plan = user_data['menueplan']
        school_id = list(menu_plan.keys())[0]
        menu_lines = menu_plan.get(school_id)

        if menu_lines:
            for menu_line_id, menu_line_data in menu_lines.items():
                for date_str, meal_data in menu_line_data.items():

                    if meal_data and 'zeilen' in meal_data and meal_data['zeilen'] and meal_data['zeilen'][0] is not None:
                        name = " ".join(filter(None, meal_data['zeilen']))
                        name = re.sub(r'\[.*?\]', '', name)  # Remove zusatzstoffe from the name
                        name = ' '.join(name.split())

                        prices = {}
                        if meal_data.get('preislistenpreis'):
                            prices['student'] = int(float(meal_data['preislistenpreis']) * 100)

                        notes = []
                        if meal_data.get('zusatzstoffeids') and isinstance(meal_data['zusatzstoffeids'], list):
                            notes = [gwdata_json['zusatzstoffe'].get(zs_id) for zs_id in meal_data['zusatzstoffeids'] if gwdata_json['zusatzstoffe'].get(zs_id)]

                        canteen.addMeal(
                            date=date_str,
                            category=f"Hauptgericht",
                            name=name,
                            prices=prices,
                            notes=notes,
                        )
        
    return canteen.toXMLFeed()


if __name__ == "__main__":
    cookies, proc, logidpost = get_initial_data(BASE_URL)
    login(BASE_URL, USERNAME, PASSWORD, cookies, proc, logidpost)

    gwdata_json_list = []
    for target_week in TARGET_WEEKS:
        response = fetch_mensa_plan(target_week)
        soup = BeautifulSoup(response.text, 'html.parser')
        gwdata_input = soup.find('input', {'id': 'gwdata'})

        if gwdata_input:
            print(f"DEBUG: Found 'gwdata' for week {target_week}")
            gwdata_json_list.append(json.loads(gwdata_input['value']))
            #print(f"DEBUG: gwdata_json for week {target_week}: {gwdata_json_list[-1]}")
        else:
            print(f"DEBUG: ERROR: No 'gwdata' found for week {target_week}.")

    print("Creating OpenMensa feed...")
    openmensa_feed = create_openmensa_feed(gwdata_json_list)

    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_file_path = os.path.join(output_folder, "mensa.xml")

    print(f"Saving OpenMensa feed to '{output_file_path}'...")
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(openmensa_feed)
    print("Done!")
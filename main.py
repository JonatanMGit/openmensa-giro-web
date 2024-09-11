import requests
from bs4 import BeautifulSoup
import json
from datetime import date, timedelta
from pyopenmensa.feed import LazyBuilder
import re
import os

requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'  # Giroweb does not support good ciphers :(

# Your login credentials
USERNAME = ""
PASSWORD = ""

# Base URL of the Mensa website (https://example.giro-web.de/index.php)
BASE_URL = ""

# Week to fetch (0 for current, 1 for next, etc. incase your mensa provides more weeks)
TARGET_WEEKS = [0, 1]  

# Session to reuse connection
session = requests.Session()

def get_initial_data(base_url):
    """Gets initial cookies, logidpost, and proc."""
    print("Fetching initial data...")
    response = session.get(base_url)
    soup = BeautifulSoup(response.text, 'html.parser')

    form = soup.find('form', id='loginform')
    proc = form.find('input', {'name': 'proc'})['value']
    logidpost = form.find('input', {'name': 'logidpost'})['value']

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
    session.post(base_url, data=login_data, cookies=cookies)

def fetch_mensa_plan(target_week):
    """Fetches the Mensa plan for the specified week."""
    data = {
        'wochenwahl': target_week,
        'sid': '1000000041' # Assuming this is static for now, changes depending on who you are (user, class, something else, or maybe entirely different for other Mensas)
    }
    print(f"Fetching Mensa plan for week {target_week}...")
    return session.post(BASE_URL, data=data)

def create_openmensa_feed(gwdata_json_list):
    """Creates a single OpenMensa feed."""
    canteen = LazyBuilder()
    school_id = gwdata_json_list[0]["ersteller"]["schulenid"] 
    personen_id = gwdata_json_list[0]["ersteller"]["personenid"]  # Get the personenID

    for i, gwdata_json in enumerate(gwdata_json_list):
        today = date.today()
        this_monday = today - timedelta(days=today.weekday())
        target_monday = this_monday + timedelta(weeks=i) 

        for day_num in range(5):
            day = target_monday + timedelta(days=day_num)
            day_str = day.strftime("%d.%m.%Y")

            for menu_num in range(1, 4):
                menu_data = gwdata_json["personenliste"][personen_id]["menueplan"][school_id][str(menu_num)].get(day_str)

                if menu_data and menu_data["menueplanid"] is not None:
                    # Remove allergy squares and extra spaces from the meal name
                    meal_name = " ".join([line.strip() for line in menu_data["zeilen"] if line])
                    meal_name = re.sub(r'\[.*?\]', '', meal_name)
                    meal_name = ' '.join(meal_name.split())  # Remove extra spaces 
                    
                    notes = [gwdata_json["zusatzstoffe"][str(zusatzstoff_id)] for zusatzstoff_id in menu_data["zusatzstoffeids"]]
                    prices = {'student': menu_data["preislistenpreis_ggf_subventioniert"]}

                    canteen.addMeal(day, "Hauptgericht", meal_name, notes=notes, prices=prices, roles=['student'])

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
            gwdata_json_list.append(json.loads(gwdata_input['value']))
        else:
            print(f"No 'gwdata' found for week {target_week}.")

    print("Creating OpenMensa feed...")
    openmensa_feed = create_openmensa_feed(gwdata_json_list)

    # Create the output folder if it doesn't exist
    output_folder = "output"
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    output_file_path = os.path.join(output_folder, "mensa.xml")  

    print(f"Saving OpenMensa feed to '{output_file_path}'...")
    with open(output_file_path, 'w', encoding='utf-8') as f:
        f.write(openmensa_feed)
    print("Done!")
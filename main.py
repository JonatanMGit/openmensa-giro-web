import requests
from bs4 import BeautifulSoup
import json
from datetime import date, timedelta
from pyopenmensa.feed import LazyBuilder

requests.packages.urllib3.util.ssl_.DEFAULT_CIPHERS += ':HIGH:!DH:!aNULL'  # Giroweb does not support good ciphers :(

# Your login credentials
USERNAME = ""
PASSWORD = ""

# Base URL of the Mensa website (https://https://example.giro-web.de/index.php/index.php)
BASE_URL = ""

# Week to fetch (0 for current, 1 for next, etc.)
TARGET_WEEKS = [0, 1]  


def get_initial_cookies_and_form_data(base_url):
    """Gets initial cookies, logidpost, and proc from the initial page load."""
    response = requests.get(base_url, verify=False)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Extract form data
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

    response = requests.post(base_url, data=login_data, cookies=cookies, verify=False)
    return response


def fetch_mensa_plan(base_url, cookies, target_week):
    """Fetches the Mensa plan for the specified week."""
    data = {
        'wochenwahl': target_week,
        'sid': '1000000041',  # Assuming this is static for now, changes depending on who you are (user, class, something else)
        'btun': '',
        'btup': '',
        'cardnum': ''
    }

    response = requests.post(base_url, data=data, cookies=cookies, verify=False)
    return response


def create_openmensa_feed(gwdata_json_list):
    """Creates a single OpenMensa feed from 'gwdata' JSON for multiple weeks."""
    canteen = LazyBuilder()
    
    school_id = gwdata_json_list[0]["ersteller"]["schulenid"] 

    # Loop through the list of gwdata_json for each week
    for gwdata_json in gwdata_json_list:
        # Extract the base date from the 'zeiten' section and convert it to YYYY-MM-DD format
        date_parts = gwdata_json["zeiten"]["datumwahl"].split('.')
        base_date = date(int(date_parts[2]), int(date_parts[1]), int(date_parts[0]))

        first_day_of_week = base_date - timedelta(days=base_date.weekday())

        # Loop through the weekdays (Mon-Fri)
        for day_num in range(5):
            day = first_day_of_week + timedelta(days=day_num)
            day_str = day.strftime("%d.%m.%Y")

            # Loop through the menus for each day
            for menu_num in range(1, 4):
                menu_data = gwdata_json["personenliste"]["10744"]["menueplan"][school_id][str(menu_num)]

                # Check if the date exists within the 'menueplan' data
                if day_str in menu_data:
                    menu_data = menu_data[day_str]

                    if menu_data["menueplanid"] is not None:
                        # Combine the meal lines into a single string, ensuring proper encoding
                        meal_name = " ".join([line.strip() for line in menu_data["zeilen"] if line is not None])
                        meal_name = meal_name.replace("  ", " ")  # Remove double spaces
                        meal_name = meal_name.strip()  # Remove leading/trailing spaces
                        category = "Hauptgericht"  # Assuming all meals are main courses
                        notes = [gwdata_json["zusatzstoffe"][str(zusatzstoff_id)] for zusatzstoff_id in menu_data["zusatzstoffeids"]]
                        prices = {'student': menu_data["preislistenpreis_ggf_subventioniert"]}  # Price in Euros now

                        canteen.addMeal(day, category, meal_name, notes=notes, prices=prices, roles=['student'])

    return canteen.toXMLFeed()

if __name__ == "__main__":
    # Get initial cookies and form data
    cookies, proc, logidpost = get_initial_cookies_and_form_data(BASE_URL)

    login_response = login(BASE_URL, USERNAME, PASSWORD, cookies, proc, logidpost)

    # Fetch Mensa plans for multiple weeks
    gwdata_json_list = []
    for target_week in TARGET_WEEKS:
        # Fetch Mensa plan
        mensa_plan_response = fetch_mensa_plan(BASE_URL, login_response.cookies, target_week)
        
        soup = BeautifulSoup(mensa_plan_response.text, 'html.parser')
        gwdata_input = soup.find('input', {'id': 'gwdata'})

        if gwdata_input:
            gwdata_json = json.loads(gwdata_input['value'])
            gwdata_json_list.append(gwdata_json)
        else:
            print(f"Couldn't find the 'gwdata' element for week {target_week}.  Mensa plan might not be available.")

    # Create a single feed combining both weeks
    openmensa_feed = create_openmensa_feed(gwdata_json_list)

    print(openmensa_feed)
    with open('mensa.xml', 'w', encoding='utf-8') as f:
        f.write(openmensa_feed)
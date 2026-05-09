#!/usr/bin/env python3

"""
A command-line utility to track movie streaming availability across paid and free platforms. Checks US availability by default, with an option to search internationally. Searches are saved to a local JSON watchlist, allowing users to easily poll for status updates and receive native system notifications when a movie's streaming status changes.
"""

import datetime
import json
import os
from pathlib import Path
import requests
import sys
import subprocess
import platform

TMDB_API_KEY = os.environ.get("TMDB_API_KEY")
HOME_DIR = Path.home()
CONFIG_DIR = HOME_DIR / ".config" / "streamcheck"
DATA_FILE = CONFIG_DIR / "watchlist.json"

def send_notification(title, message): 
    system = platform.system()
    
    try: 
        if system == "Linux": 
            subprocess.run(["notify-send", title, message])
            
        elif system == "Darwin": 
            script = f'display notification "{message}" with title "{title}"'
            subprocess.run(["osascript", "-e", script])
    except Exception as e: 
        print(f"⚠️ Notification failed: {e}")
        
def open_watchlist_file():
    system = platform.system()
    
    if system == "Darwin":      # macOS
        subprocess.call(["open", DATA_FILE])
    elif system == "Linux":     # Linux
        subprocess.call(["xdg-open", DATA_FILE])


class WatchlistManager:
    def __init__(self):
        self.home = HOME_DIR
        self.config_dir = CONFIG_DIR
        self.data_file = DATA_FILE
        self.ensure_setup()
        
    def ensure_setup(self):
        if not self.config_dir.exists():
            self.config_dir.mkdir(parents=True)
            print(f"📁 Created config directory: {self.config_dir}")
            
        if not self.data_file.exists():
            self.save_data({})
            print(f"📄 Created new watchlist file: {self.data_file}")
            
    def load_data(self):
        try:
            with open(self.data_file, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            return {}
        except json.JSONDecodeError:
            print(f"❌ CRITICAL ERROR: Your watchlist file is corrupted or contains invalid JSON.")
            print(f"Please manually fix the file at {self.data_file} before running streamcheck again.")
            sys.exit(1)
        
    def save_data(self, data):
        with open(self.data_file, 'w') as f:
            json.dump(data, f, indent=4)
            
    def add_movie(self, movie_id, title, streaming_status=False):
        data = self.load_data()
        str_id = str(movie_id)
        
        data[str_id] = {
            "title": title, 
            "streaming_in_us": streaming_status, 
            "last_checked": None
        }
        self.save_data(data)
        print(f"💾 Saved '{title}' to watchlist.")
        
    def remove_last(self): 
        data = self.load_data()
        
        if not data:
            print("The list is already empty.")
            return
        
        last_key, last_value = data.popitem()
        self.save_data(data)
        print(f"Removed {last_value['title']}")
        
    def check_watchlist(self, movie_finder):
        data = self.load_data()
        now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        updates_found = False
        
        print(f"🕵️ Checking {len(data)} movies in watchlist...")

        for movie_id, info in data.items():
            title = info['title']
            old_status = info['streaming_in_us']
            
            providers = movie_finder.get_providers(movie_id)
            
            us_info = providers.get('US', {})
            stream_list = us_info.get('flatrate', []) + us_info.get('ads', []) + us_info.get('free', [])
            new_status = bool(stream_list)
            
            info['last_checked'] = now
            updates_found = True
            
            if new_status != old_status: 
                if new_status:
                    provider_names = ", ".join([p['provider_name'] for p in stream_list])
                    msg = f"{title} is now streaming on: {provider_names}"
                    print(f"🔔 ALERT: {msg}")
                    send_notification("Movie Found!", msg)
                else: 
                    print(f"📉 {title} has left streaming services.")
                
                info['streaming_in_us'] = new_status
        
        if updates_found:
            self.save_data(data)
            print("✅ Watchlist updated.")
        else: 
            print("💤 No changes found.")
            

class MovieFinder:
    def __init__(self, api_key): 
        self.api_key = api_key
        self.base_url = "https://api.themoviedb.org/3"
        
    def search_movie(self, query): 
        url = f"{self.base_url}/search/movie"
        params = {"api_key": self.api_key, "query": query}

        try: 
            response = requests.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data['results']:
                first_result = data['results'][0]
                title = first_result['title']
                date = first_result.get('release_date') or "????"
                year = date[:4]
                
                return first_result['id'], f"{title} ({year})"
        
            return None, None
        except requests.RequestException as e: 
            print(f"❌ Network error: {e}")
            sys.exit(1)
            
    def get_providers(self, movie_id):
        url = f"{self.base_url}/movie/{movie_id}/watch/providers"
        params = {"api_key": self.api_key}
        
        try: 
            response = requests.get(url, params=params)
            data = response.json()
            return data.get('results', {})
        except requests.RequestException:
            return {}


def print_services(providers, country_code): 
    if country_code not in providers:
        return False
        
    flatrate = providers[country_code].get('flatrate', [])
    if not flatrate: 
        return False
        
    countries = {
        "AD": "Andorra",
        "AE": "United Arab Emirates",
        "AF": "Afghanistan",
        "AG": "Antigua and Barbuda",
        "AI": "Anguilla",
        "AL": "Albania",
        "AM": "Armenia",
        "AO": "Angola",
        "AQ": "Antarctica",
        "AR": "Argentina",
        "AS": "American Samoa",
        "AT": "Austria",
        "AU": "Australia",
        "AW": "Aruba",
        "AX": "Åland Islands",
        "AZ": "Azerbaijan",
        "BA": "Bosnia and Herzegovina",
        "BB": "Barbados",
        "BD": "Bangladesh",
        "BE": "Belgium",
        "BF": "Burkina Faso",
        "BG": "Bulgaria",
        "BH": "Bahrain",
        "BI": "Burundi",
        "BJ": "Benin",
        "BL": "Saint Barthélemy",
        "BM": "Bermuda",
        "BN": "Brunei Darussalam",
        "BO": "Bolivia (Plurinational State of)",
        "BQ": "Bonaire, Sint Eustatius and Saba",
        "BR": "Brazil",
        "BS": "Bahamas",
        "BT": "Bhutan",
        "BV": "Bouvet Island",
        "BW": "Botswana",
        "BY": "Belarus",
        "BZ": "Belize",
        "CA": "Canada",
        "CC": "Cocos (Keeling) Islands",
        "CD": "Congo (The Democratic Republic of the)",
        "CF": "Central African Republic",
        "CG": "Congo",
        "CH": "Switzerland",
        "CI": "Côte d'Ivoire",
        "CK": "Cook Islands",
        "CL": "Chile",
        "CM": "Cameroon",
        "CN": "China",
        "CO": "Colombia",
        "CR": "Costa Rica",
        "CU": "Cuba",
        "CV": "Cabo Verde",
        "CW": "Curaçao",
        "CX": "Christmas Island",
        "CY": "Cyprus",
        "CZ": "Czechia",
        "DE": "Germany",
        "DJ": "Djibouti",
        "DK": "Denmark",
        "DM": "Dominica",
        "DO": "Dominican Republic",
        "DZ": "Algeria",
        "EC": "Ecuador",
        "EE": "Estonia",
        "EG": "Egypt",
        "EH": "Western Sahara",
        "ER": "Eritrea",
        "ES": "Spain",
        "ET": "Ethiopia",
        "FI": "Finland",
        "FJ": "Fiji",
        "FK": "Falkland Islands (Malvinas)",
        "FM": "Micronesia (Federated States of)",
        "FO": "Faroe Islands",
        "FR": "France",
        "GA": "Gabon",
        "GB": "United Kingdom of Great Britain and Northern Ireland",
        "GD": "Grenada",
        "GE": "Georgia",
        "GF": "French Guiana",
        "GG": "Guernsey",
        "GH": "Ghana",
        "GI": "Gibraltar",
        "GL": "Greenland",
        "GM": "Gambia",
        "GN": "Guinea",
        "GP": "Guadeloupe",
        "GQ": "Equatorial Guinea",
        "GR": "Greece",
        "GS": "South Georgia and the South Sandwich Islands",
        "GT": "Guatemala",
        "GU": "Guam",
        "GW": "Guinea-Bissau",
        "GY": "Guyana",
        "HK": "Hong Kong",
        "HM": "Heard Island and McDonald Islands",
        "HN": "Honduras",
        "HR": "Croatia",
        "HT": "Haiti",
        "HU": "Hungary",
        "ID": "Indonesia",
        "IE": "Ireland",
        "IL": "Israel",
        "IM": "Isle of Man",
        "IN": "India",
        "IO": "British Indian Ocean Territory",
        "IQ": "Iraq",
        "IR": "Iran (Islamic Republic of)",
        "IS": "Iceland",
        "IT": "Italy",
        "JE": "Jersey",
        "JM": "Jamaica",
        "JO": "Jordan",
        "JP": "Japan",
        "KE": "Kenya",
        "KG": "Kyrgyzstan",
        "KH": "Cambodia",
        "KI": "Kiribati",
        "KM": "Comoros",
        "KN": "Saint Kitts and Nevis",
        "KP": "Korea (The Democratic People's Republic of)",
        "KR": "Korea (The Republic of)",
        "KW": "Kuwait",
        "KY": "Cayman Islands",
        "KZ": "Kazakhstan",
        "LA": "Lao People's Democratic Republic",
        "LB": "Lebanon",
        "LC": "Saint Lucia",
        "LI": "Liechtenstein",
        "LK": "Sri Lanka",
        "LR": "Liberia",
        "LS": "Lesotho",
        "LT": "Lithuania",
        "LU": "Luxembourg",
        "LV": "Latvia",
        "LY": "Libya",
        "MA": "Morocco",
        "MC": "Monaco",
        "MD": "Moldova (The Republic of)",
        "ME": "Montenegro",
        "MF": "Saint Martin (French part)",
        "MG": "Madagascar",
        "MH": "Marshall Islands",
        "MK": "North Macedonia",
        "ML": "Mali",
        "MM": "Myanmar",
        "MN": "Mongolia",
        "MO": "Macao",
        "MP": "Northern Mariana Islands",
        "MQ": "Martinique",
        "MR": "Mauritania",
        "MS": "Montserrat",
        "MT": "Malta",
        "MU": "Mauritius",
        "MV": "Maldives",
        "MW": "Malawi",
        "MX": "Mexico",
        "MY": "Malaysia",
        "MZ": "Mozambique",
        "NA": "Namibia",
        "NC": "New Caledonia",
        "NE": "Niger",
        "NF": "Norfolk Island",
        "NG": "Nigeria",
        "NI": "Nicaragua",
        "NL": "Netherlands",
        "NO": "Norway",
        "NP": "Nepal",
        "NR": "Nauru",
        "NU": "Niue",
        "NZ": "New Zealand",
        "OM": "Oman",
        "PA": "Panama",
        "PE": "Peru",
        "PF": "French Polynesia",
        "PG": "Papua New Guinea",
        "PH": "Philippines",
        "PK": "Pakistan",
        "PL": "Poland",
        "PM": "Saint Pierre and Miquelon",
        "PN": "Pitcairn",
        "PR": "Puerto Rico",
        "PS": "Palestine, State of",
        "PT": "Portugal",
        "PW": "Palau",
        "PY": "Paraguay",
        "QA": "Qatar",
        "RE": "Réunion",
        "RO": "Romania",
        "RS": "Serbia",
        "RU": "Russian Federation",
        "RW": "Rwanda",
        "SA": "Saudi Arabia",
        "SB": "Solomon Islands",
        "SC": "Seychelles",
        "SD": "Sudan",
        "SE": "Sweden",
        "SG": "Singapore",
        "SH": "Saint Helena, Ascension and Tristan da Cunha",
        "SI": "Slovenia",
        "SJ": "Svalbard and Jan Mayen",
        "SK": "Slovakia",
        "SL": "Sierra Leone",
        "SM": "San Marino",
        "SN": "Senegal",
        "SO": "Somalia",
        "SR": "Suriname",
        "SS": "South Sudan",
        "ST": "Sao Tome and Principe",
        "SV": "El Salvador",
        "SX": "Sint Maarten (Dutch part)",
        "SY": "Syrian Arab Republic",
        "SZ": "Eswatini",
        "TC": "Turks and Caicos Islands",
        "TD": "Chad",
        "TF": "French Southern Territories",
        "TG": "Togo",
        "TH": "Thailand",
        "TJ": "Tajikistan",
        "TK": "Tokelau",
        "TL": "Timor-Leste",
        "TM": "Turkmenistan",
        "TN": "Tunisia",
        "TO": "Tonga",
        "TR": "Türkiye",
        "TT": "Trinidad and Tobago",
        "TV": "Tuvalu",
        "TW": "Taiwan (Province of China)",
        "TZ": "Tanzania, United Republic of",
        "UA": "Ukraine",
        "UG": "Uganda",
        "UM": "United States Minor Outlying Islands",
        "US": "United States of America",
        "UY": "Uruguay",
        "UZ": "Uzbekistan",
        "VA": "Holy See",
        "VC": "Saint Vincent and the Grenadines",
        "VE": "Venezuela (Bolivarian Republic of)",
        "VG": "Virgin Islands (British)",
        "VI": "Virgin Islands (U.S.)",
        "VN": "Viet Nam",
        "VU": "Vanuatu",
        "WF": "Wallis and Futuna",
        "WS": "Samoa",
        "YE": "Yemen",
        "YT": "Mayotte",
        "ZA": "South Africa",
        "ZM": "Zambia",
        "ZW": "Zimbabwe"
    }    
    
    country_name = countries.get(country_code, country_code)
        
    print(f"\n🌍 {country_name} Streaming:")
    for service in flatrate:
        print(f"  🎞️  {service['provider_name']}")
    return True
    
def list_all_movies(movie_finder, data, country_code): 
    print(f"list movies:")
    
    for movie_id, movie_data in data.items():
        providers = movie_finder.get_providers(movie_id)
        print(f"🍿️ {movie_data['title']}")
        
        if country_code in providers: 
            p_info = providers.get(country_code, {})
            stream_list = p_info.get('flatrate', []) + p_info.get('ads', []) + p_info.get('free', [])
            
            if not stream_list:
                print(f"Not streaming in {country_code}")
            else: 
                streamers = ", ".join([p['provider_name'] for p in stream_list])
                print(f"Streaming in {country_code} on: {streamers}")
                
        else: 
            print(f"Not streaming in {country_code}")
        
        print(f"\n")
    
        
if __name__ == "__main__":
    def show_help():
        print("Usage:")
        print("  Search: streamcheck \"Movie Name\"")
        print("  Refresh list of saved movies: streamcheck --check")
        print("  List all saved movies: streamcheck --list")
        print("  Remove the movie most recently saved to the list: streamcheck --remove-last")
        print("  Edit watchlist file: streamcheck --edit")
        sys.exit(1)

    if len(sys.argv) < 2:
        show_help()
    
    arg = sys.argv[1].lower()
    
    if arg in ["help", "--help", "-h", "-?", "/?", "/h", "usage"]:
        show_help()
        
    if not TMDB_API_KEY:
        print("❌ Error: TMDB_API_KEY environment variable not set.")
        sys.exit(1)
    
    mf = MovieFinder(TMDB_API_KEY)
    wm = WatchlistManager()
    
    if arg == "--check":
        wm.check_watchlist(mf)
    elif arg in ["--list", "-l"]:
        data = wm.load_data()
        list_all_movies(mf, data, 'US')
    elif arg in ['-rl', '--remove-last']:
        wm.remove_last()
    elif arg in ['-e', '--edit']:
        open_watchlist_file()
    else: 
        query = arg

        print(f"🔎 Searching for '{query}'...")
        movie_id, display_title = mf.search_movie(query)
    
        if not movie_id:
            print(f"❌ Could not find movie: {query}")
            sys.exit(1)
        
        print(f"Found: {display_title}")
    
        all_providers = mf.get_providers(movie_id)
        is_streaming_us = False
            
        us_info = all_providers.get('US', {})
        stream_list = us_info.get('flatrate', []) + us_info.get('ads', []) + us_info.get('free', [])
            
        if stream_list:
            
            print(f"\n🌍 US Streaming:")
            for s in stream_list:
                print(f"  🎞️  {s['provider_name']}")
            is_streaming_us = True
            
        else: 
            print("\n❌ Not currently streaming in the US.")
        
        wm.add_movie(movie_id, display_title, is_streaming_us)
    
        print("\nCheck all other countries? (y/n): ", end="", flush=True)
        if sys.stdin.readline().strip().lower() == 'y':
            found_any = False
            for country, data in all_providers.items():
                if country == 'US': continue
                if print_services(all_providers, country): 
                    found_any = True
                    
            if not found_any: 
                print("❌ Not streaming anywhere else either.")

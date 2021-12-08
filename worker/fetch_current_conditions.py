# File to fetch current resort conditions HTML and parse via beautiful soup
from bs4 import BeautifulSoup
import requests

# Initializing Mountain Constants
COPPER = 'Copper'
ELDORA = 'Eldora'
STEAMBOAT = 'Steamboat'
WINTER_PARK = 'Winter Park'

# Initializing Resort Name to URL mapping
resort_to_url = {
    COPPER: "https://www.coppercolorado.com/the-mountain/conditions-weather/snow-report",
    ELDORA: "https://www.eldora.com/the-mountain/conditions-weather/current-conditions-forecast",
    STEAMBOAT: "https://www.steamboat.com/the-mountain/mountain-report#/",
    WINTER_PARK: "https://www.winterparkresort.com/the-mountain/mountain-report#/"
}


# Fetch the current conditions for the given resort name, returns JSON format
def scrape_resort_conditions_page(resort_name):
    conditions_url = resort_to_url[resort_name]
    response = requests.get(conditions_url)
    raw_html = response.text
    resort_not_found_response = {"ERROR resort not found"}

    if resort_name == COPPER:
        return read_copper_conditions(raw_html)
    elif resort_name == ELDORA:
        return read_eldora_conditions(raw_html)
    elif resort_name == STEAMBOAT:
        return read_steamboat_conditions(raw_html)
    elif resort_name == WINTER_PARK:
        return read_winter_park_conditions(raw_html)
    else:
        return resort_not_found_response


# Debugging function to return pretty HTML version of a webpage
def parse_raw_html_for_conditions(raw_hmtl):
    conditions_soup = BeautifulSoup(raw_hmtl, 'html.parser')
    pretty_soup = conditions_soup.prettify()
    return pretty_soup


# Format the current weather conditions to a standard JSON style
def format_conditions_json(new_snow_inches, wind_speed, lifts_open, trails_open):
    conditions_json = {
        'NewSnowInches': new_snow_inches,
        'WindSpeed': wind_speed,
        'LiftsOpen': lifts_open,
        'TrailsOpen': trails_open
    }
    return conditions_json


# Read HTML file for conditions form Winter Park
def read_winter_park_conditions(raw_html):
    conditions_soup = BeautifulSoup(raw_html, 'html.parser')

    wind_speed = "-1"
    imperial_stats = conditions_soup.find_all('div', class_="switchable-stat-item switchable-stat-imperial")
    for tag in imperial_stats:
        tag_label = tag.find('span', class_="label")
        if tag_label:
            tag_label_text = tag_label.get_text()
            if tag_label_text == "Wind Speed":
                wind_speed = tag.find('span', class_='value').get_text()
                continue
        else:
            continue

    expected_snowfall_list_item = conditions_soup.find_all('li', class_="weather-forecast-snowfall-list-item")[0]
    new_snow_inches = expected_snowfall_list_item.find('div', class_="switchable-stat-item switchable-stat-imperial")\
        .find('span', class_="value")\
        .get_text()

    # list tag for open lifts and trails
    trail_conditions_tags = conditions_soup.find_all('li', class_="conditions-trails-content-others-metric")

    lifts_open = -1
    trails_open = -1
    for tag in trail_conditions_tags:
        metric_name = tag.find('p', class_="conditions-trails-content-others-metric-name").get_text()
        metric_value = tag.find('p', class_="conditions-trails-content-others-metric-value").get_text()

        if metric_name == 'Open Lifts':
            # if this tag is the Open Lifts metric name, the value after it is the number of lifts open
            lifts_open = metric_value
        elif metric_name == 'Open Trails':
            trails_open = metric_value

    return format_conditions_json(new_snow_inches, wind_speed, lifts_open, trails_open)


# Read Raw HTML from Copper Mountain to get snow report
def read_copper_conditions(raw_html):
    conditions_soup = BeautifulSoup(raw_html, 'html.parser')

    new_snow_inches = -1

    wind_speed = -1

    lifts_open = -1

    trail_open = -1

    return format_conditions_json(new_snow_inches, wind_speed, lifts_open, trail_open)


# Read Raw HTML from Eldora Mountain to get snow report
def read_eldora_conditions(raw_html):
    conditions_soup = BeautifulSoup(raw_html, 'html.parser')

    new_snow_inches = -1

    wind_speed = -1

    lifts_open = -1

    trail_open = -1

    return format_conditions_json(new_snow_inches, wind_speed, lifts_open, trail_open)


# Read Raw HTML from Copper Mountain to get snow report
def read_steamboat_conditions(raw_html):
    new_snow_inches = -1

    wind_speed = -1

    lifts_open = -1

    trail_open = -1

    return format_conditions_json(new_snow_inches, wind_speed, lifts_open, trail_open)

def main():
    print("Fetching Winter Park Conditions")
    wp_conditions = scrape_resort_conditions_page(WINTER_PARK)
    print(wp_conditions)

    print("Fetching Copper Conditions")
    copper_conditions = scrape_resort_conditions_page(COPPER)
    print(copper_conditions)

    print("Fetching Eldora Conditions")
    eldora_conditions = scrape_resort_conditions_page(ELDORA)
    print(eldora_conditions)

    print("Fetching Steamboat Conditions")
    steamboat_conditions = scrape_resort_conditions_page(STEAMBOAT)
    print(steamboat_conditions)

if __name__ == "__main__":
    main()
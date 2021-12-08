# File to fetch current resort conditions HTML and parse via beautiful soup
from bs4 import BeautifulSoup
import requests
import sys

# fetch the raw HTML for the given conditions URL
def scrape_resort_conditions_page(conditions_url):
    response = requests.get(conditions_url)
    raw_html = response.text
    return raw_html

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

def main():
    print("Running main")
    conditions_url = 'https://www.winterparkresort.com/the-mountain/mountain-report#/'
    raw_html = scrape_resort_conditions_page(conditions_url)
    # Uncomment to debug Raw HTML
    #pretty_html = parse_raw_html_for_conditions(raw_html)

    conditions = read_winter_park_conditions(raw_html)
    print(conditions)

if __name__ == "__main__":
    main()
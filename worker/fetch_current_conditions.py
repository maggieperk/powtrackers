# File to fetch current resort conditions HTML and parse via beautiful soup
from bs4 import BeautifulSoup
from pyppeteer import launch

import asyncio
import pika
import platform
import os
import re
import requests
import sys

rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"

#
# This is the payload format used in the solution. It doesn't specify a callback,
# so you'll need to test that out another way or modify this example.
#

workerJson = {'resorts': [
    'Eldora',
    'Copper',
    'Winter Park',
    'Steamboat']}

rabbitMQ = pika.BlockingConnection(
    pika.ConnectionParameters(host=rabbitMQHost))
rabbitMQChannel = rabbitMQ.channel()

rabbitMQChannel.exchange_declare(exchange='logs', exchange_type='topic')
infoKey = f"{platform.node()}.worker.info"
debugKey = f"{platform.node()}.worker.debug"
#
# A helpful function to send a log message
#
def log_debug(message, key=debugKey):
    print("DEBUG:", message, file=sys.stderr)
    rabbitMQChannel.basic_publish(
        exchange='logs', routing_key=key, body=message)

# Initializing Mountain Constants
COPPER = 'Copper'
ELDORA = 'Eldora'
STEAMBOAT = 'Steamboat'
WINTER_PARK = 'Winter Park'

# Initializing Resort Name to URL mapping
resort_to_url = {
    COPPER: "https://www.coppercolorado.com/the-mountain/conditions-weather/snow-report",
    ELDORA: "https://www.eldora.com/the-mountain/conditions-weather/current-conditions-forecast",
    #ELDORA: "https://www.eldora.com/the-mountain/conditions-weather/current-conditions-forecast?utm_source=Google&utm_medium=Cross-Device-Text&utm_campaign=DLA-Eldora-2021-POWDR-Eldora-Winter&utm_term=Search-Audience-Keywords-NA-Priority-Markets&utm_content=Multi&gclid=CjwKCAiAwKyNBhBfEiwA_mrUMoPu-j8ZjkHsFlTHMJmO94hZEZijWfbk3IwAPTY3oBm27sApQNFS4xoCqIQQAvD_BwE&gclsrc=aw.ds",
    STEAMBOAT: "https://www.steamboat.com/the-mountain/mountain-report#/",
    WINTER_PARK: "https://www.winterparkresort.com/the-mountain/mountain-report#/"
}

# Initialize static text conditions for resorts
resort_to_static_text = {
    COPPER: "CopperConditions.txt",
    ELDORA: "EldoraConditions.txt",
    STEAMBOAT: "SteamboatConditions.txt",
    WINTER_PARK: "WinterParkConditions.txt"
}


async def render_javascript_with_pyppeteer(url_name):
    try:
        browser = await launch(headless=True, args=["--disable-gpu",
                                    "--disable-dev-shm-usage",
                                    "--disable-setuid-sandbox",
                                    "--no-sandbox"])
        page = await browser.newPage()
        response = await page.goto(url_name)
        content = await page.content()
        log_debug(f"Page response was {response}")
        await browser.close()
        return content

    except Exception as e:
        log_debug(f"Exception hit while rendering JavaScript code: {e}")
        return None

# Fetch the current conditions for the given resort name, returns JSON format
def scrape_resort_conditions_page(resort_name):
    conditions_url = resort_to_url[resort_name]
    resort_not_found_response = {"ERROR resort not found"}

    if resort_name == COPPER:
        loop = asyncio.get_event_loop()
        raw_html = loop.run_until_complete(render_javascript_with_pyppeteer(conditions_url))
        return read_copper_conditions(raw_html)
    elif resort_name == ELDORA:
        loop = asyncio.get_event_loop()
        raw_html = loop.run_until_complete(render_javascript_with_pyppeteer(conditions_url))
        return read_eldora_conditions(raw_html)
    elif resort_name == STEAMBOAT:
        loop = asyncio.get_event_loop()
        raw_html = loop.run_until_complete(render_javascript_with_pyppeteer(conditions_url))
        return read_steamboat_conditions(raw_html)
    elif resort_name == WINTER_PARK:
        response = requests.get(conditions_url)
        raw_html = response.text
        return read_winter_park_conditions(raw_html)
    else:
        return resort_not_found_response


# Use a static text document with the HTML for the website to produce conditions.  This is in the event
# That we cannot get JavaScript to render in the Docker context
def scrape_resort_pages_from_static_html(resort_name):
    conditions_text = resort_to_static_text[resort_name]
    resort_not_found_response = {"ERROR resort not found"}

    if resort_name == COPPER:
        return read_copper_conditions(conditions_text, static_page=True)
    elif resort_name == ELDORA:
        return read_eldora_conditions(conditions_text, static_page=True)
    elif resort_name == STEAMBOAT:
        return read_steamboat_conditions(conditions_text, static_page=True)
    elif resort_name == WINTER_PARK:
        return read_winter_park_conditions(conditions_text, static_page=True)
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
        "NewSnowInches": float(new_snow_inches),
        "WindSpeed": int(wind_speed),
        "LiftsOpen": int(lifts_open),
        "TrailsOpen": int(trails_open)
    }
    return conditions_json


# Read HTML file for conditions form Winter Park
def read_winter_park_conditions(raw_html, static_page=False):
    if static_page:
        with open(raw_html) as f:
            conditions_soup = BeautifulSoup(f.read(), 'html.parser')
    else:
        conditions_soup = BeautifulSoup(raw_html, 'html.parser')

    wind_speed = "-1"
    imperial_stats = conditions_soup.find_all('div', class_="switchable-stat-item switchable-stat-imperial")
    for tag in imperial_stats:
        tag_label = tag.find('span', class_="label")
        if tag_label:
            tag_label_text = tag_label.get_text()
            if tag_label_text == "Wind Speed":
                wind_speed = re.search(r'\d+', tag.find('span', class_='value').get_text())[0]
                continue
        else:
            continue

    expected_snowfall_list_item = conditions_soup.find_all('li', class_="weather-forecast-snowfall-list-item")[0]
    new_snow_inches = expected_snowfall_list_item.find('div', class_="switchable-stat-item switchable-stat-imperial")\
        .find('span', class_="value")\
        .get_text()

    # When no snow is expected at Winter Park, they report "--" instead of a numeric value
    if new_snow_inches == '--':
        new_snow_inches = 0

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
def read_copper_conditions(raw_html, static_page=False):
    if static_page:
        with open(raw_html) as f:
            conditions_soup = BeautifulSoup(f.read(), 'html.parser')
    else:
        conditions_soup = BeautifulSoup(raw_html, 'html.parser')

    # Find New Snow Value
    new_snow_inches = -1.0
    weather_widget_tags = conditions_soup.find_all('div', class_='widget-weather')
    for w_tag in weather_widget_tags:
        status_tag = w_tag.find('p', class_="status m-")
        if status_tag.text == 'snow':
            new_snow_inches = re.search(r'\d+(.\d+)?', w_tag.find('span', class_="integer m-").text)[0]

    # Wind Speed from Copper is not present on their website
    wind_speed = -1

    # Find Lifts and Trails Open
    lifts_open = -1
    trails_open = -1

    lift_open_found = False
    trail_open_found = False

    trail_and_lifts_div = conditions_soup.find_all('div', class_="dor-grid-item col col-6of12-m-5 base dor-colors u-m-b-10 u-p-a-10")
    for div_tag in trail_and_lifts_div:
        if lift_open_found and trail_open_found:
            break

        p_tag_text = div_tag.find('p', class_="dtr-type ng-scope").text
        if p_tag_text == "Open Trails":
            # The first text value is the # of currently open trails
            open_trails_text_tag = div_tag.find_all('text', class_="ng-binding")[0]
            trails_open = open_trails_text_tag.text
            trail_open_found = True
        elif p_tag_text == "Open Lifts":
            open_lifts_text_tag = div_tag.find_all('text', class_="ng-binding")[0]
            lifts_open = open_lifts_text_tag.text
            lift_open_found = True


    return format_conditions_json(new_snow_inches, wind_speed, lifts_open, trails_open)


# Read Raw HTML from Eldora Mountain to get snow report
# Open Trails in format: <strong>Open Trails</strong></span>
# <br />Hornblower<br />Windmill<br />International<br />La Belle<br />Hot Dog Alley<br />Chute<br />Bunnyfair<br />Ryder's<br /><br />
# </li>
# Open Lifts in format: <strong>Open Lifts</strong></span><br>Alpenglow<br>Race<br>EZ<br><br></li>
# AKA for both I should find the open trails list indicator, then get the following items in <br> and count
# Find Wind Speed: 22 to 32 miles per hour --> search for re w/ miles per hour and digits beforehand
def read_eldora_conditions(raw_html, static_page=False):
    if static_page:
        with open(raw_html) as f:
            conditions_soup = BeautifulSoup(f.read(), 'html.parser')
    else:
        conditions_soup = BeautifulSoup(raw_html, 'html.parser')

    # Search for wind and snow
    wind_speed = -1
    new_snow_inches = 0.0

    wind_match_found = False
    snow_match_found = False

    span_tags = conditions_soup.find_all('span')
    for s_tag in span_tags:
        if wind_match_found and snow_match_found:
            break

        s_text = s_tag.text
        wind_match = re.search(r'(\d+) miles per hour', s_text)
        # Should match the first instance of inch and/or inches in the snow report (if present)
        snow_match = re.search(r'(\d+) inch', s_text)

        if wind_match:
            wind_speed = wind_match[1]
            wind_match_found = True
        if snow_match:
            new_snow_inches = snow_match[1]
            snow_match_found = True

    # Find Open lifts and Trails
    list_tags = conditions_soup.find_all('li')

    lifts_open = -1
    trails_open = -1

    open_trails_found = False
    open_lifts_found = False

    for l_tag in list_tags:
        if open_lifts_found and open_trails_found:
            break
        if l_tag.find_all('span'):
            span_tag = l_tag.find_all('span')[0]
        else:
            continue

        if span_tag.text == 'Open Trails':
            # The number of br tags is equivalent to the # of open trails + 2 based on list format w/headers and empty line
            br_tags = l_tag.find_all('br')
            trails_open = len(br_tags) - 2
            open_trails_found = True
        elif span_tag.text == 'Open Lifts':
            # # of br tags = # of open lifts + 2 based on list format w/headers and empty line
            br_tags = l_tag.find_all('br')
            lifts_open = len(br_tags) - 2
            open_lifts_found = True

    return format_conditions_json(new_snow_inches, wind_speed, lifts_open, trails_open)


# Read Raw HTML from Steamboat to get snow report
def read_steamboat_conditions(raw_html, static_page=False):
    if static_page:
        with open(raw_html) as f:
            conditions_soup = BeautifulSoup(f.read(), 'html.parser')
    else:
        conditions_soup = BeautifulSoup(raw_html, 'html.parser')

    new_snow_inches = -1
    col_block_div = conditions_soup.find('div', class_="col conditions-block")
    data_tags = col_block_div.find_all('p')
    for dt in data_tags:
        if re.search('24 hour', dt.text):
            new_snow_inches = re.search(r'\d+.\d+', dt.text)[0]

    wind_speed_tag = conditions_soup.find('p', class_="wind-speed-text")
    wind_speed = re.search(r'\d+', wind_speed_tag.find('strong').text)[0]

    # Find Lifts and trails open values
    data_block_divs = conditions_soup.find('div', class_="col data-block")
    trails_open = data_block_divs.find_all('strong')[0].text

    data_block_main_divs = conditions_soup.find('div', class_="col data-block main-block")
    # This will return an n/m number so we only want the first value
    lifts_open = re.split('/', data_block_main_divs.find('div', class_="block-text").text)[0]

    return format_conditions_json(new_snow_inches, wind_speed, lifts_open, trails_open)

def main():
    # Run this locally to fetch all reent conditions files and save them for static reference
    # Test the static page load functions
    print("Writing Winter Park Conditions to file")
    with open(resort_to_static_text[WINTER_PARK], "w") as f:
        winter_park_conditions_url = resort_to_url[WINTER_PARK]
        response = requests.get(winter_park_conditions_url)
        raw_html_winter_park = response.text
        f.write(raw_html_winter_park)
    print("Wrote winter park conditions to file")
    winter_park_static_conditions = scrape_resort_pages_from_static_html(WINTER_PARK)
    print(f"Winter Park static conditions: {winter_park_static_conditions}")

    print("Writing Copper Conditions to file")
    with open(resort_to_static_text[COPPER], "w") as f:
        copper_conditions_url = resort_to_url[COPPER]
        loop = asyncio.get_event_loop()
        raw_html_copper = loop.run_until_complete(render_javascript_with_pyppeteer(copper_conditions_url))
        f.write(raw_html_copper)
    print("Wrote Copper conditions to file")
    copper_static_conditions = scrape_resort_pages_from_static_html(COPPER)
    print(f"Copper static conditions: {copper_static_conditions}")

    print("Writing Eldora Conditions to file")
    with open(resort_to_static_text[ELDORA], "w") as f:
        eldora_conditions_url = resort_to_url[ELDORA]
        loop = asyncio.get_event_loop()
        raw_html_eldora = loop.run_until_complete(render_javascript_with_pyppeteer(eldora_conditions_url))
        f.write(raw_html_eldora)
    print("Wrote Eldora conditions to file")
    eldora_static_conditions = scrape_resort_pages_from_static_html(ELDORA)
    print(f"Eldora static conditions: {eldora_static_conditions}")

    print("Writing Steamboat Conditions to file")
    with open(resort_to_static_text[STEAMBOAT], "w") as f:
        steamboat_conditions_url = resort_to_url[STEAMBOAT]
        loop = asyncio.get_event_loop()
        raw_html_steamboat= loop.run_until_complete(render_javascript_with_pyppeteer(steamboat_conditions_url))
        f.write(raw_html_steamboat)
    print("Wrote Steamboat conditions to file")
    steamboat_static_conditions = scrape_resort_pages_from_static_html(STEAMBOAT)
    print(f"Steamboat static conditions: {steamboat_static_conditions}")


    # To test fetching conditions from scrape resort page run these functions
    """
    print("\nFetching Winter Park Conditions")
    copper_conditions = scrape_resort_conditions_page(WINTER_PARK)
    print(copper_conditions)

    print("\nFetching Copper Conditions")
    copper_conditions = scrape_resort_conditions_page(COPPER)
    print(copper_conditions)

    print("\nFetching Eldora Conditions")
    eldora_conditions = scrape_resort_conditions_page(ELDORA)
    print(eldora_conditions)

    print("\nFetching Steamboat Conditions")
    steamboat_conditions = scrape_resort_conditions_page(STEAMBOAT)
    print(steamboat_conditions)
    """

if __name__ == "__main__":
    main()
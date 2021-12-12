import requests
import json

def getTravelInfo(coordinates_start, coordinates_end, API_KEY = ''):
    response = None
    if API_KEY != '': # for when we are actually using the API

        origins_string = "origins="
        for i, key in enumerate(coordinates_start.keys()):
            origins_string = origins_string + coordinates_start[key][0] + "%2C" + coordinates_start[key][1]

            if i < len(coordinates_end) - 1:
                origins_string = origins_string + "%7C"
    
        destinations_string = "&destinations="

        for i, key in enumerate(coordinates_end.keys()):
            destinations_string = destinations_string + coordinates_end[key][0] + "%2C" + coordinates_end[key][1]

            if i < len(coordinates_end) - 1:
                destinations_string = destinations_string + "%7C"

        url = "https://maps.googleapis.com/maps/api/distancematrix/json?" + origins_string + destinations_string + "&departure_time=now&key=" + API_KEY

        print(url)
        payload={}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)
        response = response.json()

    else:
        # TESTING PARSE OF OUTPUT W/OUT HAVING TO SUBMIT API REQUEST; breaks if only 1 is passed in; will return eldora everytime lol

        response = json.load(open('../testingAPIs/sampleMaps.json'))

    # Process the response and return as dictionary

    resortTrafficInfo = {}

    for key in coordinates_end.keys():
        resortTrafficInfo[key] = {"origin": response["origin_addresses"][0]}

    for key in resortTrafficInfo.keys():

        k = 0
        for i, destination in enumerate(response['destination_addresses']):
            if key in destination:
                k = i

        distance_kms = response["rows"][0]["elements"][k]["distance"]["text"].split(' ')
        resortTrafficInfo[key]['miles'] = float(distance_kms[0])*0.621371
    
        duration = response["rows"][0]["elements"][k]["duration"]["text"].split(' ')
    
        if len(duration) == 2: # case when we have less that 1 hour of travel time
            resortTrafficInfo[key]["time"] = {"hours": 0, duration[1]: int(duration[0])}
        else:
            resortTrafficInfo[key]["time"] = {"hours": int(duration[0]), duration[3]: int(duration[2])}
    
    return resortTrafficInfo

import requests
import json

coordinates_start = ['40.007719', '-105.261416'] # ECCR

#  # allow for multiple desitations at once:
# # order is Eldora, Steamboat, Copper, Winter Park 
coordinates_end = [['39.938086', '-105.584282'], ['40.455464', '-106.808369'], ['39.498871', '-106.139443'], ['39.886346', '-105.761533']] 

def getTravelInfo(coordinates_start, coordinates_end, API_KEY = ''):
    response = None
    if API_KEY != '': # for when we are actually using the API

        origins_string = "origins=" + coordinates_start[0] + "%2C" + coordinates_start[1]

        destinations_string = "&destinations="

        for i, coord in enumerate(coordinates_end):
            destinations_string = destinations_string + coordinates_end[i][0] + "%2C" + coordinates_end[i][1]

            if i < len(coordinates_end) - 1:
                destinations_string = destinations_string + "%7C"

        arrival_time = '8:50' # to do - needs to be as an integer in seconds since midnight, January 1, 1970 UTC :(
        avoid = 'tolls'


        url = "https://maps.googleapis.com/maps/api/distancematrix/json?" + origins_string + destinations_string + "&departure_time=now&key=" + API_KEY

        print(url)
        payload={}
        headers = {}

        response = requests.request("GET", url, headers=headers, data=payload)
        response = response.json()

    else:
        # TESTING PARSE OF OUTPUT W/OUT HAVING TO SUBMIT API REQUEST

        response = json.load(open('testingAPIs/sampleMaps.json'))

    # Process the response and return as dictionary

    resortTrafficInfo = {"Eldora": {"origin": response["origin_addresses"][0]}, "Steamboat":{"origin": response["origin_addresses"][0]}, "Copper":{"origin": response["origin_addresses"][0]}, "Winter Park":{"origin": response["origin_addresses"][0]}}

    for k, key in enumerate(resortTrafficInfo.keys()):

        distance_kms = response["rows"][0]["elements"][k]["distance"]["text"].split(' ')
        resortTrafficInfo[key]['miles'] = float(distance_kms[0])*0.621371
    
        duration = response["rows"][0]["elements"][k]["duration"]["text"].split(' ')
    
        if len(duration) == 2: # case when we have less that 1 hour of travel time
            resortTrafficInfo[key]['time'] = {'hours': 0, duration[1]: int(duration[0])}
        else:
            resortTrafficInfo[key]['time'] = {'hours': int(duration[0]), duration[3]: int(duration[2])}
    
    return resortTrafficInfo

print(getTravelInfo(coordinates_start, coordinates_end))
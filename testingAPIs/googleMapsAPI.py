import requests
import json

# coordinates_start = ['40.007719', '-105.261416'] # ECCR
# origins_string = "origins=" + coordinates_start[0] + "%2C" + coordinates_start[1]

#  # allow for multiple desitations at once:
# # order is Eldora, Steamboat, Copper, Winter Park 
# coordinates_end = [['39.938086', '-105.584282'], ['40.455464', '-106.808369'], ['39.498871', '-106.139443'], ['39.886346', '-105.761533']] 

# destinations_string = "&destinations=" 
# dest_end = ''
# for i, coord in enumerate(coordinates_end):
#     destinations_string = destinations_string + coordinates_end[i][0] + "%2C" + coordinates_end[i][1]

#     if i < len(coordinates_end) - 1:
#         destinations_string = destinations_string + "%7C"

# arrival_time = '8:50' # to do - needs to be as an integer in seconds since midnight, January 1, 1970 UTC :(
# avoid = 'tolls'

# API_KEY = 'FAKEAPI'


# url = "https://maps.googleapis.com/maps/api/distancematrix/json?" + origins_string + destinations_string + "&key=" + API_KEY

# print(url)
# payload={}
# headers = {}

# response = requests.request("GET", url, headers=headers, data=payload)

# print(response.text)

# TESTING PARSE OF OUTPUT W/OUT HAVING TO SUBMIT API REQUEST

response = json.load(open('testingAPIs/sampleMaps.json'))
print(response)

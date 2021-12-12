#!/usr/bin/env python3

import requests
import json
import os
import sys
import time

#
# Use localhost & port 5000 if not specified by environment variable REST
#
REST = os.getenv("REST") or "localhost:5000"
print(os.getenv("REST"))
# REST = "localhost:80"
##
# The following routine makes a JSON REST query of the specified type
# and if a successful JSON reply is made, it pretty-prints the reply
##


def mkReq(reqmethod, endpoint, data):
    print(f"Response to http://{REST}/{endpoint} request is")
    jsonData = json.dumps(data)
    response = reqmethod(f"http://{REST}/{endpoint}", data=jsonData,
                         headers={'Content-type': 'application/json'})
    print("STATUS CODE", response.status_code)
    if response.status_code == 200:
        jsonResponse = json.dumps(response.json(), indent=4, sort_keys=True)
        print(jsonResponse)
        return
    else:
        print(
            f"response code is {response.status_code}, raw response is {response.text}")
        return response.text

mkReq(requests.post, "apiv1/initConditionsDB",
      data = {'resorts': ['Eldora', 'Steamboat', 'Copper', 'Winter Park'],
             'App ID': 'd8bd1a82',
             'API': '3a31bf0c1217741c8d00c206034ca4ca'})

mkReq(requests.get, "apiv1/initResortDB",
      data = {'Eldora': '39.938086,-105.584282',
              'Steamboat': '40.455464,-106.808369',
              'Copper': '39.498871,-106.139443',
              'Winter Park': '39.886346,-105.761533',
              'ECCR': '40.007719,-105.261416'
            })
print('Sleeping...', end='')
time.sleep(100) # should fix this. should wait for response from rabbitMQ?
print('Awake!')

mkReq(requests.get, "apiv1/traffic",
      data={
          "start": "ECCR",
          "API": 'AIzaSyAxjuRYGbP3GMzv1o7__kBu0nL2qvy4_TA'
      })

mkReq(requests.get, "apiv1/getSkiSuggestions", data={
    'App ID': 'd8bd1a82',
    'API': '3a31bf0c1217741c8d00c206034ca4ca'
})

mkReq(requests.get, "apiv1/resortConditions/Eldora",
      data={
          'App ID': 'd8bd1a82',
          'API': '3a31bf0c1217741c8d00c206034ca4ca',
      })


# mkReq(requests.post, "apiv1/resortConditions/Eldora",
#       data=None)

sys.exit(0)

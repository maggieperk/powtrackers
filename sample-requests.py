#!/usr/bin/env python3

import requests
import json
import os
import sys


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


mkReq(requests.get, "apiv1/traffic",
      data={
          "home": "ECCR",
          "resort": "Eldora",
          "API": ''
      })

mkReq(requests.get, "apiv1/getSkiSuggestions", data=None)

mkReq(requests.get, "apiv1/resortConditions/Eldora",
      data=None)


mkReq(requests.post, "apiv1/resortConditions/Eldora",
      data=None)

sys.exit(0)

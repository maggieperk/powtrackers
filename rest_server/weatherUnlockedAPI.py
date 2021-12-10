import requests
import json


# allow for multiple desitations at once:
# # order is Eldora, Steamboat, Copper, Winter Park 
# coordinates = [['39.938086', '-105.584282'], ['40.455464', '-106.808369'], ['39.498871', '-106.139443'], ['39.886346', '-105.761533']] 



def getWeatherInfo(coordinates, appID = '', APP_KEY = ''):

    forecastData = ['temp_max_f', 'windspd_max_mph', 'snow_total_in', 'precip_total_in']
    currentData = ['wx_desc', 'temp_f', 'feelslike_f', 'vis_mi', 'winddir_compass']
    weatherData = {}

    coord_string = coordinates[0][:-3] + ',' + coordinates[1][:-3]
    url = "http://api.weatherunlocked.com/api/forecast/"+ coord_string +"?app_id=" + appID + "&app_key="+ APP_KEY
    print(url)
    rForecast = requests.get(url).json()

    url = "http://api.weatherunlocked.com/api/current/"+ coord_string +"?app_id=" + appID + "&app_key="+ APP_KEY
    print(url)
    rCurrent = requests.get(url).json()

    for key in forecastData:
        subDict = rForecast['Days'][1] #get current day totals
        weatherData[key] = subDict[key]

    for key in currentData:
        weatherData[key] = rCurrent[key]
        

    return weatherData

# print(getWeatherInfo(coordinates[:1], appID = 'X', APP_KEY = 'X'))
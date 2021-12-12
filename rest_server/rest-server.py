##
from flask import Flask, request, Response, jsonify

import datetime
import json
import platform
import io, os, sys
import pika, redis
import jsonpickle
from googleMapsAPI import getTravelInfo
from weatherUnlockedAPI import getWeatherInfo

# Initialize the Flask application
app = Flask(__name__)

coordinates_start = {'ECCR': ['40.007719', '-105.261416']}
# import logging
# log = logging.getLogger('werkzeug')
# log.setLevel(10) # should be the same as logging.DEBUG

##
## Configure test vs. production
##
redisHost = os.getenv("REDIS_HOST") or "localhost"
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"

print("Connecting to rabbitmq({}) and redis({})".format(rabbitMQHost,redisHost))

##
## Set up redis connections
##
db_locations = redis.Redis(host=redisHost, db=0, decode_responses=True)
db_conditions = redis.Redis(host=redisHost, db=1, decode_responses=True)
db_traffic = redis.Redis(host=redisHost, db=2, decode_responses=True)

##
## Set up rabbitmq connection
##
rabbitMQ = pika.BlockingConnection(
        pika.ConnectionParameters(host=rabbitMQHost))
rabbitMQChannel = rabbitMQ.channel()

rabbitMQChannel.queue_declare(queue='toWorker')
rabbitMQChannel.exchange_declare(exchange='logs', exchange_type='topic')
infoKey = f"{platform.node()}.worker.info"
debugKey = f"{platform.node()}.worker.debug"

def log_debug(message, key=debugKey):
    print("DEBUG:", message, file=sys.stdout)
    rabbitMQChannel.basic_publish(
        exchange='logs', routing_key=key, body=message)


def log_info(message, key=infoKey):
    print("INFO:", message, file=sys.stdout)
    rabbitMQChannel.basic_publish(
        exchange='logs', routing_key=key, body=message)


def sendToWorker(message_dict):
    connection = pika.BlockingConnection(pika.ConnectionParameters(rabbitMQHost))
    channel = connection.channel()
    channel.queue_declare(queue='toWorker')
    channel.basic_publish(exchange = '', routing_key = 'toWorker', body=jsonpickle.encode(message_dict), properties = pika.BasicProperties(delivery_mode=2))
    channel.close()
    connection.close()


# Initialize resort info database
@app.route("/apiv1/initResortDB", methods = ['GET'])
def initResortDB():
    json = request.get_json()
    for key in json.keys():
        db_locations.set(key, json[key])

    response = jsonpickle.encode({'response': 'Resort DB initialized.'})
    return Response(response=response, status=200, mimetype='application/json')


# Initialize conditions info database
@app.route("/apiv1/initConditionsDB", methods=['POST'])
def initConditionsDB():
    json = request.get_json()
    resorts = json['resorts']
    appID = json['App ID']
    apiKey = json['API']

    message = {'resorts': resorts,
                          'App ID': appID,
                          'API': apiKey}
    log_debug(f"Creating initial conditions request for worker.")
    sendToWorker(message)

    response = jsonpickle.encode({'response': 'Conditions DB initialized.'})
    return Response(response=response, status=200, mimetype='application/json')

def rank_traffic():
    int_times = {}

    for key in db_traffic.keys():
        val = json.loads(db_traffic[key].replace("'", '"'))
        time = int(val['time']['hours'])*60 + int(val['time']['mins'])
        int_times[key] = time
    
    # sorted_times = {k: v for k, v in sorted(int_times.items(), reverse = True,key=lambda item: item[1])}
    
    # ranked = {k: i for i, k in enumerate(sorted_times.keys())}
    # print('ranked', sorted_times, ranked)

    return int_times

def score_max_temp(max_temp):
    if max_temp <= 0 :
        # You're gonna feel the chill
        return 2
    elif max_temp > 0 and max_temp <= 10:
        return 4
    elif max_temp > 10 and max_temp < 25:
        # The Sweet Spot For Ideal Ski Day Enjoyment
        return 10
    elif (max_temp >= 25 and max_temp <= 40):
        return 6
    else:
        # Over 40F? You're gonna feel the burn.
        return 2


def score_wind_speed(wind_speed):
    if wind_speed < 5:
        return 10
    elif 5 <= wind_speed < 10:
        return 8
    elif 10 <= wind_speed < 15:
        return 6
    elif 15 <= wind_speed < 20:
        return 4
    elif 20 <= wind_speed:
        return 2


# Rank the conditions from the given mapping of resort conditions
def rank_conditions(conditions_map, traffic_map):
    conditions_scoring_dict = dict()
    for key in conditions_map.keys():
        conditions_scoring_dict[key] = 0

    resorts = conditions_map.keys()

    # Build metric dictionaries
    for r in resorts:
        # Snow Inches * 10 (Snow has highest weight value in conditions)
        snow_score = conditions_map[r]['weather']['snow_total_in'] * 10.0

        # Score is from 2 to 10
        max_temp = conditions_map[r]['weather']['temp_max_f']
        max_temp_score = score_max_temp(max_temp)

        # Score is from 2 to 10
        wind_speed = conditions_map[r]['weather']['windspd_max_mph']
        wind_speed_score = score_wind_speed(wind_speed)

        # Score is equivalent to total amount of open terrain
        open_terrain_score = int(conditions_map[r]['resortConditions']['LiftsOpen']) + \
                                  int(conditions_map[r]['resortConditions']['TrailsOpen'])

        mountain_score = snow_score + max_temp_score + wind_speed_score + open_terrain_score
        conditions_scoring_dict[r] = mountain_score

    # Compare Traffic Values (Relative value based on index in list)
    traffic_tuples = sorted(traffic_map.items(), key=lambda kv: kv[1], reverse=True)
    traffic_rank = [resort for resort, traffic_time in traffic_tuples]

    for r in resorts:

        traffic_score = (traffic_rank.index(r) + 1) * 2
        print(r, traffic_score)
        conditions_scoring_dict[r] = conditions_scoring_dict[r] + traffic_score
    print(conditions_scoring_dict)
    # Rank the resorts based on total conditions values
    ranked_tuples = sorted(conditions_scoring_dict.items(), key=lambda kv: kv[1], reverse=True)
    ranked_resorts = [resort for resort, score in ranked_tuples]

    return ranked_resorts


# Provide a ranked list of ski suggestions for the user
@app.route("/apiv1/getSkiSuggestions", methods=['GET', 'POST'])
def getSkiSuggestions():
    request_json = request.get_json()
    appID = request_json['App ID']
    apiKey = request_json['API']

    log_info('Starting API request on /apiv1/getSkiSuggestions')

    conditions = dict()
    resorts_to_update = []
    all_resorts = db_conditions.keys()

    for key in all_resorts:
        db_entry = db_conditions[key]
        print(db_entry)
        cache_value = json.loads(db_conditions[key].replace("'", '"'))
        resort_conditions = cache_value['conditions']
        last_updated_time = cache_value['lastRefreshedTime']
        conditions[key] = resort_conditions

        # Calculate the time difference between when we last updated the cache and now, if > 30 minutes refresh
        current_time = datetime.datetime.now()
        time_difference_minutes = (current_time.timestamp() - last_updated_time) / 60

        if time_difference_minutes > 30:
            resorts_to_update.append(key)

    if resorts_to_update:
        conditions_message = {'resorts': resorts_to_update,
                              'App ID': appID,
                              'API': apiKey}
        log_debug(f"Creating new conditions request for worker.")
        sendToWorker(conditions_message)

    log_debug(f"Evaluating conditions to develop ranking.")

    # TODO: Update to call the actual traffic database - shortest time gets highest score
    traffic_mapping = rank_traffic()

    ranked_conditions = rank_conditions(conditions, traffic_mapping)

    response = jsonpickle.encode({"RankedResults": ranked_conditions})

    log_info('Completed API request for /apiv1/getSkiSuggestions')
    return Response(response=response, status=200, mimetype='application/json')


@app.route("/apiv1/resortConditions/<name>", methods=['GET', 'POST'])
def resortConditions(name):
    request_json = request.get_json()
    appID = request_json['App ID']
    apiKey = request_json['API']

    conditions_cached_response = json.loads(db_conditions[name].replace("'", '"'))

    # Calculate the time difference between when we last updated the cache and now, if > 30 minutes refresh
    last_updated_timestamp = conditions_cached_response['lastRefreshedTime']

    current_time = datetime.datetime.now()
    time_difference_minutes = (current_time.timestamp() - last_updated_timestamp) / 60

    if time_difference_minutes > 30:
        conditions_message = {'resorts': [name],
                              'App ID': appID,
                              'API': apiKey}

        log_debug(f"Creating new conditions request for worker.")
        sendToWorker(conditions_message)

    data_out = conditions_cached_response['conditions']
    response = jsonpickle.encode(data_out)

    return Response(response=response, status=200, mimetype='application/json')

@app.route("/apiv1/traffic", methods=['GET'])
def getResortTraffic():
    json = request.get_json()
    start_location = json['start']
    apiKey = json["API"]

    response = {"start_location": start_location}

    gps_start = db_locations.get(start_location)
    for key in db_locations.keys():
        if key != start_location:
            gps_end = db_locations[key]

            trafficInfo = getTravelInfo({start_location : gps_start.split(',')}, {key : gps_end.split(',')}, API_KEY = apiKey)
            db_traffic.set(key, str(trafficInfo[key]))
            response[key] = trafficInfo[key]['time']

    response = jsonpickle.encode(response)

    return Response(response = response, status=200, mimetype='application/json')

# start flask app
app.run(host="0.0.0.0", port=5000) #host="localhost", port=5000
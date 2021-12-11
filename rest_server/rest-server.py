##
from flask import Flask, request, Response, jsonify

import datetime
import json
import platform
import io, os, sys
import pika, redis
import jsonpickle

# Initialize the Flask application
app = Flask(__name__)

import logging
log = logging.getLogger('werkzeug')
log.setLevel(10) # should be the same as logging.DEBUG

##
## Configure test vs. production
##
redisHost = os.getenv("REDIS_HOST") or "localhost"
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"

print("Connecting to rabbitmq({}) and redis({})".format(rabbitMQHost,redisHost))

##
## Set up redis connections
##
db = redis.Redis(host=redisHost, db=1, decode_responses=True)

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

# Rank the conditions from the given mapping of resort conditions
def rankConditions(conditions_map):
    # TODO: define conditions ranking here
    conditions_scoring_dict = {key: 0 for key in conditions_map.keys}

    # Compare Snowfall


    # Compare Open Terrain


    # Compare Wind Speeds


    # Compare Traffic Times
    # The resort with the highest

    ranked_tuples = sorted(conditions_scoring_dict.items(), key = lambda kv: kv[1])
    ranked_resorts = [resort for resort, score in ranked_tuples]

    return ranked_resorts

# Provide a ranked list of ski suggestions for the user
@app.route("/apiv1/getSkiSuggestions", methods=['GET', 'POST'])
def getSkiSuggestions():
    log.log('Starting API request on /apiv1/getSkiSuggestions', True)

    conditions = []
    for key in db.keys():
        cache_value = json.loads(db[key])
        conditions = cache_value['conditions']
        last_updated_time = cache_value['lastUpdatedTime']
        resort_conditions = {"resort": key, "conditions": conditions}
        conditions.append(resort_conditions)

        # Calculate the time difference between when we last updated the cache and now, if > 30 minutes refresh
        current_time = datetime.datime.now()
        time_difference_minutes = (current_time - last_updated_time).total_seconds() / 60

        if time_difference_minutes > 30:
            conditions_message = {
                'resorts': [key]
            }
            log_debug(f"Creating new conditions request for worker for resort {key}.")
            sendToWorker(conditions_message)

    log_debug(f"Evaluating condtions to develop ranking.")
    ranked_conditions = rankConditions(conditions)

    response = jsonpickle.encode({"RankedResults": ranked_conditions})

    # log.log('GET /apiv1/getSkiSuggestions', True)
    return Response(response=response, status=200, mimetype='application/json')


@app.route("/apiv1/resortConditions/<name>", methods=['GET', 'POST'])
def resortConditions(name):
    # Reading conditions from conditions cache
    # TODO: Define the columns in the conditions cache rows
    #conditions = db[name]
    #open_trails = conditions['trailsOpen']
    open_trails = '14'
    wind = '24W'
    #wind = conditions['wind']
    new_snow = '14"'
    #new_snow = conditions['newSnow']


    response = jsonpickle.encode({
        'resort': name,
        'trailsOpen': open_trails,
        'wind':  wind,
        'new_snow': new_snow})

    return Response(response=response, status=200, mimetype='application/json')

@app.route("/apiv1/traffic", methods=['GET'])
def getResortTraffic():
    json = request.get_json()
    start_location = json['home']
    destination_resort = json['resort']

    # TODO: Get the resort's GPS location from the resort DB
    gps_location = '123.456'

    # TODO: Call Google Maps api
    traffic_time = 10

    response = jsonpickle.encode({
        "start_location": start_location,
        "resort": destination_resort,
        "destination_location": gps_location,
        "traffic_time": traffic_time})

    return Response(response = response, status=200, mimetype='application/json')

# start flask app
app.run(host="0.0.0.0", port=5000) #host="localhost", port=5000
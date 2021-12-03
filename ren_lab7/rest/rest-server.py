##
from flask import Flask, request, Response, jsonify
import platform
import io, os, sys
import pika, redis
import hashlib, requests
import json
import jsonpickle

# Initialize the Flask application
app = Flask(__name__)

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
## Your code goes here..
##

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

#REST methods
@app.route('/', methods = ['GET'])
def hello():
    return '<h1> Sentiment analysis REST Server </h1><p> Please use a valid endpoint.</p>'

@app.route("/apiv1/analyze", methods=['POST'])
def analyze():
    # log.log('Starting API request on /apiv1/analyze', True)
    json = request.get_json()
    sentences = json['sentences']
    model = json['model']

    response = jsonpickle.encode({"action": "queued"})
    for sentence in sentences:
        sentence_dict = {'sentence': sentence, 'model': model}
        sendToWorker(sentence_dict)

    # log.log('POST /apiv1/analyze', True)
    return Response(response = response, status=200, mimetype='application/json')

@app.route("/apiv1/cache/sentiment", methods=['GET'])
def sentiment():
    # only reads from database
    sentences = []
    for key in db.keys():
        out = {"model": "sentiment", "result": str(db[key]).replace('\\', '')}
        sentences.append(out)
        
    # only reads from database

    response = jsonpickle.encode({"model": "sentiment", "sentences": sentences})

    return Response(response = response, status=200, mimetype='application/json')

@app.route("/apiv1/sentence", methods=['GET'])
def sentence():
    json = request.get_json()
    sentences_in = json['sentences']

    sentences_out = []
    for sentence in sentences_in:
        out = {}
        out["analysis"] = {"model": "sentiment", "result": str(db[sentence]).replace('\\', '')}
        out["sentence"] = sentence
        sentences_out.append(out)

    response = jsonpickle.encode({"model": "sentiment", "sentences": sentences_out})

    return Response(response = response, status=200, mimetype='application/json')

# start flask app
app.run(host="0.0.0.0", port=5000) #host="localhost", port=5000
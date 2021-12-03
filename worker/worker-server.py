#
# Worker server
#
import pickle
import platform
import io
import os
import sys
import pika
import redis
import hashlib
import json
import requests
import jsonpickle


from flair.models import TextClassifier
from flair.data import Sentence


hostname = platform.node()

##
## Configure test vs. production
##
redisHost = os.getenv("REDIS_HOST") or "localhost"
rabbitMQHost = os.getenv("RABBITMQ_HOST") or "localhost"

print(f"Connecting to rabbitmq({rabbitMQHost}) and redis({redisHost})")

##
## Set up redis connections
##
db = redis.Redis(host=redisHost, db=1)                                                                           

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


def callback(ch, method, properties, body): # from https://www.rabbitmq.com/tutorials/tutorial-two-python.html
    print(" [x] Received %r" % body.decode())
    # time.sleep(body.count(b'.'))
    # print(" [x] Done")
    ch.basic_ack(delivery_tag=method.delivery_tag)
    sentence_dict = jsonpickle.decode(body)
    print(sentence_dict)

    processMessage(sentence_dict)
    

def processMessage(sentence_dict):

    sentence = Sentence(sentence_dict['sentence']) #input incoming sentence here
    #load tagger
    classifier = TextClassifier.load('sentiment')
    print(sentence)
    classifier.predict(sentence)
    # dont push back to queue; only write to database
    # print("hello there")
    # print(sentence_dict['sentence'])
    # db.set(sentence_dict['sentence'], str(prediction))
    prediction = sentence.to_dict('sentiment')
    print('Prediction: ', prediction)

    # just save to database
    db.set(prediction['text'], str(prediction))


##
## Your code goes here...
##


rabbitMQChannel.basic_consume(queue='toWorker', on_message_callback=callback)
print("Consuming queue...")
rabbitMQChannel.start_consuming()

rabbitMQChannel.stop_consuming()
rabbitMQChannel.close()
rabbitMQChannel.close()
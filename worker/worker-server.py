#
# Worker server
#
from fetch_current_conditions import scrape_resort_conditions_page

import datetime
import jsonpickle
import os
import pika
import platform
import redis
import sys

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
    resort_dict = jsonpickle.decode(body)
    print(resort_dict)

    processMessage(resort_dict)
    

def processMessage(resort_dict):
    resorts_list = resort_dict['resorts']

    for resort in resorts_list:
        try:
            log_debug(f"Fetching conditions for {resort}")
            resort_conditions = scrape_resort_conditions_page(resort)
            current_time = datetime.datetime.now()
            condition_dict = {
                'conditions': resort_conditions,
                'lastRefreshedTime': current_time
            }
            log_debug(f"Resort conditions are: {condition_dict}")
            log_debug(f"Writing conditions to cache for {resort}.")
            db.set(resort, str(condition_dict))
            log_info(f"Successfully fetched conditions for {resort} and updated cache.")
        except Exception as e:
            log_info(f"Exception while trying to process conditions for {resort}: {e}")


rabbitMQChannel.basic_consume(queue='toWorker', on_message_callback=callback)
print("Consuming queue...")
rabbitMQChannel.start_consuming()

rabbitMQChannel.stop_consuming()
rabbitMQChannel.close()
rabbitMQChannel.close()

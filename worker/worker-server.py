#
# Worker server
#
from fetch_current_conditions import scrape_resort_conditions_page, scrape_resort_pages_from_static_html
from weatherUnlockedAPI import getWeatherInfo

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
db_resort = redis.Redis(host=redisHost, db=0, decode_responses=True)
db_conditions = redis.Redis(host=redisHost, db=1, decode_responses=True)

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


# Initialize Resort DB
resort_info = {'Eldora': '39.938086,-105.584282',
 'Steamboat': '40.455464,-106.808369',
 'Copper': '39.498871,-106.139443',
 'Winter Park': '39.886346,-105.761533'
 }

print("Initializing the Resort DB")
for key in resort_info:
    db_resort.set(key, resort_info[key])

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
    

def processMessage(queue_message):
    resorts_list = queue_message['resorts']
    appID = queue_message['App ID']
    apiKey = queue_message['API']

    for resort in resorts_list:
        try:
            log_debug(f"Fetching conditions for {resort}")
            resort_conditions = scrape_resort_pages_from_static_html(resort)

            # Uncomment this line to fetch resort conditions dynamically - currently this does not work in Docker
            # only when running the worker-server.py locally
            #resort_conditions = scrape_resort_conditions_page(resort)

            weather_conditions = getWeatherInfo(db_resort[resort].split(','), appID=appID, APP_KEY=apiKey)
            current_time = datetime.datetime.now().timestamp()
            condition_dict = {
                "conditions": {
                    "resortConditions": resort_conditions,
                    "weather": weather_conditions},
                "lastRefreshedTime": current_time
            }
            log_debug(f"Resort conditions are: {condition_dict}")
            log_debug(f"Weather conditions are: {weather_conditions}")
            log_debug(f"Writing conditions to cache for {resort}.")
            db_conditions.set(resort, str(condition_dict))
            log_info(f"Successfully fetched conditions for {resort} and updated cache.")
        except Exception as e:
            log_info(f"Exception while trying to process conditions for {resort}: {e}")


rabbitMQChannel.basic_consume(queue='toWorker', on_message_callback=callback)
print("Consuming queue...")
rabbitMQChannel.start_consuming()

rabbitMQChannel.stop_consuming()
rabbitMQChannel.close()
rabbitMQChannel.close()

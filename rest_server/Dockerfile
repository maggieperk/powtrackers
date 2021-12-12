FROM python:3.6-slim

RUN  pip3 install pika flask redis requests jsonpickle
EXPOSE 5000
COPY rest-server.py .
COPY googleMapsAPI.py .
COPY weatherUnlockedAPI.py .

ENV PYTHONUNBUFFERED=1
CMD [ "python3", "rest-server.py"]

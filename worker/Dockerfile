FROM python:3.6-slim


RUN  pip3 install pika flask redis requests jsonpickle beautifulsoup4
COPY worker-server.py .

ENV PYTHONUNBUFFERED=1
CMD [ "python3", "worker-server.py"]

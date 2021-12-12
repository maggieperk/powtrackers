FROM python:3.6-slim


RUN  pip3 install pika flask redis requests jsonpickle beautifulsoup4 http-requests requests-html
COPY worker-server.py .
COPY weatherUnlockedAPI.py .
COPY fetch_current_conditions.py .

ENV PYTHONUNBUFFERED=1
CMD [ "python3", "worker-server.py"]

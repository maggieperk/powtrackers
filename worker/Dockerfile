FROM python:3.6-slim



RUN  pip3 install pika flask redis requests jsonpickle beautifulsoup4 requests-html pyppeteer
RUN pyppeteer-install

COPY worker-server.py .
COPY weatherUnlockedAPI.py .
COPY fetch_current_conditions.py .
COPY EldoraConditions.txt .
COPY SteamboatConditions.txt .
COPY CopperConditions.txt .
COPY WinterParkConditions.txt .

ENV PYTHONUNBUFFERED=1
CMD [ "python3", "worker-server.py"]

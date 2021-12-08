FROM dirkcgrunwald/flair:latest

RUN  pip3 install pika flask redis requests jsonpickle beautifulsoup4
COPY worker-server.py .

ENV PYTHONUNBUFFERED=1
CMD [ "python3", "worker-server.py"]

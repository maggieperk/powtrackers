#!/bin/sh
kubectl apply -f redis/redis-deployment.yaml
kubectl apply -f redis/redis-service.yaml
kubectl apply -f rabbitmq/rabbitmq-deployment.yaml
kubectl apply -f rabbitmq/rabbitmq-service.yaml

kubectl apply -f worker/worker-deployment.yaml

kubectl apply -f rest_server/rest-deployment.yaml
kubectl apply -f rest_server/rest-service.yaml

kubectl apply -f rest_server/rest-ingress.yaml

kubectl apply -f logs/logs-deployment.yaml

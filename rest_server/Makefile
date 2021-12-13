VERSION=v11
DOCKERUSER=karenlstengel

build:
	docker build -f Dockerfile -t karenlstengel/powtrackers-rest:latest .
push:
	docker tag powtrackers-rest $(DOCKERUSER)/powtrackers-rest:$(VERSION)
	docker push $(DOCKERUSER)/powtrackers-rest:$(VERSION)
	docker tag powtrackers-rest $(DOCKERUSER)/powtrackers-rest:latest
	docker push $(DOCKERUSER)/powtrackers-rest:latest

VERSION=v11
DOCKERUSER=karenlstengel

build:
	docker build -f Dockerfile -t karenlstengel/powtrackers-worker:latest .
push:
	docker tag powtrackers-worker $(DOCKERUSER)/powtrackers-worker:$(VERSION)
	docker push $(DOCKERUSER)/powtrackers-worker:$(VERSION)
	docker tag powtrackers-worker $(DOCKERUSER)/powtrackers-worker:latest
	docker push $(DOCKERUSER)/powtrackers-worker:latest

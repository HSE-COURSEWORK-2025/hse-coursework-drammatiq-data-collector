#!/bin/bash

export $(cat .env | sed 's/#.*//g' | xargs) || true
docker build -t awesomecosmonaut/data-collection-consumer-app -f Dockerfile.consumer . || true
docker build -t awesomecosmonaut/data-collection-dramatiq-app -f Dockerfile.dramatiq . || true
docker push awesomecosmonaut/data-collection-consumer-app || true
docker push awesomecosmonaut/data-collection-dramatiq-app || true
kubectl delete -f deployment -n hse-coursework-health || true
kubectl apply -f deployment -n hse-coursework-health || true

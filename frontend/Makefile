VERSION := $(shell cat VERSION)
IMAGE_NAME := toilet-frontend

docker-build:
	docker build -t $(IMAGE_NAME):$(VERSION) .

docker-run:
	docker run -p 3000:3000 --rm -it $(IMAGE_NAME):$(VERSION)

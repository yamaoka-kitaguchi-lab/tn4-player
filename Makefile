EE_REPOSITORY=ghcr.io/yamaoka-kitaguchi-lab/tn4-player
EE_TAG=latest

default: build.ee

.PHONY: build.ee
build.ee:
	docker build -t $(EE_REPOSITORY):$(EE_TAG) -f docker.ee/Dockerfile .
	perl -i -pe's!^DOCKER_IMAGE=.*$$!DOCKER_MAGE=$(EE_REPOSITORY):$(EE_TAG)!g' ./bin/tn4.outer

.PHONY: install
install:


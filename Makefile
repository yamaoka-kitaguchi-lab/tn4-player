BASE_EE_REPOSITORY="ghcr.io/yamaoka-kitaguchi-lab/tn4-player/ansible-runner-base"
BASE_EE_TAG="latest"
BASE_EE_IMAGE=$(BASE_EE_REPOSITORY):$(BASE_EE_TAG)

.PHONY: build.ee
build.ee:
	mkdir -p docker.ee
	pipenv update
	pipenv requirements > docker.ee/requirements.txt
	docker build -t $(BASE_EE_IMAGE) - < docker.ee/Dockerfile.base
	pipenv run ansible-builder

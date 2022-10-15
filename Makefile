EE_REPOSITORY="ghcr.io/yamaoka-kitaguchi-lab/tn4-player"
EE_TAG="latest"

.PHONY: build.ee
build.ee:
	docker build -t $(EE_REPOSITORY):$(EE_TAG) - < docker.ee/Dockerfile

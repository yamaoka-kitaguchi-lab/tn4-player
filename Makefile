.PHONY: build.ee
build.ee:
	mkdir -p docker.ee
	pipenv update
	pipenv requirements > docker.ee/requirements.txt
	pipenv run ansible-builder

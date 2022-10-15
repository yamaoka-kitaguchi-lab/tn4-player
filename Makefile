.PHONY: build.ee
build.ee:
	pipenv update
	pipenv requirements > ./docker/requirements.txt
	pipenv run ansible-runner

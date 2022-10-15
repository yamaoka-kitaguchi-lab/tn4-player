.PHONY: build.ee
build.ee:
	pipenv update
	pipenv requirements > requirements.txt
	pipenv run ansible-runner

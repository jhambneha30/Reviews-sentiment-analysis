APP_NAME=review-sentiment-evaluator

.PHONY: req
req:  ## install requirements
	@pip install -r requirements.txt
	python -m spacy download en_core_web_sm

	
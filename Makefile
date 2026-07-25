.PHONY: install doctor test run compare serve

install:
	cd ../harness_core && pip install -e ".[dev]"
	pip install -e ".[dev,harness]"

doctor:
	arena doctor

test:
	pytest -q

run:
	arena run --model models/examples/honest-mock.yaml --circuit demo

compare:
	arena compare models/examples/honest-mock.yaml models/examples/malicious-mock.yaml --circuit demo

serve:
	arena serve --port 8790

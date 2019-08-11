
PYTHONPATH?=$(shell pwd)
ENVPATH?=$(VIRTUAL_ENV)

.PHONY: test

test:
	PYTHONPATH=$(PYTHONPATH) $(ENVPATH)/bin/pytest

test_cov:
	PYTHONPATH=$(PYTHONPATH) $(ENVPATH)/bin/pytest \
		--cov=betmaster_test \
		--cov-report=html \
		--cov-report=term

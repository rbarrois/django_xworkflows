

DJANGO_VERSION ?= 1.9
PYTHON_VERSION := $(shell python --version)
NEXT_DJANGO_VERSION=$(shell python -c "v='$(DJANGO_VERSION)'; parts=v.split('.'); parts[-1]=str(int(parts[-1])+1); print('.'.join(parts))")

default: test

$(info $(PYTHON_VERSION))

install-deps: auto_dev_requirements_django$(DJANGO_VERSION).txt
	pip install --upgrade pip setuptools
	pip install --upgrade -r $<
	pip freeze

auto_dev_requirements_%.txt: dev_requirements_%.txt dev_requirements.txt requirements.txt
	grep --no-filename "^[^#-]" $^ | grep -v "^Django" > $@
	echo "Django>=$(DJANGO_VERSION),<$(NEXT_DJANGO_VERSION)" >> $@

clean:
	rm -f auto_dev_requirements*

test: install-deps
	python setup.py test


coverage: install-deps
	coverage run --branch --include="django_xworkflows/*.py,tests/*.py" setup.py test

coverage-xml-report: coverage
	coverage xml --include="django_xworkflows/*.py,tests/*.py"


.PHONY: clean install-deps test coverage coverage-xml-report

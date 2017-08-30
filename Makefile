PACKAGE=django_xworkflows
TESTS_DIR=tests
DOC_DIR=docs

# Use current python binary instead of system default.
COVERAGE = python $(shell which coverage)
FLAKE8 = flake8
MANAGE_PY = python manage.py
DJANGO_ADMIN = django-admin.py
PO_FILES = $(shell find $(PACKAGE) -name '*.po')
MO_FILES = $(PO_FILES:.po=.mo)

all: default


default: build


# Package management
# ==================


# DOC: Remove temporary or compiled files
clean:
	find . -type f -name '*.pyc' -delete
	find . -type f -path '*/__pycache__/*' -delete
	find . -type d -empty -delete
	rm -f $(MO_FILES)
	@rm -rf tmp_test/

# DOC: Compile files (extensions, message catalogs, etc.)
build: $(MO_FILES)


%.mo: %.po
	cd $(abspath $(dir $<)/../../..) && $(DJANGO_ADMIN) compilemessages

# DOC: Install and/or upgrade dependencies
update:
	pip install --upgrade pip setuptools
	pip install --upgrade -r requirements_dev.txt
	pip freeze


release:
	fullrelease


.PHONY: all default clean build update release


# Tests and quality
# =================


# DOC: Run tests for all supported versions (creates a set of virtualenvs)
testall:
	tox

# DOC: Run tests for the currently installed version
test: build
	PYTHONPATH=. python -Wdefault $(TESTS_DIR)/runner.py



# Note: we run the linter in two runs, because our __init__.py files has specific warnings we want to exclude
# DOC: Perform code quality tasks
lint:
	$(FLAKE8) --config .flake8 --exclude $(PACKAGE)/__init__.py $(PACKAGE)
	$(FLAKE8) --config .flake8 --ignore F401 $(PACKAGE)/__init__.py
	$(FLAKE8) --config .flake8 $(TESTS_DIR)
	check-manifest

coverage:
	$(COVERAGE) erase
	$(COVERAGE) run "--include=$(PACKAGE)/*.py,$(TESTS_DIR)/*.py" --branch setup.py test
	$(COVERAGE) report "--include=$(PACKAGE)/*.py,$(TESTS_DIR)/*.py"
	$(COVERAGE) html "--include=$(PACKAGE)/*.py,$(TESTS_DIR)/*.py"


.PHONY: test testall lint coverage


# Documentation
# =============


# DOC: Compile the documentation
doc:
	$(MAKE) -C $(DOC_DIR) html


# DOC: Show this help message
help:
	@grep -A1 '^# DOC:' Makefile \
	 | awk '    					\
	    BEGIN { FS="\n"; RS="--\n"; opt_len=0; }    \
	    {    					\
		doc=$$1; name=$$2;    			\
		sub("# DOC: ", "", doc);    		\
		sub(":.*", "", name);    		\
		if (length(name) > opt_len) {    	\
		    opt_len = length(name)    		\
		}    					\
		opts[NR] = name;    			\
		docs[name] = doc;    			\
	    }    					\
	    END {    					\
		pat="%-" (opt_len + 4) "s %s\n";    	\
		asort(opts);    			\
		for (i in opts) {    			\
		    opt=opts[i];    			\
		    printf pat, opt, docs[opt]    	\
		}    					\
	    }'


.PHONY: doc help

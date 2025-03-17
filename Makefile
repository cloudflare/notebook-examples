#
# GNU Makefile
#


SHELL := bash -e

PYTHON_CMD := $(shell type -fp python3)
PYTHON_VENV := .venv

NB_SOURCE_DIR := notebooks
NB_EXPORT_DIR := export/html-wasm

INDEX_DIR := $(shell echo '$(NB_EXPORT_DIR)' | cut -d/ -f1)
PAGES_DIR := pages

ifneq ($(wildcard .env),)
	include .env
endif


.PHONY: all
all: venv
	@printf '\n==> Run "make edit" to start a local notebook server.\n'
	@printf '==> Run "make export" to generate the WASM notebooks.\n'

$(PYTHON_VENV): requirements.txt $(PYTHON_CMD)
	$(PYTHON_CMD) -m venv $(PYTHON_VENV)
	$(PYTHON_VENV)/bin/pip install --disable-pip-version-check --upgrade -r requirements.txt
	@touch $(PYTHON_VENV)
	@printf "\n==> A self-contained python environment has been created with all the required dependencies.\n"
	@printf "==> To activate that environment and start the notebooks server, run the following commands:\n"
	@printf "\n\tsource $(PYTHON_VENV)/bin/activate\n\tmake edit\n\n"

node_modules: package.json
	npm install
	touch node_modules

.PHONY: venv
venv: $(PYTHON_VENV)

.PHONY: lint
lint: $(PYTHON_VENV) node_modules
	$(PYTHON_VENV)/bin/flake8 $(NB_SOURCE_DIR) $(PAGES_DIR)
	npm run lint

# Skip any python source code that doesn't appear to be a notebook...
$(NB_EXPORT_DIR)/%.html: $(NB_SOURCE_DIR)/%.py $(PYTHON_VENV) $(shell find $(NB_SOURCE_DIR)/public -type f)
	@if $(PYTHON_VENV)/bin/python -c 'import sys, $(NB_SOURCE_DIR).$(basename $(notdir $<)) as m; sys.exit(0 if hasattr(m, "__generated_with") else 1)' ; then \
		echo "$<: $@" ; \
		$(PYTHON_VENV)/bin/marimo -q export html-wasm "$<" -o "$@" --mode edit ; \
	fi

$(INDEX_DIR)/index.html: notebooks.yaml $(PAGES_DIR)/index.py $(shell find $(PAGES_DIR)/template -type f) $(patsubst $(NB_SOURCE_DIR)/%.py,$(NB_EXPORT_DIR)/%.html,$(wildcard $(NB_SOURCE_DIR)/*.py))
	$(PYTHON_VENV)/bin/python $(PAGES_DIR)/index.py --lint $(NB_EXPORT_DIR) $(INDEX_DIR)

$(INDEX_DIR)/_redirects: $(PAGES_DIR)/_redirects
	mkdir -p $(shell dirname "$@")
	cp $(PAGES_DIR)/_redirects $@

.PHONY: html-wasm
html-wasm: lint $(INDEX_DIR)/_redirects $(patsubst $(NB_SOURCE_DIR)/%.py,$(NB_EXPORT_DIR)/%.html,$(wildcard $(NB_SOURCE_DIR)/*.py)) $(INDEX_DIR)/index.html

.PHONY: export
export: html-wasm
	@printf '\n==> To see the exported notebooks, run the following command and open the displayed URL in your browser:\n'
	@printf '\n\tmake preview\n\n'

.PHONY: preview
preview: html-wasm
	npm run preview

.PHONY: edit
edit: $(PYTHON_VENV)
	cd notebooks && ../$(PYTHON_VENV)/bin/marimo edit --skip-update-check --port 8088

deploy: node_modules lint export
	npm run deploy

.PHONY: clean
clean:
	find . -name '*~' -type f -delete
	find . -name '*.pyc' -type f -delete
	find . -name '__pycache__' -type d -delete
	rm -rf "$(NB_EXPORT_DIR)" "$(INDEX_DIR)" node_modules

.PHONY: distclean
distclean: clean
	rm -rf "$(PYTHON_VENV)"


# EOF - Makefile

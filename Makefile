SHELL := /bin/bash

DOCKER_NAMESPACE=lorenzetti
SETUP_SCRIPT=../core/GaugiKernel/cmake/lzt_setup.sh

all:  build_sources

build_sources:
	mkdir -p build
	cd build && cmake .. && make -j${nproc} && cp ${SETUP_SCRIPT} . && cd ..

test:
	source .github/workflows/tests/test_local.sh tests

.PHONY: all build_sources test docs doc_clean doc_venv_clean

VENV_DOC = doc/venv_doc

docs:
	@if [ ! -d "$(VENV_DOC)" ]; then \
		echo "Creating virtual environment for documentation..."; \
		virtualenv -p python $(VENV_DOC); \
		$(VENV_DOC)/bin/python -m pip install -r doc/requirements_doc.txt --no-cache-dir; \
	fi
	mkdir -p doc/doxygen/xml doc/source/api doc/source/cxx doc/source/tutorials && \
	cp notebooks/*.ipynb doc/source/tutorials/ && \
	printf "Python API\n==========\n\n.. toctree::\n   :maxdepth: 2\n\n   modules\n" > doc/source/api/index.rst && \
	printf "C++ API\n=======\n\n.. toctree::\n   :maxdepth: 2\n\n   core\n   events\n   generator\n   geometry\n   reconstruction\n" > doc/source/cxx/index.rst && \
	cd doc && doxygen Doxyfile && cd .. && \
	$(VENV_DOC)/bin/python doc/setup_doc_env.py && \
	$(VENV_DOC)/bin/python -m sphinx.ext.apidoc -o doc/source/api doc/mock_site_packages -f && \
	$(VENV_DOC)/bin/python doc/generate_cxx_rst.py && \
	$(VENV_DOC)/bin/python -m sphinx.cmd.build -E -b html doc/source doc/build/html

doc_clean:
	rm -rf doc/build doc/doxygen doc/source/api doc/source/cxx doc/source/tutorials doc/mock_site_packages
	rm -rf $(VENV_DOC)



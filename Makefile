
.PHONY: init
init:
	git submodule init
	git submodule update

.PHONY: format
format:
	black -l 79 --py36 tartiflette setup.py examples/aiohttp/starwars

.PHONY: check-format
check-format:
	black -l 79 --py36 --check tartiflette setup.py

.PHONY: style
style: check-format
	pylint tartiflette --rcfile=pylintrc

.PHONY: complexity
complexity:
	xenon --max-absolute B --max-modules B --max-average A tartiflette

.PHONY: test-integration
test-integration:
	true

.PHONY: test-unit
test-unit:
	mkdir -p reports
	py.test -s tests/unit --junitxml=reports/report_unit_tests.xml --cov . --cov-config .coveragerc --cov-report term-missing --cov-report xml:reports/coverage_func.xml

.PHONY: test-functional
test-functional:
	mkdir -p reports
	py.test -s tests/functional --junitxml=reports/report_func_tests.xml --cov . --cov-config .coveragerc --cov-report term-missing --cov-report xml:reports/coverage_unit.xml

.PHONY: test
test: test-integration test-unit test-functional

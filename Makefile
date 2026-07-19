.PHONY: validate validate-runtime validate-all

validate:
	python3 scripts/validate_project.py

validate-runtime:
	python3 scripts/validate_lark_runtime.py

validate-all: validate validate-runtime

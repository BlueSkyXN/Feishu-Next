.PHONY: validate validate-governance validate-privacy validate-privacy-history validate-runtime validate-mcp validate-all

validate: validate-privacy
	python3 scripts/validate_project.py
	python3 -m unittest discover -s scripts/tests -v

validate-governance:
	python3 -m unittest discover -s scripts/tests -v

validate-privacy:
	python3 scripts/validate_privacy.py

validate-privacy-history:
	python3 scripts/validate_privacy.py --history

validate-runtime:
	python3 scripts/validate_lark_runtime.py

validate-mcp:
	cd cli-mcp-server && npm run check && npm run contract && npm run smoke && npm run smoke:mcp && npm run smoke:streamable && npm run smoke:scheduler && npm run smoke:auth && npm run smoke:transport

validate-all: validate validate-runtime validate-mcp

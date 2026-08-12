.PHONY: validate validate-runtime validate-mcp validate-all

validate:
	python3 scripts/validate_project.py

validate-runtime:
	python3 scripts/validate_lark_runtime.py

validate-mcp:
	cd cli-mcp-server && npm run check && npm run contract && npm run smoke && npm run smoke:mcp && npm run smoke:streamable && npm run smoke:scheduler && npm run smoke:auth && npm run smoke:transport

validate-all: validate validate-runtime validate-mcp

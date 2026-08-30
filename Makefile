.PHONY: verify manifest robustness reproduce all

verify:
	uv run python scripts/verify_repository.py
	uv run python scripts/verify_neurips26.py

manifest:
	uv run python scripts/process/build_r1_paper_manifest.py

robustness:
	uv run python scripts/analyse/run_neurips26_robustness.py

reproduce:
	uv run python scripts/reproduce_release.py

all: manifest robustness verify

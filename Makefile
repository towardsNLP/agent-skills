.PHONY: test lint sync-tools

# Prefer the active pyenv interpreter when one exists. Homebrew's system Python on macOS may not
# carry the development dependencies even when the selected project interpreter does. Callers can
# still override this with `make test PYTHON=/path/to/python`.
PYTHON ?= $(shell pyenv which python3 2>/dev/null || command -v python3)

test:
	"$(PYTHON)" -m pytest tests/ -q

# The status script is vendored into repos with stricter linters than this one has.
# Keeping it clean here is cheaper than exempting it in every host.
# Core correctness plus formatting, at the line length the hosts use. Deliberately
# NOT ruff's full default set: a host repo pins its own ruff and its own select list,
# and chasing whichever preview rules this machine's ruff happens to enable produces
# churn that no host asked for. The gate that matters is the host's.
lint:
	ruff check tools/ session/start-session/scripts/ tests/ --select E,F,W,I --line-length 100
	ruff format --check tools/ session/start-session/scripts/ tests/ --line-length 100

# Copy the status script into a project that vendors it. The project's CI should
# diff its copy against this source; a silent fork is how one repo ends up
# trusting a check the others have already fixed.
#   make sync-tools TO=../some-project
sync-tools:
	@test -n "$(TO)" || { echo "usage: make sync-tools TO=<project root>"; exit 2; }
	mkdir -p "$(TO)/tools"
	cp tools/ticket_status.py "$(TO)/tools/ticket_status.py"
	@echo "copied to $(TO)/tools/ticket_status.py"

.PHONY: test lint sync-tools

test:
	python3 -m pytest tests/ -q

# The status script is vendored into repos with stricter linters than this one has.
# Keeping it clean here is cheaper than exempting it in every host.
lint:
	ruff check tools/ tests/ --line-length 100
	ruff format --check tools/ tests/ --line-length 100

# Copy the status script into a project that vendors it. The project's CI should
# diff its copy against this source; a silent fork is how one repo ends up
# trusting a check the others have already fixed.
#   make sync-tools TO=../some-project
sync-tools:
	@test -n "$(TO)" || { echo "usage: make sync-tools TO=<project root>"; exit 2; }
	mkdir -p "$(TO)/tools"
	cp tools/ticket_status.py "$(TO)/tools/ticket_status.py"
	@echo "copied to $(TO)/tools/ticket_status.py"

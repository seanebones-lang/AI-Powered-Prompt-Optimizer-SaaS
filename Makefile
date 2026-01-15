.PHONY: setup start deploy logs restart open test lint

# Local development
setup:
	@chmod +x setup_local.sh && ./setup_local.sh

start:
	@chmod +x start.sh && ./start.sh

# Deployment
deploy:
	@chmod +x deploy.sh && ./deploy.sh

logs:
	@railway logs

restart:
	@railway restart

open:
	@railway open

# Testing
test:
	@TESTING=1 pytest tests/ -v

# Linting
lint:
	@ruff check . --fix && ruff format .
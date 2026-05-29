APP_NAME := clam
DIST_DIR := dist
OUTPUT := $(DIST_DIR)/$(APP_NAME)
INSTALL_DIR := $(HOME)/.local/bin

.PHONY: all build install uninstall clean run check

all: build install

check:
	@command -v uv run nuitka >/dev/null 2>&1 || { \
		echo "Error: nuitka not found"; \
		exit 1; \
	}

build: check
	uv run nuitka \
		--mode=onefile \
		--output-dir=$(DIST_DIR) \
		--output-filename=$(APP_NAME) \
		--python-flag=isolated \
		--include-package=orjson \
		--include-package=platformdirs \
		--include-package=typer \
		--include-package=rich \
		--include-package-data=typer \
		--include-package-data=rich \
		src/main.py

install:
	@if [ ! -f "$(OUTPUT)" ]; then \
		echo "Error: $(OUTPUT) does not exist."; \
		echo "Run 'make build' first."; \
		exit 1; \
	fi

	install -Dm755 $(OUTPUT) $(INSTALL_DIR)/$(APP_NAME)

uninstall:
	rm -f $(INSTALL_DIR)/(APP_NAME)

clean:
	rm -rf build
	rm -rf $(DIST_DIR)
	rm -rf *.build
	rm -rf *.dist
	rm -rf *.onefile-build

.PHONY: compile compile-no-console

# PyInstaller executable path
PYINSTALLER = ./venv/Scripts/pyinstaller

# Path to Python site-packages
SITE_PACKAGES = ./venv/Lib/site-packages

# Output directory
DISTPATH = ./out

# Name of the output executable
EXECUTABLE_NAME = img2pdf.exe

# Main Python script
SCRIPT = main.py

# Common PyInstaller flags
COMMON_FLAGS = --onefile --paths $(SITE_PACKAGES) --name $(EXECUTABLE_NAME) --distpath $(DISTPATH)

compile:
	$(PYINSTALLER) $(COMMON_FLAGS) --noconsole $(SCRIPT)

compile-with-console:
	$(PYINSTALLER) $(COMMON_FLAGS) $(SCRIPT)

compile-no-venv:
	pip install -r requirements.txt
	pyinstaller $(COMMON_FLAGS) --noconsole $(SCRIPT)
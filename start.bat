@echo off
SET VENV_DIR=.env

:: Check if the virtual environment exists
IF NOT EXIST "%VENV_DIR%\Scripts\activate" (
    echo Virtual environment not found. Creating environment...
    python -m venv %VENV_DIR%
)

:: Activate the virtual environment
echo Activating virtual environment...
call %VENV_DIR%\Scripts\activate

:: Check if the necessary modules are installed
echo Installing required modules from requirements.txt...
pip install -r requirements.txt

:: Run the Python script in headless mode
echo Running the Python script in headless mode...
python main.py --headless

:: If an error occurs, pause the system so you can view the output
IF %ERRORLEVEL% NEQ 0 (
    echo An error occurred. Press any key to continue...
    pause
)

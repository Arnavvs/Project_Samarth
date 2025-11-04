@echo off
echo [1/5] Checking for Python and creating virtual environment (venv)...
python -m venv venv

echo [2/5] Activating virtual environment...
call venv\Scripts\activate

echo [3/5] Installing required packages from requirements.txt...
pip install -r requirements.txt

echo [4/5] Building the database (running db_creator.py)...
python db_creator.py

echo [5/5] Launching the Streamlit app (app.py)...
echo Your app will now open in your web browser.
streamlit run app.py

@echo off
echo This window will close when you stop the Streamlit server (Ctrl+C).
pause
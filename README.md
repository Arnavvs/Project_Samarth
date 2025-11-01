roject Samart: Agricultural & Climate Q&A Agent

Project Samart is a Q&A system for India's agricultural economy and climate patterns. You can ask complex questions in natural language (e.g., "What was the total rice production in West Bengal in 2014?") and get answers synthesized from multiple government datasets.

The project works by first processing raw data from data.gov.in into a clean, local SQL database. Then, a Streamlit web app uses a LangChain and Google Gemini agent (agent.py) to understand your question, write its own SQL queries, and give you a final answer.

Tech Stack

Frontend: Streamlit

AI Agent: LangChain, Google Gemini

Data Processing: pandas

Database: SQLite

How to Run This Project (Step-by-Step)

Follow these steps exactly to get the project running on your local machine.

Prerequisites

Python 3.8+

Git

Step 1: Clone the Repository



Step 2: Set Up Python Environment & Install Dependencies

It's highly recommended to use a virtual environment to avoid conflicts.

# Create a virtual environment
python -m venv venv

# Activate it (Windows)
.\venv\Scripts\activate

# Activate it (macOS/Linux)
source venv/bin/activate

# Install all required packages
pip install -r requirements.txt


Step 3: Set Up Your Google API Key

The AI agent needs a Google API Key to function.

Create a new file in the project's root directory named .env

Open this file and add your API key like this:

GOOGLE_API_KEY="your-actual-api-key-goes-here"


Step 4: Build the Database (The Important Part!)

This project does not work without its database. The db_creator.py script will read the raw_crop_data.csv and raw_rainfall_data.csv files, clean them, and create the final data.gov.db file.

Run this command from your terminal:

python db_creator.py


You should see output telling you it's processing the files and then:
--- DATABASE BUILD COMPLETE ---

Step 5: Run the Streamlit Web App

Now that your environment is set up and your database is built, you can start the application.

streamlit run app.py


This will open the Project Samart Q&A interface in your web browser, ready for your questions!

Project File Structure

Here's a quick guide to what each file does:

app.py: The main Streamlit web application you interact with.

agent.py: The "brain" of the app. It defines the LangChain SQL Agent powered by Gemini that answers your questions.

requirements.txt: The list of all Python packages needed for the project.

Data Pipeline Files:

db_creator.py: (Setup Script) This is the most important setup file. It reads the raw CSVs, cleans them, and builds the final data.gov.db.

raw_crop_data.csv: Raw data on crop production.

raw_rainfall_data.csv: Raw data on rainfall.

crop_data.py & rainfall.py: (Optional) These are the scripts used to fetch the raw CSV data from data.gov.in. You do not need to run them unless you want to refresh the raw data.

Utility Files:

verification.py: A helper script you can run (python verification.py) to check the database and see the year ranges for your data.

New Text Document.txt: This file appears to be empty or a reference note. It is not used by the application and can be safely deleted.

IMPORTANT: How to use .gitignore

As we discussed, you should never upload your database file, your secrets file, or your environment folder to GitHub.

Create a file named .gitignore in the root of your project and paste the following into it. This will tell Git to ignore these files.

# Python virtual environment
venv/
.venv/
__pycache__/

# Secrets file
.env
*.env

# Generated Database
# This is the file created by db_creator.py
data.gov.db
*.db
*.sqlite
*.sqlite3

# OS-specific files
.DS_Store
Thumbs.db

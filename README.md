# Project Samart: Agricultural & Climate Q&A Agent

Project Samart is a Q&A system for India's agricultural economy and climate patterns. You can ask complex questions in natural language (e.g., "What was the total rice production in West Bengal in 2014?") and get answers synthesized from multiple government datasets.

The project works by processing raw data into a local SQL database, which a Streamlit web app queries using a LangChain and Google Gemini agent.

## 🚀 How to Run

### Prerequisites
* Python 3.8+
* Git
* A Google API Key (for the Gemini agent)

### Step-by-Step Instructions

1.  **Clone the Repository**
    ```bash
    # Clone the project to your local machine
      git clone https://github.com/Arnavvs/Project_Samarth.git
      cd Project_Samarth

    ```

2.  **Unzip the Raw Data**
    
    This project requires raw CSV files to build its database.
    * Find the `data.zip` file.
    * Unzip it in the main project folder.
    * You should now have `raw_crop_data.csv` and `raw_rainfall_data.csv` in your directory.

3.  **Click on run.bat**
    

4.  **Set Up Your Google API Key from Google AI STUDIO**
    

5.  **Build the Database**
    
    This is a critical step. The script reads the raw CSVs, cleans them, and creates the `data.gov.db` file the agent needs.
    ```bash
    python db_creator.py
    ```
    You should see output ending in `--- DATABASE BUILD COMPLETE ---`.

6.  **Run the Streamlit Web App**
    ```bash
    streamlit run app.py
    ```
    This will open the Project Samart Q&A interface in your web browser.

## 🛠️ Tech Stack

* **Frontend:** Streamlit
* **AI Agent:** LangChain, Google Gemini
* **Data Processing:** pandas
* **Database:** SQLite

## 📁 Project File Structure

* `app.py`: The main Streamlit web application.
* `agent.py`: Defines the LangChain SQL Agent (the "brain").
* `db_creator.py`: **(Setup Script)** Reads CSVs and builds the final `data.gov.db`.
* `data.zip`: Contains the raw data files.
    * `raw_crop_data.csv`: Raw data on crop production.
    * `raw_rainfall_data.csv`: Raw data on rainfall.
* `requirements.txt`: The list of all Python packages needed.
* `crop_data.py` / `rainfall.py`: (Optional) Scripts used to fetch the raw data from data.gov.in.

## 🔒 .gitignore

To keep your secrets and large files out of Git, create a `.gitignore` file with the following content:

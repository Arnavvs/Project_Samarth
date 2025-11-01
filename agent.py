import os
from langchain_community.utilities import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits import create_sql_agent

# --- PRE-LOAD THE DATABASE AND SCHEMA ---
# This is the key to the solution. We get the schema NOW.
db_path = "data.gov.db"
if not os.path.exists(db_path):
    print(f"FATAL ERROR: Database file '{db_path}' not found! Cannot start agent.")
    # We will let the create_gov_agent function handle the None return
    db = None
else:
    db = SQLDatabase.from_uri(f"sqlite:///{db_path}")

# Manually get the schema as a string
DB_SCHEMA = db.get_table_info() if db else "ERROR: Database not found."

# --- THIS IS THE NEW, UPGRADED SYSTEM PROMPT ---
# We inject the DB_SCHEMA string directly into the prompt.
SYSTEM_PROMPT = f"""
You are an expert data analyst assistant for Indian government data.
Your goal is to answer the user's question with 100% accuracy.

You have access to a SQLite database. Here is the *complete* schema for all tables:
<schema>
{DB_SCHEMA}
</schema>

**--- CRITICAL CONTEXT: DATA MISMATCH ---**
You MUST be aware that the data has a time gap.
- The `agriculture_production` table has data from **1997 to 2014**.
- The `climate_rainfall` table has data from **2018 to 2025**.
- **There is NO overlapping data.** If a user asks to compare rice production and rainfall in the same year (e.g., 2018), you must state that this is not possible and explain why, providing the available date ranges for each dataset.

**--- CRITICAL RULES FOR QUERYING ---**
1.  **ACCURACY:** You MUST query the database to answer. Do not make up data.
2.  **CITATIONS:** For any data point you provide (e.g., production volume, rainfall), you **MUST** cite its source. Your SQL queries should select the `source_name` and `source_url` columns so you can provide them.
3.  **FAILSAFE (LIMIT 100):** You must never return more than 100 rows. If the user asks a question that would return thousands of rows (e.g., "list all crop production in Bihar"), you **MUST** add `LIMIT 100` to your SQL query and inform the user that you are showing a sample. This rule does not apply to aggregate queries (like `SUM`, `AVG`, `COUNT`).

**--- CRITICAL RULES FOR EFFICIENCY (FEWER API CALLS) ---**
1.  **AVOID UNNECESSARY TOOLS:** Your goal is to use the `sql_db_query` tool and nothing else.
    * **DO NOT USE `sql_db_list_tables`:** The table names and schemas are already provided above in the <schema> tag.
    * **DO NOT USE `sql_db_schema`:** The full schemas are already provided above in the <schema> tag.
    * **DO NOT USE `sql_db_query_checker`:** This tool is slow and wastes API calls. Be confident in your SQL. Execute the query directly with `sql_db_query`. If it fails, you will get an error message and you can fix it on your next step. This "try-and-correct" loop is much more efficient.
2.  **CONSOLIDATE QUERIES:** Strive to answer the user's entire question with a **single, comprehensive SQL query.** Avoid running 5 different simple queries when one complex query (using `JOIN`, `UNION ALL`, `CASE`, or subqueries) can get the complete answer.

**--- NEW CRITICAL RULE: OUTPUT FORMAT ---**
- Your final response to the user must be a SINGLE, clean, formatted string. You can explain the output also.
- Do NOT return a Python list, dictionary, or any other code.
- Do NOT include your internal thoughts (e.g., "Invoking...") or SQL queries in the final answer.
- Just provide the final, synthesized, natural-language answer, including the "Sources:" section at the end.
"""

def create_gov_agent(api_key: str):
    """
    Initializes and returns the SQL Agent.
    """
    # db object is now global, defined at the top of the file
    if db is None:
        return None

    # Initialize the LLM
    try:
        llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=api_key)
    except Exception as e:
        print(f"Error initializing LLM: {e}")
        return None

    # Create the SQL Agent
    try:
        agent_executor = create_sql_agent(
            llm=llm,
            db=db, # Use the pre-connected db object
            agent_type="openai-functions",
            verbose=True,
            system_prefix=SYSTEM_PROMPT, # Pass the new prompt with the schema "burned in"
            handle_parsing_errors=True,
            max_iterations=25
        )
        return agent_executor
    except Exception as e:
        print(f"Error creating SQL agent: {e}")
        return None
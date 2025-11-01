import streamlit as st
import os
import sqlite3
import logging
import json
from sqlalchemy import create_engine
from langchain_community.utilities.sql_database import SQLDatabase
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.agent_toolkits import create_sql_agent

# --- 1. Configuration ---

# Set up basic logging
logging.basicConfig(level=logging.INFO)
log = logging.getLogger(__name__)

# --- Database Configuration ---
DB_FILE = "data.gov.db"
DB_URI = f"sqlite:///{DB_FILE}"

# --- Agent Prompt Engineering ---
# This is the "brain" of the agent. We give it context about the schema
# and explicitly tell it to follow the "Traceability" rule.
AGENT_PREFIX = """
You are an expert Q&A system for Project Samarth, specialized in India's agricultural economy and climate patterns.
Your job is to answer questions by querying a SQLite database and reasoning intelligently even when data is inconsistent, incomplete, or non-overlapping.

Always use valid SQLite syntax.

--- DATABASE SCHEMA ---
You have access to two tables:

1. `agriculture_production`: Contains data on crop production.
   - Key Columns:
     - `state` (string)
     - `district` (string)
     - `year` (integer)
     - `season` (string)
     - `crop` (string)
     - `area_hectares` (float)
     - `production_tonnes` (float)
     - `source_name` (string)
     - `source_url` (string)
   - Data available from 1997 to 2015.

2. `climate_rainfall`: Contains data on annual rainfall.
   - Key Columns:
     - `state` (string)
     - `district` (string)
     - `year` (integer)
     - `annual_rainfall_mm` (float)
     - `source_name` (string)
     - `source_url` (string)
   - Data available from 2018 to 2025.

--- DATA LIMITATIONS & FLEXIBLE REASONING ---
1. Non-overlapping years are common between the two tables. If years do not align, use trends, averages, or logical inference to make the best possible connection.
2. If exact data is missing, approximate using nearest available years, similar states, or historical patterns — but always make it clear what you’re inferring.
3. Never refuse to answer. Always aim to give a “best-effort” explanation, even if you have to reason or extrapolate.
4. When summarizing or approximating, mention your reasoning briefly in the answer.

--- CORE VALUES ---
- **Accuracy**: Use correct numbers and relationships from available data.
- **Transparency**: Clearly explain data gaps or assumptions.
- **Traceability**: Always cite at least one `source_url` from your SQL results.
- **Reasoned Flexibility**: You may interpolate, compare, or reason about trends when direct correlation isn’t possible.

--- QUERY EXECUTION ---
CRITICAL: The database schema and data limitations are fully defined above. You MUST NOT use the `sql_db_list_tables` or `sql_db_schema` tools. You MUST proceed directly to constructing a query using the `sql_db_query` tool.

- Always use valid SQLite queries.
- You may run multiple queries if necessary.
- Focus on extracting the most relevant data even if imperfect.
- It’s fine to summarize or compute averages or trends accross years from available rows.

--- FINAL ANSWER FORMAT ---
Your output must be a single valid JSON object with:
1. "answer": A natural language explanation with reasoning, trends, and context.
2. "sources": A list of all unique dataset URLs used in your answer.

The answer must include any assumptions made and always cite the source(s).

Example of a good output:
{{
  "answer": "Direct correlation between rainfall and rice production for 2010 cannot be made, as rainfall data is available only from 2018 onwards. However, based on average rainfall trends (2018–2020) and historical production (2010–2015), it’s likely that rainfall remained sufficient for consistent rice yield. (Sources: https://data.gov.in/resource/abc123)",
  "sources": ["https://data.gov.in/resource/abc123"]
}}
"""


# --- 2. Helper Functions ---

@st.cache_resource
def get_db_engine():
    """Creates a cacheable SQLAlchemy engine."""
    log.info(f"Creating SQLAlchemy engine for {DB_URI}")
    return create_engine(DB_URI)

@st.cache_resource
def get_sql_database_tool(_engine):
    """Creates a cacheable LangChain SQLDatabase object."""
    log.info("Creating LangChain SQLDatabase tool")
    # We explicitly tell it which tables to use, just in case.
    return SQLDatabase(
        _engine,
        include_tables=['agriculture_production', 'climate_rainfall']
    )

@st.cache_resource
def get_llm(_api_key):
    """Creates a cacheable Google Gemini LLM instance."""
    log.info("Initializing Google Gemini LLM (gemini-2.5-flash)")
    return ChatGoogleGenerativeAI(
        model="gemini-2.5-flash",
        google_api_key=_api_key,
        temperature=0,  # Set to 0 for factual, deterministic answers
    )

# --- THIS FUNCTION IS NO LONGER CACHED ---
# This is the key to fixing the "stuck agent" bug.
def get_sql_agent(_llm, _db_tool):
    """Creates a SQL Agent Executor."""
    log.info("Creating LangChain SQL Agent Executor")
    return create_sql_agent(
        llm=_llm,
        db=_db_tool,
        agent_type="openai-tools",  # This type works well with Gemini
        verbose=True,  # This logs the agent's thoughts/queries to the console
        prefix=AGENT_PREFIX,
        handle_parsing_errors=True,
        max_iterations=30
    )

# --- 3. Streamlit UI Application ---

def main():
    st.set_page_config(page_title="Project Samarth Q&A", layout="wide")
    st.title("🇮🇳 Project Samarth: Agriculture & Climate Q&A")

    # --- Sidebar for API Key and Info ---
    with st.sidebar:
        st.header("Configuration")
        google_api_key = st.text_input(
            "Enter your Google API Key:", type="password"
        )
        st.markdown("---")
        st.subheader("How to Use")
        st.info(
            f"1. Make sure the database file `{DB_FILE}` is in the same directory.\n"
            f"2. If not, run `python db_creator.py` first.\n"
            "3. Enter your Google API Key.\n"
            "4. Ask a question!"
        )
        st.markdown("---")
        st.subheader("Sample Questions")
        st.markdown(
            """
            - "Compare the total annual rainfall in 'Uttar Pradesh' and 'Maharashtra' for the last 3 available years."
            - "What were the top 5 most produced crops in 'Punjab' in 2013? Cite your sources."
            - "Analyze the production trend of 'Rice' in the 'ANDAMAN AND NICOBAR ISLANDS' from 2000 to 2005."
            - "(This will now give a 'best effort' answer) Correlate Rice production and rainfall in 2010."
            """
        )

    # --- Main Chat Interface ---

    # Check for prerequisites
    if not os.path.exists(DB_FILE):
        st.error(
            f"Database file '{DB_FILE}' not found. "
            f"Please run `python db_creator.py` (from Phase 1) to create it."
        )
        st.stop()

    if not google_api_key:
        st.info("Please enter your Google API Key in the sidebar to begin.")
        st.stop()

    # --- Initialize CACHED components (LLM and DB) ---
    try:
        engine = get_db_engine()
        db_tool = get_sql_database_tool(engine)
        llm = get_llm(google_api_key)
        # --- AGENT IS NO LONGER CREATED HERE ---
    except Exception as e:
        st.error(f"Failed to initialize components. Error: {e}")
        st.stop()

    # Initialize chat history in session state
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Display past messages
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Handle new chat input
    if prompt := st.chat_input("Ask a question about agriculture and climate..."):
        # Add user message to history and display it
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get AI response
        with st.chat_message("assistant"):
            with st.spinner("Thinking and querying live data..."):
                try:
                    # --- AGENT IS CREATED FRESH *INSIDE* THE LOOP ---
                    # This ensures we get a "new worker" for every query.
                    agent_executor = get_sql_agent(llm, db_tool)
                    
                    # Run the agent
                    response = agent_executor.invoke({"input": prompt})
                    
                    # --- FIX for fragmented/list output ---
                    agent_output = response.get("output")
                    output_str = ""

                    if isinstance(agent_output, list):
                        parts = []
                        for part in agent_output:
                            if isinstance(part, dict) and 'text' in part:
                                parts.append(part.get('text', ''))
                            elif isinstance(part, str):
                                parts.append(part)
                        output_str = "".join(parts)
                    elif isinstance(agent_output, str):
                        output_str = agent_output
                    else:
                        log.warning(f"Unexpected agent output structure: {agent_output}")
                        output_str = str(agent_output)
                    # --- END OF FIX ---
                    
                    final_answer = ""
                    sources = []

                    # Try to parse the JSON output from the agent
                    try:
                        json_start = output_str.find('{')
                        json_end = output_str.rfind('}') + 1
                        
                        if json_start != -1 and json_end != -1:
                            clean_json_str = output_str[json_start:json_end]
                            data = json.loads(clean_json_str)
                            final_answer = data.get("answer", "Sorry, I couldn't find an answer in the expected format.")
                            sources = data.get("sources", [])
                        else:
                            log.error(f"Could not find JSON block in output: {output_str}")
                            final_answer = f"Error: Agent returned invalid/incomplete JSON. (Raw response: {output_str})"
                    
                    except json.JSONDecodeError as json_err:
                        log.error(f"Failed to decode JSON. Error: {json_err}. Raw output: {output_str}")
                        final_answer = output_str # Just display the raw, unparsed output
                        sources = []

                    # Display the formatted answer
                    st.markdown(final_answer)
                    
                    # Display the sources separately
                    if sources:
                        st.markdown("---")
                        st.subheader("Data Sources")
                        for source in sources:
                            st.write(f"- {source}")
                    
                    # Add AI response to history
                    st.session_state.messages.append(
                        {"role": "assistant", "content": final_answer}
                    )

                except Exception as e:
                    log.error(f"Error during agent invocation: {e}")
                    error_message = f"An error occurred: {e}. Please check your query or API key."
                    st.error(error_message)
                    st.session_state.messages.append(
                        {"role": "assistant", "content": error_message}
                    )
                    

if __name__ == "__main__":
    main()
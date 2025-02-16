# Master's Program Recommendation System

## Overview

This project is a master's program recommendation system built using Flask APIs and an integrated chatbot agent. The system leverages OpenAI's GPT models along with several filtering chains (academic, language, general, GMAT/GRE, QS ranking) to provide tailored program recommendations. The project is organized into two main parts:

- **Backend**: Contains all the server-side logic, including:
  - **app_final**: Contains the backend API, recommendation logic, database connections, and configuration loading.
  - **chatbot_agent**: Contains the multi-tool chatbot agent and its supporting tools.
- **Frontend**: Contains the HTML, CSS, and JavaScript files for the user interface (located under the `templates/` and `static/` directories).
## Directory Structure

Below is an example of the project directory structure:
Please find `Recommendation.py` in `app_final/api` to start project

```
project/
├── config.yaml                    # Global configuration file
├── requirements.txt               # Python dependencies   
├── data/
│   └── genai.db                   # SQLite database 
├── generated_pdfs/                # Directory for generated PDF files
├── static/
│   ├── css/
│   │   ├── application_helper.css
│   │   ├── application_overview.css
│   │   ├── global.css
│   │   ├── login.css
│   │   └── selections.css
│   ├── js/
│   │   ├── application.js
│   │   ├── auth.js
│   │   ├── login.js
│   │   ├── overview.js
│   │   └── selections.js
│   └── User_Interface/
│       ├── chat.png
│       ├── file attachment 1.svg
│       ├── Line 1.svg
│       ├── OIG4.jpeg
│       ├── profile.png
│       └── user.svg
├── templates/
│   ├── application_helper.html
│   ├── application_overview.html
│   ├── login.html
│   └── selections.html
├── app_final/
│   ├── api/
│   │   ├── __init__.py
│   │   ├── application_api.py
│   │   ├── auth_api.py
│   │   ├── pdf_api.py
│   │   ├── recommendation_api.py   # Application startup script
│   │   └── user.py
│   ├── application_helper/
│   │   ├── __init__.py
│   │   ├── app.py
│   │   ├── db.py                   
│   │   ├── interaction.py
│   │   └── openai_api.py
│   ├── application_overview/
│   │   ├── __init__.py
│   │   └── pdf_generator.py
│   ├── recommendation/
│   │   ├── __init__.py
│   │   ├── chains/
│   │   │   ├── academic_chain.py
│   │   │   ├── additional_chain.py
│   │   │   ├── general_chain.py
│   │   │   ├── language_chain.py
│   │   │   └── ranking_chain.py
│   │   └── prompts/
│   │       ├── academic_prompts.py
│   │       ├── additional_prompts.py
│   │       ├── general_prompts.py
│   │       ├── language_prompts.py
│   │       └── ranking_prompts.py
│   └── project_config.py           # Loads config.yaml from project root
├── chatbot_agent/
│   ├── agent.py
│   ├── recommendation_input.py     # Pydantic model for recommendation input
│   └── tools/
│       ├── academic_tool.py
│       ├── additional_tool.py
│       ├── extract_info_tool.py
│       ├── general_tool.py
│       ├── language_tool.py
│       └── ranking_tool.py
└── .venv/                         # Virtual environment directory (not included in Git)
```

## Installation

### Prerequisites
- Python 3.8 or higher
- Git

### Setup Steps

1. **Clone the Repository:**
   ```bash
   git clone https://github.com/yourusername/yourproject.git
   cd yourproject
   ```

2. **Create and Activate a Virtual Environment:**
   ```bash
   python -m venv .venv
   source .venv/bin/activate      # For Windows: .venv\Scripts\activate
   ```

3. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install the Project in Development Mode:**
   ```bash
   pip install -e .
   ```

5. **Configure the Application:**
   - Ensure the configuration file `config.yaml` is present at the project root.
   - Update `config.yaml` if necessary (e.g., set your OpenAI API key and database path). The example below shows a basic configuration:
     ```yaml
     config:
       api_keys:
         openai: "your_openai_api_key_here"
       llm:
         model_name: "gpt-4o-mini"
         temperature: 0
         max_tokens: 800
         presence_penalty: 0.0
         frequency_penalty: 0.2
         top_p: 1.0
       database:
         uri: "sqlite:///data/genai.db"
     ```

6. **Ensure the Database is in Place:**
   - The SQLite database (`genai.db`) should reside in the `data/` folder.
   - If the database does not exist, you may need to initialize it based on your schema.

## Running the Application

- **Start the Web API:**
- Before starting the application, make sure your virtual environment is activated and your environment variables are set. Then, from the root of your project, run the following commands:
  ```bash
  export PYTHONPATH=./
  python -m app_final.api.recommendation
  ```
- This will launch the Flask app using the module entry point at app_final/api/recommendation.py.
- **Access Frontend Pages:**
  - Frontend HTML files are served via Flask. Open your browser to view pages like `login.html`, `application_helper.html`, etc.

## Usage

- The project provides endpoints for user authentication, program recommendation, application helper and PDF generation.
- The chatbot agent integrates multiple filtering tools to offer personalized program recommendations.
## Troubleshooting

- Make sure your virtual environment is activated.
- Confirm that `config.yaml` and the database file are in the expected locations.
  - This project may include more than one config.yaml file (for example, one in app_final and another under a separate directory). Make sure you update both if necessary.
  Each config.yaml might define separate settings (e.g., API keys, database URIs). Confirm that these files align with your local environment (e.g., the correct OpenAI API key, the correct path to genai.db).
- Check console logs for errors if any functionality is not working as expected. 
- Chrome Privacy and Security Settings 
  - If the chatbot’s front-end page or some features do not load properly in Google Chrome, verify your browser’s privacy/security settings. Certain strict settings or extensions can block local script requests. 
  - If Chrome continues to have issues, try other browsers like Safari or Firefox to see if the problem persists. 
- Other General Tips 
  - Confirm you have installed all dependencies (e.g., pip install -r requirements.txt). 
  - If environment variables are required (for instance, OPENAI_API_KEY), ensure they are set before running the Flask server. 
  - If you run into module import errors, double-check the PYTHONPATH or re-check the relative imports in your code.

## Acknowledgements

- OpenAI, Flask, Langchain, and all contributors.

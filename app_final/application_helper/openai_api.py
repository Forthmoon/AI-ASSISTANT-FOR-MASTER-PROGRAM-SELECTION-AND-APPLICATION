from openai import OpenAI
from app_final.project_config import openai_api_key

client = OpenAI(api_key=openai_api_key)
def ask_openai(question):
    """Asks a question using the OpenAI API and retrieves an answer."""
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system",
                 "content": "You are a helpful assistant specialized in master program applications."},
                {"role": "system",
                 "content": "Only answer questions related to English-taught master program in Germany applications. Do not include unrelated details."},
                {"role": "system",
                 "content": "Please provide your answer in plain text using a concise, structured format (e.g., using bullet points or numbered steps) and avoid any markdown formatting (no asterisks, bold, etc.)."},
                {"role": "user", "content": question}
            ],
            temperature=0.7,
            max_tokens=1000,
            top_p=1.0,
            frequency_penalty=0.0,
            presence_penalty=0.0
        )
        return response.choices[0].message.content.strip()
    except Exception as e:
        return f"An error occurred: {e}"

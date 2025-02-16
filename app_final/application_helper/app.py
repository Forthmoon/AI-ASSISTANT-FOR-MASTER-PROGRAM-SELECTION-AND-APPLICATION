import sqlite3
from program import get_program_details_with_university, get_programs_by_city
from interaction import save_interaction
from openai_api import ask_openai

def is_irrelevant_question(question):
    relevant_keywords = ["program", "university", "semester", "academic", "language", "master", "masters"]
    return not any(keyword in question for keyword in relevant_keywords)

def chatbot():
    print("Welcome to the AI Application Helper!")

    # Chatbot loop
    while True:
        question = input("\nWhat can I help you with? (Type 'exit' to quit): ").strip().lower()

        if question == 'exit':
            print("Goodbye! Feel free to come back anytime.")
            break

        # Check for irrelevant questions
        if is_irrelevant_question(question):
            print("I'm here to assist with master's programs and related academic queries. Please ask relevant questions.")
            save_interaction(None, question, "Irrelevant question warning.")
            continue

        # Handle user commands
        elif "details" in question and "university" in question:
            program_name = input("Enter the program name: ").strip()
            university_name = input("Enter the university name: ").strip()
            program_details = get_program_details_with_university(program_name, university_name)

            if program_details:
                print(f"\nDetails for {program_name} at {university_name}:")
                for key, value in program_details.items():
                    print(f"- {key}: {value}")
                save_interaction(None, question, str(program_details))
                continue  # Veritabanında bilgi bulunduğunda API çağrısı yapma
            else:
                print("Sorry, no details found for the specified program and university. Let me check further...")
                response = ask_openai(f"{program_name} requirements at {university_name}")
                print(f"AI Agent: {response}")
                save_interaction(None, question, response)

        elif "deadline" in question and "program" in question:
            program_name = input("Enter the program name: ").strip()
            university_name = input("Enter the university name: ").strip()
            program_details = get_program_details_with_university(program_name, university_name)

            if program_details and "Application Deadline" in program_details:
                print(f"The application deadline for {program_name} at {university_name} is: {program_details['Application Deadline']}")
                save_interaction(None, question, program_details['Application Deadline'])
            else:
                print(f"No application deadline found for {program_name} at {university_name}. Let me check further...")
                response = ask_openai(f"Application deadline for {program_name} at {university_name}")
                print(f"AI Agent: {response}")
                save_interaction(None, question, response)

        elif "programs in" in question:
            city = input("Which city are you interested in? ").strip()
            programs = get_programs_by_city(city)

            if programs:
                print(f"\nPrograms available in {city}:")
                for program in programs:
                    print(f"- {program['Program Name']} at {program['University Name']} ({program['Duration']})")
                save_interaction(None, question, f"Listed programs in {city}")
            else:
                print(f"No programs found in {city}.")

        else:
            print("Let me check further...")
            response = ask_openai(question)
            print(f"AI Agent: {response}")
            save_interaction(None, question, response)

if __name__ == "__main__":
    chatbot()

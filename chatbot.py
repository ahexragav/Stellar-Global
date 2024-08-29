from dotenv import load_dotenv
import os
import mysql.connector
from twilio.rest import Client
from flask import Flask, request, render_template
from langchain_openai import ChatOpenAI
from twilio.twiml.messaging_response import MessagingResponse
from utils import send_whatsapp_message,receive_whatsapp_message
from langchain_core.prompts import ChatPromptTemplate
# Load environment variables
load_dotenv()



# MySQL database connection
db = mysql.connector.connect(
    host=os.getenv("DB_HOST"),
    user=os.getenv("DB_USER"),
    password=os.getenv("DB_PASSWORD"),
    database=os.getenv("DB_NAME")
)

# Initialize Flask app
app = Flask(__name__)


openai_api_key = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(
    model="gpt-3.5-turbo",
    temperature=0.7,
    max_tokens=50,
    api_key=openai_api_key
)

# Define the prompt template
prompt = ChatPromptTemplate.from_messages(
    [
        ("system", "You are a helpful assistant."),
        ("human", "{user_input}")
    ]
)
def generate_response(user_input):
    print("User input:", user_input)
    
    # Format the prompt with the user input
    formatted_prompt = prompt.format_messages(user_input=user_input)
    
    # Generate response from OpenAI
    response = llm.invoke(formatted_prompt)
    
    # Extract and return the response content
    response_message = response.content  # Directly access the content attribute
    
    print("AI response:", response_message)
    return response_message

@app.route('/sms', methods=['POST'])
def sms_reply():
    user_input = request.form.get('Body')
    from_number = request.form.get('From')
    print("Received user input:", user_input)

    # Generate a response using OpenAI
    response_message = generate_response(user_input)
    print("Generated response message:", response_message)

    # Send the response back via WhatsApp
    send_whatsapp_message(from_number, response_message)

    return "Message processed", 200


def process_message(message):
    if 'hi' in message.lower():
        return "Hi! What's your name and email?"
    elif '@' in message:
        name, email = extract_name_email(message)
        save_user_data(name, email)
        return f"Thanks {name}, your email {email} has been saved."
    else:
        return "Sorry, I didn't understand that. Could you provide your name and email?"

def extract_name_email(message):
    # Basic parsing, for better results, use regex or NER models
    parts = message.split()
    email = next((part for part in parts if "@" in part), None)
    name = " ".join(part for part in parts if part != email)
    return name, email

def save_user_data(name, email):
    cursor = db.cursor()
    cursor.execute("INSERT INTO users (name, email) VALUES (%s, %s)", (name, email))
    db.commit()
    cursor.close()






if __name__ == "__main__":
    app.run(debug=True)

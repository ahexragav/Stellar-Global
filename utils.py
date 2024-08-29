from dotenv import load_dotenv
import os
from twilio.rest import Client
load_dotenv()
# Twilio credentials
account_sid = os.getenv("ACCOUNT_SID")
auth_token = os.getenv("AUTH_TOKEN")
client = Client(account_sid, auth_token)

def send_whatsapp_message(to_number, message_body):
   
    print(to_number,message_body)
    message = client.messages.create(
    from_='whatsapp:+14155238886',
    body= f"{message_body}",
    to=f'{to_number}'
    )   
    return message.sid


def receive_whatsapp_message(request):
    from flask import request
    from twilio.twiml.messaging_response import MessagingResponse

    # Get incoming message and sender's phone number
    incoming_msg = request.form.get('Body')
    from_number = request.form.get('From')
   
    # Create a response
    resp = MessagingResponse()
    resp.message(f'Thank you for your message: {incoming_msg},{ from_number}')

    return str(resp)

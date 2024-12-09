from twilio.rest import Client
import random
from fastapi import HTTPException,status
# Twilio account credentials (you'll need to replace these with your actual credentials)
TWILIO_ACCOUNT_SID = 'your_account_sid'
TWILIO_AUTH_TOKEN = 'your_auth_token'
TWILIO_PHONE_NUMBER = 'your_twilio_phone_number'

client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

# Helper function to generate OTP
def generate_otp(length=6):
    return ''.join([str(random.randint(0, 9)) for _ in range(length)])

async def send_otp(to: str):
    otp = generate_otp()  # Generate a 6-digit OTP

    try:
        # Send OTP via SMS
        message = client.messages.create(
            body=f"Your OTP is: {otp}",
            from_=TWILIO_PHONE_NUMBER,
            to=to
        )
        print(f"OTP sent: {message.sid}")  # You can log or print message SID for debugging
        return otp
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to send OTP: {str(e)}"
        )

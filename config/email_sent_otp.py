
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
from config.config import settings

# SMTP Configuration
SMTP_SERVER = settings.SMTP_SERVER
SMTP_PORT = settings.SMTP_PORT
SMTP_USERNAME = settings.FROM_MAIL
SMTP_PASSWORD = settings.EMAIL_PASSWORD

# Configure Logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def send_reset_email(recipient_email: str, token: str):
    """
    Sends a password reset OTP email to the recipient.

    Args:
        recipient_email (str): The recipient's email address.
        token (str): The OTP token to be included in the email.

    Raises:
        Exception: If there is an error during the email sending process.
    """
    try:
        logging.info(f"Preparing to send OTP email to {recipient_email}")
        
        # Create the email message
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = recipient_email
        msg['Subject'] = "Password Reset OTP"
        
        body = f"""
        <p>Dear User,</p>
        <p style="color:red;">Your password reset OTP is:</p>
        <h2>{token}</h2>
        <p>This OTP will expire in 15 minutes. If you did not request this, please ignore this email.</p>
        <p>Best regards,</p>
        <p>Your Team</p>
        """
        msg.attach(MIMEText(body, 'html'))  # Sending HTML content

        # Connect to the SMTP server
        logging.info("Connecting to the SMTP server...")
        with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as server:
            server.set_debuglevel(1)  # Enable detailed debug output for troubleshooting
            server.starttls()  # Secure the connection
            logging.info("Logging into the SMTP server...")
            server.login(SMTP_USERNAME, SMTP_PASSWORD)
            
            # Send the email
            logging.info(f"Sending OTP email to {recipient_email}")
            server.sendmail(SMTP_USERNAME, recipient_email, msg.as_string())
            logging.info(f"OTP email successfully sent to {recipient_email}")

    except smtplib.SMTPException as e:
        logging.error(f"SMTP error occurred: {e}")
    except Exception as e:
        logging.error(f"An error occurred while sending email to {recipient_email}: {e}")


async def send_invoice_email(recipient_email: str, invoice_details: dict):
    print("user email ",recipient_email)
    try:
        logging.info(f"Starting email send process for {recipient_email}")
        
        # Create the email headers and body
        msg = MIMEMultipart()
        msg['From'] = SMTP_USERNAME
        msg['To'] = recipient_email
        msg['Subject'] = f"Invoice: Payment Confirmation (Invoice #{invoice_details['invoice_number']})"

        # Construct the email body
        body = f"""
        <p>Dear {invoice_details['full_name']},</p>
        <p>Thank you for your payment!</p>
        <p>Invoice Number: {invoice_details['invoice_number']}</p>
        <p>Amount Paid: ${invoice_details['amount_paid']}</p>
        <p>Payment Date: {invoice_details['payment_date']}</p>
        <p>Payment Method: {invoice_details['payment_method']}</p>
        <p>We appreciate your business. If you have any questions, please contact us.</p>
        <p>Best regards,</p>
        <p>Your Team</p>
        """
        msg.attach(MIMEText(body, 'html'))

        # Connecting to the SMTP server
        logging.info("Connecting to the SMTP server")
        server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls()  # Upgrade to secure connection
        logging.info("Starting TLS encryption and logging in")
        server.login(SMTP_USERNAME, SMTP_PASSWORD)

        # Send the email
        logging.info(f"Sending email to {recipient_email}")
        server.sendmail(SMTP_USERNAME, recipient_email, msg.as_string())
        
        server.quit()
        logging.info(f"Invoice email sent successfully to {recipient_email}")
    except Exception as e:
        logging.error(f"Failed to send invoice email: {e}")
# import smtplib
# from email.mime.text import MIMEText
# from email.mime.multipart import MIMEMultipart
# import smtplib
# from email.mime.multipart import MIMEMultipart
# from email.mime.text import MIMEText
# from config.config import settings
# SMTP_SERVER = settings.SMTP_SERVER
# SMTP_PORT = settings.SMTP_PORT
# SMTP_USERNAME = settings.FROM_MAIL
# SMTP_PASSWORD=settings.EMAIL_PASSWORD

# import logging
# logging.basicConfig(level=logging.INFO)

# def send_reset_email(recipient_email: str, token: str):
#     try:
#         logging.info(f"Starting email send process for {recipient_email}")
#         # Create the email headers and body
#         msg = MIMEMultipart()
#         msg['From'] = SMTP_USERNAME
#         msg['To'] = recipient_email
#         msg['Subject'] = "Password Reset OTP"
        
#         body = f"Your password reset OTP is: {token}. This OTP will expire soon."
#         msg.attach(MIMEText(body, 'plain'))
        
#         # Connecting to the SMTP server
#         logging.info("Connecting to the SMTP server")
#         server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
#         server.starttls()  # Upgrade to secure connection
#         logging.info("Starting TLS encryption and logging in")
#         server.login(SMTP_USERNAME, SMTP_PASSWORD)
        
#         # Send the email
#         logging.info(f"Sending email to {recipient_email}")
#         server.sendmail(SMTP_USERNAME, recipient_email, msg.as_string())
#         server.set_debuglevel(1)  # This will print out the low-level SMTP communication

#         server.quit()
#         logging.info(f"OTP sent successfully to {recipient_email}")
#     except Exception as e:
#         logging.error(f"Failed to send email: {e}")

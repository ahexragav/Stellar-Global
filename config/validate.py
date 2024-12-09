import re
# Function to validate the email format
def is_valid_email(email: str) -> bool:
    email_regex = r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$'
    return re.match(email_regex, email) is not None

# def validate_payment(payment_details: dict) -> bool:
#     """
#     Mock payment validation logic. Replace with actual payment gateway integration.
#     """
#     # Simulate payment validation (e.g., with a third-party API)
#     if "card_number" in payment_details and payment_details.get("amount", 0) > 0:
#         return True
#     return False
def validate_payment(payment_details):
    required_fields = ["method", "amount"]
    return all(field in payment_details for field in required_fields) and payment_details["amount"] > 0

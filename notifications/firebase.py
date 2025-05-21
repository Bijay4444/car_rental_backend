import os
import json
import requests
from dotenv import load_dotenv
from google.auth.transport.requests import Request
from google.oauth2 import service_account

load_dotenv()

def generate_firebase_auth_key():
    """
    Generate a Firebase authentication key using a service account.

    Returns:
        str: The access token for Firebase Cloud Messaging.
    """
    scopes = ['https://www.googleapis.com/auth/firebase.messaging']
    credentials_path = os.getenv('FIREBASE_CREDENTIAL_PATH')
    credentials = service_account.Credentials.from_service_account_file(
        credentials_path, scopes=scopes
    )
    credentials.refresh(Request())
    return credentials.token

def send_push_notification(auth_token, fcm_token, title, body, data=None):
    """
    Send a push notification to a device using Firebase Cloud Messaging.

    Args:
        auth_token (str): The Firebase access token.
        fcm_token (str): The device's FCM token.
        title (str): Notification title.
        body (str): Notification body.
        data (dict, optional): Additional data to send.

    Returns:
        tuple: (status_code, response_text) from the FCM API.
    """
    url = "https://fcm.googleapis.com/v1/projects/carrentalmanagement-d7fdd/messages:send"
    payload = {
        "message": {
            "token": fcm_token,
            "notification": {
                "title": title,
                "body": body
            },
            "data": data or {}
        }
    }
    headers = {
        'Content-Type': 'application/json',
        'Authorization': f'Bearer {auth_token}'
    }
    response = requests.post(url, headers=headers, data=json.dumps(payload))
    return response.status_code, response.text

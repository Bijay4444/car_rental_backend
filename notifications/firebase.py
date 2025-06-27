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
    """
    # Use the PROJECT ID from your service account, not client_id
    project_id = os.getenv('FIREBASE_PROJECT_ID')  # This should be 'myrides-raracube'
    
    url = f"https://fcm.googleapis.com/v1/projects/{project_id}/messages:send"
    
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

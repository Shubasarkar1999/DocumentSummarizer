import os
import google.auth
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
import json # Make sure json is imported for in-memory client_secrets
import io   # Make sure io is imported for in-memory client_secrets

# The SCOPES define what kind of data your application needs to access.
# For Google Drive, common scopes are:
# 'https://www.googleapis.com/auth/drive.readonly' (read-only access)
# 'https://www.googleapis.com/auth/drive.file' (access to files created by the app)
# 'https://www.googleapis.com/auth/drive' (full read/write access to all files)
# Choose the most appropriate scope for your needs.
SCOPES = ['https://www.googleapis.com/auth/drive.readonly'] # Example scope: Read-only access to Drive files

class TokenGenerator:
    def __init__(self, client_secret_file='client_secret.json', token_file='token.json'):
        self.client_secret_file = client_secret_file
        self.token_file = token_file
        self.creds = None

    def generate_token(self):
        """
        Generates and saves a token.json file for Google API authentication in the current directory.
        If a token.json already exists, it attempts to refresh it.
        If no valid token exists, it initiates an OAuth 2.0 flow.
        """
        creds = None
        # The file token.json stores the user's access and refresh tokens, and is
        # created automatically when the authorization flow completes for the first time.
        if os.path.exists(self.token_file):
            try:
                creds = Credentials.from_authorized_user_file(self.token_file, SCOPES)
                print(f"Loaded existing token from {self.token_file}")
            except Exception as e:
                print(f"Error loading token from {self.token_file}: {e}")
                creds = None # Invalidate creds if loading fails

        # If there are no (valid) credentials available, let the user log in.
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                # Attempt to refresh the token if it's expired and a refresh token exists
                try:
                    creds.refresh(Request())
                    print("Token refreshed successfully.")
                except Exception as e:
                    print(f"Error refreshing token: {e}. Re-authenticating...")
                    creds = None # Force re-authentication if refresh fails
            
            if not creds or not creds.valid: # If still no valid creds after refresh attempt
                print("Initiating new authentication flow...")
                try:
                    # Read client secrets from the file
                    flow = InstalledAppFlow.from_client_secrets_file(
                        self.client_secret_file, SCOPES)
                    
                    # Run the local server flow to get credentials
                    # This will open a browser window for user authentication
                    creds = flow.run_local_server(port=0) 
                    
                    print("Authentication successful.")
                except FileNotFoundError:
                    print(f"Error: {self.client_secret_file} not found. Please ensure it's in the same directory.")
                    return None
                except Exception as e:
                    print(f"An error occurred during the authentication flow: {e}")
                    return None

        # Save the credentials for the next run
        if creds:
            try:
                with open(self.token_file, 'w') as token:
                    token.write(creds.to_json())
                print(f"Token saved to {self.token_file}")
                return creds
            except Exception as e:
                print(f"Error saving token to {self.token_file}: {e}")
                return None
        return None

if __name__ == '__main__':
    print("Starting token generation process...")
    generator = TokenGenerator()
    generator.generate_token()
    print("Token generation process finished.")


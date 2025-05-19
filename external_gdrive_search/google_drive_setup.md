# Google Drive API Setup Instructions

This document provides step-by-step instructions for setting up the Google Drive API for the LlamaIndex search demo.

## Prerequisites
- A Google account
- Access to Google Cloud Console

## Step 1: Create a Google Cloud Project
1. Go to the [Google Cloud Console](https://console.cloud.google.com/)
2. Click on the project dropdown at the top of the page
3. Click on "New Project"
4. Enter a project name (e.g., "LlamaIndex Search Demo")
5. Click "Create"

## Step 2: Enable the Google Drive API
1. Select your newly created project
2. In the left sidebar, click on "APIs & Services" > "Library"
3. Search for "Google Drive API"
4. Click on "Google Drive API" in the search results
5. Click "Enable"

## Step 3: Configure OAuth Consent Screen
1. In the left sidebar, click on "APIs & Services" > "OAuth consent screen"
2. Select "External" user type (unless you have a Google Workspace account)
3. Click "Create"
4. Fill in the required information:
   - App name: "LlamaIndex Search Demo"
   - User support email: Your email address
   - Developer contact information: Your email address
5. Click "Save and Continue"
6. On the "Scopes" page, click "Add or Remove Scopes"
7. Add the scope: `https://www.googleapis.com/auth/drive.readonly`
8. Click "Save and Continue"
9. Add test users if needed, then click "Save and Continue"
10. Review your settings and click "Back to Dashboard"

## Step 4: Create OAuth 2.0 Credentials
1. In the left sidebar, click on "APIs & Services" > "Credentials"
2. Click "Create Credentials" and select "OAuth client ID"
3. Select "Desktop app" as the application type
4. Enter a name for your OAuth client (e.g., "LlamaIndex Desktop Client")
5. Click "Create"
6. A dialog will appear with your client ID and client secret
7. Click "Download JSON" to download your credentials file
8. Rename the downloaded file to `credentials.json`

## Step 5: Place Credentials in the Application Directory
1. Move the `credentials.json` file to the root directory of the LlamaIndex demo application
2. Ensure the file is named exactly `credentials.json`

## Step 6: First-Time Authentication
1. When you first run the application and connect to Google Drive, a browser window will open
2. Sign in with your Google account
3. You'll see a warning that the app isn't verified - click "Continue"
4. Grant the requested permissions to access your Google Drive files
5. After authentication, a token will be saved locally for future use

## Troubleshooting
- If you encounter errors about invalid credentials, ensure the credentials.json file is correctly placed
- If you see authentication errors, delete the token.pickle file (if it exists) and try again
- For "Access Denied" errors, check that you've enabled the Google Drive API and configured the OAuth consent screen correctly

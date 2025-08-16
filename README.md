Document Summarizer (FastAPI + Google Drive)
This project provides a robust application to download documents from Google Drive, extract their text, generate AI-powered summaries, and present these summaries in a user-friendly web interface with downloadable reports.

✨ Features
Google Drive Integration: Authenticate with Google Drive (OAuth2), list files, and download documents (PDFs, DOCX, TXTs, MD, CSV, XLSX, XLS).

Document Parsing: Extract raw text content from various document formats.

AI-Powered Summarization(openai/gpt-4o): Generate concise 5-10 sentence summaries for each document using a customizable summarization function.

Comprehensive Reporting:

Styled HTML Table(http://127.0.0.1:8000/rendered-summaries-html): Display all summaries in a responsive and styled web interface.

Individual File Links: Clickable links within the HTML table to view each document's raw summary text.

Collective Reports: Download all summaries consolidated into a single CSV or PDF report.

Modular API Design: Clear endpoints for each step of the process, making it easy to understand and extend.

🚀 Tech Stack
Backend: Python, FastAPI

Templates: Jinja2

PDF Generation: FPDF

Data Handling: Pandas

Google Drive API: google-api-python-client, google-auth-httplib2, google-auth-oauthlib

Document Parsing: PyMuPDF (fitz), pdfplumber, python-docx

AI Integration: openai (via OpenRouter)

Environment Variables: python-dotenv

Environment Management: venv



⚙️ Setup Instructions (from scratch)
Follow these steps to get the application up and running on your local machine:

1️⃣ Clone the Repository
git clone 
cd TextSummarizer

2️⃣ Create a Virtual Environment
It's recommended to use a virtual environment to manage dependencies:

python -m venv .venv

Activate your virtual environment:

Windows (Git Bash/CMD):

.venv\Scripts\activate


3️⃣ Install Dependencies
Ensure your pip is up to date, then install the required libraries:

pip install -r requirements.txt


4️⃣ Google Drive API & AI Model Setup (.env & client_secret.json)
Sensitive information should be managed carefully.

Google Cloud Console Setup (for client_secret.json):

Go to the Google Cloud Console.

Create a new project (or select an existing one).

Navigate to APIs & Services > Library and Enable the Google Drive API.

Go to APIs & Services > Credentials.

Click "Create Credentials" > "OAuth client ID".

Select "Desktop app" as the application type.

Download the generated client_secret.json file.

Place this client_secret.json file in the root directory of your TextSummarizer/ project. This file is REQUIRED for the Google Drive authentication flow to work.

Create Your .env File (for OPENROUTER_API_KEY):

Create a file named .env in the root directory of your TextSummarizer/ project.

Add your OpenRouter API key to this file:

OPENROUTER_API_KEY="sk-or-v1-YOUR_OPENROUTER_API_KEY"

Replace sk-or-v1-YOUR_OPENROUTER_API_KEY with your actual OpenRouter API Key.

Generate token.json for Google Drive Authentication (Mandatory Step):

The token.json file stores your user's access and refresh tokens. It's automatically created by the Google API client library the first time you authenticate. If it doesn't exist, is invalid, or needs to be refreshed, follow these steps:

Ensure client_secret.json is in the project root. This file contains the credentials the authentication tool needs.

Run the following command in your terminal (with your virtual environment activated):

python -m google_auth_oauthlib.tool \
  --client-secrets client_secret.json \
  --scope https://www.googleapis.com/auth/drive.readonly \
  --save

What this command does: It initiates an OAuth 2.0 authorization flow.

Browser Interaction: This will automatically open a web browser tab asking you to log in to your Google account and grant permissions to your application (specifically "See and download all your Google Drive files").

Token Generation: Upon successful authorization in the browser, the tool will automatically save the token.json file in your project's root directory. This token.json allows your application to authenticate with Google Drive without requiring re-login until the token expires.

Example structure after setup:

TextSummarizer/
├─ .env                  # Contains your OpenRouter API key
├─ client_secret.json    # **required** for Google Auth flow
├─ token.json            # Automatically generated after first authentication
├─ ... (other project files)


5️⃣ Run the Application
Start the FastAPI application using Uvicorn. The API will be available at http://127.0.0.1:5000.

uvicorn app:app --reload --host 127.0.0.1 --port 5000

🌐 API Endpoints
Once the application is running, you can interact with it via these endpoints:

/test-list/{folder_id} (GET): Lists file metadata (ID, name, MIME type) within a specified Google Drive folder.

/download-folder/{folder_id} (GET): Downloads all files from a specified Google Drive folder to the downloads/ directory.

/parse-folder/{folder_id} (GET): Downloads files, extracts their text, and saves the parsed content (raw text and JSON metadata) to parsed_outputs/.

/summarize-folder/{folder_id} (GET): (Main Orchestrator) Downloads, parses, and summarizes all documents in the given folder. It saves individual summaries to summaries/ and generates collective CSV and PDF reports in reports/.

/view-summaries (GET): Returns a JSON response providing the direct URL to the HTML web interface where all summaries are displayed. Use this endpoint from Swagger UI to get the link.

/rendered-summaries-html (GET - hidden from Swagger UI): This is the actual web interface that renders the styled HTML table of summaries. You'll navigate to this URL in your browser after running /summarize-folder.

Static File Serving for Summaries: Individual raw .txt summary files can be accessed directly from the summaries/ directory (e.g., http://127.0.0.1:5000/summaries/your_file_summary.txt). The links in the HTML table use this mechanism.

/reports/summaries_report.csv (GET): Provides the collective CSV report for download.

/reports/summaries_report.pdf (GET): Provides the collective PDF report for download.

🚶 User Flow Example
Get a Google Drive folder ID (e.g., from your Google Drive URL).

Trigger summarization and report generation (e.g., via browser or curl):

http://127.0.0.1:5000/summarize-folder/YOUR_GOOGLE_DRIVE_FOLDER_ID

This will process files, generate summaries, and create the CSV/PDF reports.

Get the URL for the web interface (e.g., via Swagger UI or curl):

http://127.0.0.1:5000/view-summaries

You will get a JSON response like: {"message": "...", "url": "http://127.0.0.1:5000/rendered-summaries-html"}

Open the web interface in your browser:

http://127.0.0.1:5000/rendered-summaries-html

Here, you will see the styled HTML table of all summaries. You can click on individual file names to see their raw text summary in a new tab, and use the dedicated buttons to download the collective CSV and PDF reports.

**Please download and extract the zip in sample outputs folder to watch the demo clip for full execution**
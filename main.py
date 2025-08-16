import os
import json
from typing import List, Dict

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

# Import dotenv to load environment variables
from dotenv import load_dotenv

# Load environment variables from .env file at the very start
load_dotenv()

# --- ENSURE DIRECTORIES EXIST BEFORE APP INITIALIZATION ---
# This function creates all necessary directories for the application.
# It's called here to guarantee they exist before StaticFiles tries to mount them.
def _ensure_dirs():
    os.makedirs("downloads", exist_ok=True)
    os.makedirs("parsed_outputs", exist_ok=True)
    os.makedirs("summaries", exist_ok=True)
    os.makedirs("reports", exist_ok=True) # Ensure reports directory exists

_ensure_dirs() # Call the function immediately after loading environment variables


# Assuming drive_utils, parse_utils, and summarize_utils are in the same directory
from utils.drive_utils import DriveClient
from utils.parse_utils import extract_text
from utils.summarize_utils import summarize_document 

import pandas as pd
from fpdf import FPDF

app = FastAPI(title="Drive Document Summarizer")
# Now, when StaticFiles is instantiated, these directories are guaranteed to exist.
app.mount("/summaries", StaticFiles(directory="summaries"), name="summaries")
app.mount("/reports", StaticFiles(directory="reports"), name="reports") # Mount reports directory for access
templates = Jinja2Templates(directory="templates")


@app.get("/test-list/{folder_id}")
async def test_list(folder_id: str):
    """
    Lists files in a specified Google Drive folder.
    """
    drive = DriveClient()
    drive.authenticate()
    files = drive.list_files_in_folder(folder_id)
    return {"files": files}


@app.get("/download-folder/{folder_id}")
async def download_folder(folder_id: str):
    """
    Downloads all files from a specified Google Drive folder to the 'downloads' directory.
    """
    drive = DriveClient()
    drive.authenticate()
    files = drive.list_files_in_folder(folder_id)

    if not files:
        return JSONResponse(content={"message": "No files found in this folder."}, status_code=404)

    downloaded_files = []
    # os.makedirs("downloads", exist_ok=True) # Not needed here, as _ensure_dirs() handles it globally

    for f in files:
        file_id = f["id"]
        name = f["name"]
        dest_path = os.path.join("downloads", name)
        drive.download_file(file_id, dest_path)
        downloaded_files.append(dest_path)

    return {"message": "Files downloaded successfully", "files": downloaded_files}


@app.get("/parse-folder/{folder_id}")
async def parse_folder(folder_id: str):
    """
    Downloads files from a folder, extracts text, and saves parsed content.
    """
    drive = DriveClient()
    drive.authenticate()
    files = drive.list_files_in_folder(folder_id)

    if not files:
        return JSONResponse(content={"message": "No files found in this folder."}, status_code=404)

    parsed_files = []

    for f in files:
        file_id = f["id"]
        name = f["name"]
        mime = f.get("mimeType")

        # Download locally
        dest_path = os.path.join("downloads", name)
        drive.download_file(file_id, dest_path)

        # Extract text
        text = extract_text(dest_path, mime)
        preview = text[:1000] + "..." if len(text) > 1000 else text

        file_info = {
            "file_name": name,
            "mime_type": mime,
            "chars": len(text),
            "preview": preview
        }
        parsed_files.append(file_info)

        # Save parsed file JSON
        save_path = os.path.join("parsed_outputs", f"{os.path.splitext(name)[0]}.json")
        with open(save_path, "w", encoding="utf-8") as out:
            json.dump({"full_text": text, **file_info}, out, ensure_ascii=False, indent=2)

        # Also save raw text for easy reading
        txt_path = os.path.join("parsed_outputs", f"{os.path.splitext(name)[0]}.txt")
        with open(txt_path, "w", encoding="utf-8") as out:
            out.write(text)

    # Save combined summary of parsed files
    combined_path = os.path.join("parsed_outputs", "parsed_summary.json")
    with open(combined_path, "w", encoding="utf-8") as out:
        json.dump({"parsed_files": parsed_files}, out, ensure_ascii=False, indent=2)

    return {
        "parsed_files": parsed_files,
        "saved_to": "parsed_outputs/"
    }


@app.get("/summarize-folder/{folder_id}")
async def summarize_folder(folder_id: str):
    """
    Downloads files, extracts text, summarizes them, and generates CSV/PDF reports.
    """
    drive = DriveClient()
    drive.authenticate()
    files = drive.list_files_in_folder(folder_id)

    if not files:
        return JSONResponse(content={"message": "No files found in this folder."}, status_code=404)

    # _ensure_dirs() # Not needed here, as it's called once at module load

    summaries = []

    for f in files:
        file_id = f["id"]
        name = f["name"]
        mime = f.get("mimeType")

        dest_path = os.path.join("downloads", name)
        drive.download_file(file_id, dest_path)

        text = extract_text(dest_path, mime)

        # Save extracted text
        txt_path = os.path.join("parsed_outputs", f"{os.path.splitext(name)[0]}.txt")
        with open(txt_path, "w", encoding="utf-8") as out:
            out.write(text)

        # Summarize
        summary_obj = summarize_document(name, text)

        # Save summary txt
        summary_path = os.path.join("summaries", f"{os.path.splitext(name)[0]}_summary.txt")
        with open(summary_path, "w", encoding="utf-8") as out:
            out.write(summary_obj["summary"])

        summaries.append({
            "file_name": name,
            "summary": summary_obj["summary"]
        })

    # Generate CSV report
    csv_path = os.path.join("reports", "summaries_report.csv")
    df = pd.DataFrame(summaries)
    df.to_csv(csv_path, index=False, encoding='utf-8-sig')

    # Generate PDF report
    pdf = FPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()
    pdf.set_font("Arial", "B", 14)
    pdf.cell(0, 10, "Document Summaries", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("Arial", "", 12)
    for s in summaries:
        pdf.multi_cell(0, 6, f"File: {s['file_name']}")
        pdf.multi_cell(0, 6, f"Summary: {s['summary']}")
        pdf.ln(5)

    pdf_path = os.path.join("reports", "summaries_report.pdf")
    pdf.output(pdf_path)

    final_output = {
        "summaries": summaries,
        "saved_text_to": "parsed_outputs/",
        "saved_summaries_to": "summaries/",
        "csv_report_link": f"/reports/{os.path.basename(csv_path)}", # Link to the CSV report
        "pdf_report_link": f"/reports/{os.path.basename(pdf_path)}"  # Link to the PDF report
    }

    print(json.dumps(final_output, ensure_ascii=False, indent=2))

    return final_output


@app.get("/view-summaries", response_class=JSONResponse)
async def view_summaries(request: Request):
    """
    Provides a URL to view the HTML table of summaries.
    The HTML content itself is rendered at the provided URL.
    """
    # This URL is where the actual HTML summaries page will be rendered by a browser
    summaries_html_url = "http://127.0.0.1:8000/rendered-summaries-html"
    return JSONResponse(content={
        "message": "To view the HTML table of summaries, please open the following URL in your web browser:",
        "url": summaries_html_url
    })

# This new endpoint will actually render the HTML for the summaries
@app.get("/rendered-summaries-html", response_class=HTMLResponse, include_in_schema=False)
async def rendered_summaries_html(request: Request):
    """
    Renders the HTML page displaying all generated summaries,
    including links to view individual summary text files and overall reports.
    """
    summaries_dir = "summaries"
    summaries_list = []
    report_links = { # Initialize report_links here
        "csv": None,
        "pdf": None
    }

    # Populate summaries_list with data and individual summary file URLs
    if os.path.exists(summaries_dir):
        for fname in os.listdir(summaries_dir):
            if fname.endswith("_summary.txt"):
                file_name_without_ext = os.path.splitext(fname)[0].replace("_summary", "")
                summary_text = ""
                with open(os.path.join(summaries_dir, fname), "r", encoding="utf-8") as f:
                    summary_text = f.read()
                
                # Construct the URL for the raw summary text file
                # The '/summaries/' part matches the app.mount("/summaries", ...)
                summary_file_url = f"/summaries/{fname}" 
                
                summaries_list.append({
                    "file_name": file_name_without_ext,
                    "summary": summary_text,
                    "summary_file_url": summary_file_url 
                })
    
    # Check for generated reports and create their URLs
    reports_dir = "reports"
    if os.path.exists(reports_dir):
        csv_report_name = "summaries_report.csv"
        pdf_report_name = "summaries_report.pdf"

        if os.path.exists(os.path.join(reports_dir, csv_report_name)):
            report_links["csv"] = f"/reports/{csv_report_name}"
        if os.path.exists(os.path.join(reports_dir, pdf_report_name)):
            report_links["pdf"] = f"/reports/{pdf_report_name}"


    return templates.TemplateResponse("summaries.html", {
        "request": request,
        "summaries": summaries_list,
        "report_links": report_links 
    })

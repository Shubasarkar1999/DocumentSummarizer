import fitz  # PyMuPDF
import pdfplumber
import docx
import os
import pandas as pd

def extract_text(file_path: str, mime: str = None) -> str:
    """
    Extracts text from various document types based on file extension.
    Supports PDF, DOCX, TXT, MD, CSV, XLSX, XLS.
    """
    ext = os.path.splitext(file_path)[1].lower()
    text = ""

    if ext == ".pdf":
        try:
            # Try pdfplumber first for better table extraction
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            print(f"Pdfplumber failed for {file_path}, falling back to PyMuPDF. Error: {e}")
            # Fallback to PyMuPDF if pdfplumber fails
            try:
                with fitz.open(file_path) as doc:
                    for page in doc:
                        text += page.get_text("text") + "\n"
            except Exception as e_fitz:
                text = f"(Error reading PDF with PyMuPDF: {e_fitz})"

    elif ext == ".docx":
        try:
            doc = docx.Document(file_path)
            text = "\n".join([para.text for para in doc.paragraphs if para.text.strip()])
        except Exception as e:
            text = f"(Error reading DOCX: {e})"

    elif ext in [".txt", ".md"]:
        # Using 'utf-8' with 'errors="ignore"' to handle potential encoding issues
        with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
            text = f.read()

    elif ext == ".csv":
        try:
            df = pd.read_csv(file_path)
            text = df.to_string(index=False) # Convert DataFrame to string
        except Exception as e:
            text = f"(Error reading CSV: {e})"

    elif ext in [".xlsx", ".xls"]:
        try:
            df = pd.read_excel(file_path)
            text = df.to_string(index=False) # Convert DataFrame to string
        except Exception as e:
            text = f"(Error reading Excel: {e})"

    else:
        text = f"(Unsupported file format: {ext})"

    return text.strip()


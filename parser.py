#!/usr/bin/env python3
import os
import re
import subprocess
import sys
from PyPDF2 import PdfReader

# Configuration: Define the directory containing PDFs and the name of the index file.
PDF_DIR = "pdfs"
INDEX_FILE = "records_index.txt"

def extract_text_using_pdftotext(pdf_path):
    """
    Attempt to extract text from a PDF using the external 'pdftotext' command.
    This method is generally faster than a Python-only approach.
    Returns the extracted text if successful; otherwise, returns None.
    """
    try:
        # Execute pdftotext with '-' to output text to stdout.
        result = subprocess.run(
            ["pdftotext", pdf_path, "-"],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except Exception as e:
        # Print an error message if pdftotext fails.
        print(f"pdftotext failed for {pdf_path}: {e}")
        return None

def extract_text(pdf_path):
    """
    Extract text from a PDF file.
    First, try using the external pdftotext command for speed.
    If that fails, fall back to using PyPDF2 to extract text from each page.
    """
    text = extract_text_using_pdftotext(pdf_path)
    if text is None:
        # Fallback: Use PyPDF2 to extract text if pdftotext is unavailable.
        text = ""
        try:
            reader = PdfReader(pdf_path)
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text += page_text + "\n"
        except Exception as e:
            print(f"Error reading {pdf_path} with PyPDF2: {e}")
    return text

def parse_records(text):
    """
    Parse the raw text from a PDF into individual records.
    In this implementation, a record is assumed to end when a line contains a phone number,
    detected by a regular expression matching a pattern like "(01202) 525072".
    Returns a list of individual records.
    """
    records = []
    current_record = ""
    # Define a regex pattern to identify a phone number: (digits) optional-space digits.
    phone_pattern = re.compile(r'\(\d+\)\s*\d+')
    
    # Process the text line by line.
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        
        # Append the current line to the accumulating record.
        if current_record:
            current_record += " " + line
        else:
            current_record = line
        
        # If the line contains a phone number, assume the record is complete.
        if phone_pattern.search(line):
            records.append(current_record)
            current_record = ""
    
    # If there is any leftover text that didn't end with a phone number, add it as a record.
    if current_record:
        records.append(current_record)
    return records

def index_pdfs():
    """
    Traverse all PDF files in the PDF_DIR directory.
    For each PDF, extract its text, parse it into records, and write each record
    to the INDEX_FILE with the source PDF filename prefixed.
    """
    with open(INDEX_FILE, "w", encoding="utf-8") as index_file:
        for filename in os.listdir(PDF_DIR):
            if filename.lower().endswith(".pdf"):
                pdf_path = os.path.join(PDF_DIR, filename)
                print(f"Indexing {pdf_path}...")
                text = extract_text(pdf_path)
                if not text:
                    continue
                records = parse_records(text)
                for record in records:
                    # Write the record to the index file, prefixed by the PDF filename.
                    index_file.write(f"{filename}: {record}\n")
    print(f"\nIndexing complete. {INDEX_FILE} has been created.")

def search_index(query):
    """
    Search the INDEX_FILE for the provided query using ripgrep (rg).
    The search is case-insensitive and uses the -F flag to treat the query as a fixed (literal) string.
    Displays the search results on stdout.
    """
    try:
        # Run ripgrep with:
        #   -i: case-insensitive search
        #   -F: fixed-string search (no regex interpretation)
        result = subprocess.run(
            ["rg", "-iF", query, INDEX_FILE],
            capture_output=True,
            text=True,
            check=True
        )
        output = result.stdout
        if output:
            print("\nSearch results:\n")
            print(output)
        else:
            print("No matching records found.")
    except subprocess.CalledProcessError as e:
        # An exit code of 1 indicates no matches; any other error is reported.
        if e.returncode == 1:
            print("No matching records found.")
        else:
            print("Error running ripgrep:", e)

def main():
    """
    Main workflow:
    - Checks if the PDF_DIR exists and contains PDF files. If not, runs scraper.py to download them.
    - Ensures that the INDEX_FILE exists by indexing the PDFs if necessary.
    - Prompts the user for a search query and uses ripgrep to search through the index.
    """
    # Check if the PDFs directory exists and is not empty; if empty, run scraper.py to download PDFs.
    if (not os.path.exists(PDF_DIR) or 
        not any(fname.lower().endswith(".pdf") for fname in os.listdir(PDF_DIR))):
        print("No PDF files found in the 'pdfs' directory. Running scraper.py to download PDFs...")
        subprocess.run([sys.executable, "scraper.py"])
    
    # Verify again that the PDF directory now contains PDF files.
    if not os.path.exists(PDF_DIR) or not any(fname.lower().endswith(".pdf") for fname in os.listdir(PDF_DIR)):
        print("No PDF files were downloaded. Exiting.")
        sys.exit(1)
    
    # If the index file does not exist, create it by indexing the PDFs.
    if not os.path.exists(INDEX_FILE):
        print("Index file not found. Indexing PDFs...")
        index_pdfs()
    else:
        print(f"Using existing index file: {INDEX_FILE}")
    
    # Prompt the user for a search query.
    query = input("\nEnter search query (name, address, or phone): ").strip()
    if not query:
        print("No query provided, exiting.")
        sys.exit(0)
    
    # Search the index for the query and display results.
    search_index(query)

# Run the main function if this script is executed directly.
if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin

def download_pdf(pdf_url, folder='pdfs'):
    """
    Download a single PDF file from the given URL (pdf_url) and save it in the specified folder.
    """
    # Ensure the download folder exists; if not, create it.
    if not os.path.exists(folder):
        os.makedirs(folder)
    
    # Extract the filename from the URL (ignoring any URL parameters)
    filename = os.path.basename(pdf_url.split('?')[0])
    # Create the complete file path by joining the folder and filename
    filepath = os.path.join(folder, filename)
    
    print(f"Downloading: {pdf_url}")
    try:
        # Send a GET request to download the PDF with stream=True for efficient chunked download
        response = requests.get(pdf_url, stream=True)
        # Raise an exception if the HTTP request returned an unsuccessful status code
        response.raise_for_status()
        # Open the target file in binary write mode and write the content in chunks
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)
        print(f"Saved to: {filepath}")
    except requests.RequestException as e:
        # Print an error message if the download fails
        print(f"Failed to download {pdf_url}: {e}")

def extract_pdf_links(url):
    """
    Fetch the webpage at the given URL and extract all links that end with '.pdf'.
    Converts relative URLs to absolute URLs.
    Returns a list of PDF links.
    """
    try:
        # Send a GET request to fetch the webpage content.
        response = requests.get(url)
        # Raise an exception if the HTTP request returned an unsuccessful status code
        response.raise_for_status()
    except requests.RequestException as e:
        # Print an error message if fetching the page fails and return an empty list.
        print(f"Error fetching the page {url}: {e}")
        return []
    
    # Parse the page content with BeautifulSoup using the 'html.parser'
    soup = BeautifulSoup(response.content, 'html.parser')
    pdf_links = []
    # Loop through all anchor (<a>) tags that have an href attribute
    for a in soup.find_all('a', href=True):
        href = a['href']
        # Check if the link ends with '.pdf' (case-insensitive)
        if href.lower().endswith('.pdf'):
            # Convert a relative URL to an absolute URL using the base URL
            full_url = urljoin(url, href)
            pdf_links.append(full_url)
    return pdf_links

def main():
    # Define the base URL from which to scrape PDF links (modify if necessary)
    base_url = "https://www.bt.com/help/the-phone-book/a-z-directory-finder"
    
    print(f"Fetching PDF links from {base_url}...")
    # Extract all PDF links from the given base URL
    pdf_links = extract_pdf_links(base_url)
    print(f"Found {len(pdf_links)} PDF files.")

    # Loop through the list of PDF URLs and download each one
    for pdf_url in pdf_links:
        download_pdf(pdf_url)

# If the script is run directly (not imported), execute the main function.
if __name__ == "__main__":
    main()

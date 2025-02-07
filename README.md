# BT Phonebook Lookup

A UK whitepages alternative which leverages the BT Phonebook and ripgrep to quickly parse through PDFs to find data on people, phone numbers, businesses, and addresses.

## Project Overview

This project downloads the BT Phonebook PDFs, indexes the data contained within them, and then allows you to quickly search for records (such as names, addresses, or phone numbers) using ripgrep for high performance.

## Project Structure

- **scraper.py**  
  Scrapes a predefined website for PDF links (sourced from the BT Phonebook) and downloads them into the `pdfs/` directory.

- **search_pdfs.py**  
  Checks if the `pdfs/` directory contains any PDFs. If not, it automatically executes `scraper.py` to download them. It then indexes the PDFs by extracting and parsing their text (using a phone number pattern as a delimiter) and provides an interactive search prompt powered by ripgrep.

- **requirements.txt**  
  Lists the Python packages required for this project.

## Requirements

- **Python 3.6+**

### Python Packages

- [PyPDF2](https://pypi.org/project/PyPDF2/)
- [requests](https://pypi.org/project/requests/)
- [beautifulsoup4](https://pypi.org/project/beautifulsoup4/)

### External Tools

- **pdftotext** (optional but recommended for fast PDF text extraction)  
  Refer to the [pdftotext documentation](https://www.xpdfreader.com/pdftotext-man.html) or install via your package manager.

- **ripgrep (rg)** (for fast, memory-efficient searching)  
  Visit [ripgrep on GitHub](https://github.com/BurntSushi/ripgrep) for installation instructions and ensure it is in your system's PATH.

## Installation

1. **Clone the repository** or download the scripts (`scraper.py`, `parser.py`, and `requirements.txt`) into the same directory.

2. **Install Python dependencies** using pip:

    ```bash
    pip install -r requirements.txt
    ```

3. **Ensure External Tools are Installed:**

    - Install **pdftotext**.
    - Install **ripgrep** and ensure it is available in your system's PATH.

## Usage

1. **Run the Search Script:**

    ```bash
    python parser.py
    ```

2. **Script Behavior:**
   - The script checks if the `pdfs` directory exists and contains any PDF files.
   - If no PDFs are found, it automatically runs `scraper.py` to download PDFs from the BT Phonebook.
   - Once the PDFs are available, the script indexes them (creating `records_index.txt`) and then prompts you for a search query.
   - Enter a search term (e.g., a name, address fragment, or phone number) to see matching records, which are retrieved using ripgrep.

## Customization

- **Change the Scraping URL:**  
  To modify the URL from which PDFs are scraped, edit the `base_url` variable in `scraper.py`.

- **Modify Record Parsing:**  
  Adjust the regular expression in the `parse_records` function in `parser.py` if your PDF data format changes.

## Acknowledgements

- [PyPDF2](https://pypi.org/project/PyPDF2/) for PDF text extraction.
- [requests](https://pypi.org/project/requests/) and [BeautifulSoup](https://pypi.org/project/beautifulsoup4/) for web scraping.
- [ripgrep](https://github.com/BurntSushi/ripgrep) for fast and efficient searching.
- [pdftotext](https://www.xpdfreader.com/pdftotext-man.html) for efficient PDF text extraction.
- AI for filling in my knowledge gaps.

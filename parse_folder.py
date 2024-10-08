import argparse
from bs4 import BeautifulSoup
import os
import re
from tqdm import tqdm

def extract_job_id_from_html(soup):
    job_id_element = soup.find('form-static', string='Job ID')
    if job_id_element:
        job_id = job_id_element.find_next_sibling('div', class_='field-widget')
        if job_id:
            return job_id.get_text(strip=True)
    return None

def extract_date_from_filepath(filepath):
    # Regular expression to match date in YYYY-MM-DD format
    date_pattern = r'\d{4}-\d{2}-\d{2}'
    filename = os.path.basename(filepath)
    match = re.search(date_pattern, filename)
    if match:
        return match.group(0)
    return None

def extract_job_title(soup):
    # Extract job title from the <h1> tag with class "job-title"
    job_title_element = soup.find('h1')
    if job_title_element:
        job_title_link = job_title_element.find('a', class_='job-title')
        if job_title_link:
            return job_title_link.get_text(strip=True)
    return None
    
def parse_html_file(filepath, verbose=False):
    with open(filepath, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    data = {}

    job_title = extract_job_title(soup)
    if job_title:
        data['Job Title'] = job_title
        
    job_id = extract_job_id_from_html(soup)
    if job_id:
        data['Job ID'] = job_id

    # Extract job description as HTML
    job_description_div = soup.find('div', class_='text-overflow space-top-lg text-gray p-group field-widget-tinymce')
    if job_description_div:
        job_description_html = job_description_div.prettify()  # Keep HTML formatting
        data['Job Description'] = job_description_html

    # Extract company name
    sidebar_header = soup.find('div', class_='sidebar-header')
    if sidebar_header:
        company_name_element = sidebar_header.find_next('h3')
        if company_name_element:
            data['Company Name'] = company_name_element.get_text(strip=True)

    # Extract location
    location_div = soup.find('div', class_='flexbox space-bottom-sm ng-star-inserted')
    if location_div:
        location_span = location_div.find('span', class_='text-overflow ng-star-inserted')
        if location_span:
            data['Location'] = location_span.get_text(separator='\n', strip=True)

    # Extract job posting date from filepath
    job_posting_date = extract_date_from_filepath(filepath)
    if job_posting_date:
        data['Job Posting Date'] = job_posting_date

    # Extract other details as plain text
    form_static_elements = soup.find_all('form-static')
    for form_static in form_static_elements:
        label = form_static.find('div', class_='field-label')
        value = form_static.find('div', class_='field-widget')
        
        if label and value:
            label_text = label.get_text(strip=True).replace(':', '')
            value_text = value.get_text(strip=True)
            
            # Handle "Preferred Program Clusters" separately to preserve newlines
            if label_text == "Preferred Program Clusters":
                value_text = value.get_text(separator='\n', strip=True)
            
            data[label_text] = value_text

    return data

def count_html_files(folderpath):
    """Count the total number of HTML files in the folder and subfolders."""
    count = 0
    for root, dirs, files in os.walk(folderpath):
        count += len([file for file in files if file.endswith('.html')])
    return count

def parse_folder(folderpath):
    label_to_file = {}  # Dictionary to store labels and the first file they are found in
    total_files = count_html_files(folderpath)

    with tqdm(total=total_files, desc="Processing files", unit="file") as pbar:
        for root, dirs, files in os.walk(folderpath):
            for file in files:
                if file.endswith('.html'):
                    filepath = os.path.join(root, file)
                    labels = parse_html_file(filepath)
                    for label in labels:
                        if label not in label_to_file:
                            label_to_file[label] = filepath  # Save the first file where the label is found
                    pbar.update(1)  # Update progress bar

    return label_to_file

def camel_case(s):
    # Use regular expression substitution to replace underscores and hyphens with spaces,
    # then title case the string (capitalize the first letter of each word), and remove spaces
    s = re.sub(r"(_|-)+", " ", s).title().replace(" ", "").replace("(", "").replace(")", "").replace("/","")
    
    # Join the string, ensuring the first letter is lowercase
    return ''.join([s[0].lower(), s[1:]])

    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse all HTML files in a folder for unique table labels.")
    parser.add_argument("-d", "--directory", help="Path to the folder containing HTML files.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print parsed labels.")

    args = parser.parse_args()

    label_to_file = parse_folder(args.directory)

    if args.verbose:
        for label, filepath in sorted(label_to_file.items()):
            print(f"Label: {label}\nFirst found in: {filepath}\n")
    else:
        print(f"Parsing completed. Found {len(label_to_file)} unique labels.")

    for label, _ in sorted(label_to_file.items()):
        print(f"\t'{label}': '{camel_case(label)}',")
import argparse
from bs4 import BeautifulSoup
import os
import re

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
    
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse HTML for job data.")
    parser.add_argument("-f", "--filepath", required=True, help="Path to the HTML file to be parsed.")
    parser.add_argument("-v", "--verbose", action="store_true", help="Print parsed data.")

    args = parser.parse_args()

    data = parse_html_file(args.filepath, args.verbose)
    
    if args.verbose:
        for key, value in data.items():
            print(f"{key}: {value}")
    else:
        print("Parsing completed.")

import argparse
from bs4 import BeautifulSoup
import re
import os
import json
from tqdm import tqdm
import logging
from datetime import datetime

# Same column mapping as before
column_mapping = {
    'Application Deadline': 'applicationDeadline',
    'Approximate Hours Per Week': 'approximateHoursPerWeek',
    'Company Name': 'companyName',
    'Compensation': 'compensation',
    'Contact': 'contact',
    'Job Description': 'jobDescription',
    'Job ID': 'jobId',
    'Job Location': 'jobLocation',
    'Job Posting Date': 'jobPostingDate',
    'Job Title': 'jobTitle',
    'Company Location': 'companyLocation',
    'Number of Openings': 'numberOfOpenings',
    'Position Type': 'positionType',
    'Preferred Program Clusters': 'preferredProgramClusters',
    'Remote/On-Site': 'remoteOnSite',
    'Required Qualifications': 'requiredQualifications',
    'Work Term': 'workTerm',
    'Work Term Duration': 'workTermDuration',
    'Work Term Duration (Other)': 'workTermDurationOther',
}

def extract_job_id_from_html(soup):
    job_id_element = soup.find('form-static', string='Job ID')
    if job_id_element:
        job_id = job_id_element.find_next_sibling('div', class_='field-widget')
        if job_id:
            return job_id.get_text(strip=True)
    return None

def extract_date_from_filepath(filepath):
    date_pattern = r'\d{4}-\d{2}-\d{2}'
    filename = os.path.basename(filepath)
    match = re.search(date_pattern, filename)
    if match:
        return match.group(0)
    return None    

def extract_job_title(soup):
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
            data['Company Location'] = location_span.get_text(separator='\n', strip=True)

    # Extract job posting date from filepath
    job_posting_date = extract_date_from_filepath(filepath)
    if job_posting_date:
        data['Job Posting Date'] = job_posting_date

    labels_needing_newlines = [
        "Preferred Program Clusters",
        "Work Duration",
        "Work Term Duration",
        "Job Location"
    ]

    # Extract other details as plain text
    form_static_elements = soup.find_all('form-static')
    for form_static in form_static_elements:
        label = form_static.find('div', class_='field-label')
        value = form_static.find('div', class_='field-widget')
        
        if label and value:
            label_text = label.get_text(strip=True).replace(':', '')
            value_text = value.get_text(strip=True)
            
            # Handle some labels separately to preserve newlines
            if label_text in labels_needing_newlines:
                value_text = value.get_text(separator='\n', strip=True)
            
            data[label_text] = value_text

    try:
        deadline = datetime.strptime(data["Application Deadline"], "%B %d, %Y")
        data["Application Deadline"] = deadline.strftime("%Y-%m-%d")
    except KeyError:
        print(f"Key 'Application Deadline' not found in file {filepath}")
        return None
    
    return data

def store_data_in_json(data, json_file):
    mapped_data = {column_mapping.get(key, key): value for key, value in data.items()}

    try:
        if os.path.exists(json_file):
            with open(json_file, 'r+', encoding='utf-8') as f:
                existing_data = json.load(f)
                if isinstance(existing_data, list):
                    existing_data.append(mapped_data)
                else:
                    existing_data = [existing_data, mapped_data]
                f.seek(0)
                json.dump(existing_data, f, indent=4)
        else:
            with open(json_file, 'w', encoding='utf-8') as f:
                json.dump([mapped_data], f, indent=4)
    except Exception as e:
        logging.error(f"Error saving to JSON: {e}")

if __name__ == "__main__":
    logging.basicConfig(filename='run.log', level=logging.INFO, format='%(asctime)s %(message)s')

    parser = argparse.ArgumentParser(description="Parse HTML files in a folder and store data in JSON.")
    parser.add_argument("-d", "--directory", default=os.getcwd(), help="Path to the directory containing HTML files. Default is the current directory.")
    parser.add_argument("-o", "--output", default=os.path.join(os.getcwd(), "job_postings.json"), help="JSON file to store the parsed data. Default is 'job_postings.json' in the directory specified by -d.")
    parser.add_argument("-v", "--verbose", action="store_true", help="logging.info parsed data.")

    args = parser.parse_args()

    # Get the list of files
    files = [os.path.join(dirpath, file) for dirpath, _, files in os.walk(args.directory) for file in files if file.endswith('.html') or file.endswith('.htm')]

    # Create a progress bar
    with tqdm(total=len(files)) as pbar:
        for subdir, _, files in os.walk(args.directory):
            job_posting_date = os.path.basename(subdir)
            for file in files:
                if file.endswith('.html') or file.endswith('.htm'):
                    filepath = os.path.join(subdir, file)
                    logging.info(filepath)
                    data = parse_html_file(filepath, args.verbose)
                    if data is None:
                        continue
                    store_data_in_json(data, args.output)
                    # Update the progress bar
                    pbar.update(1)

    logging.info("Parsing and storing completed.")

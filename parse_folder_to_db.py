import argparse
from bs4 import BeautifulSoup
import re
import os
import sqlite3
from tqdm import tqdm
import logging

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
            data['Company Location'] = location_span.get_text(separator='\n', strip=True)

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

def store_data_in_db(data, db_cursor):
    mapped_data = {column_mapping.get(key, key): value for key, value in data.items()}

    columns = ', '.join([f'"{key}"' for key in mapped_data.keys()])
    placeholders = ', '.join(['?' for _ in mapped_data.values()])
    
    sql = f'INSERT OR REPLACE INTO "JobPosting" ({columns}) VALUES ({placeholders})'
    try:
        db_cursor.execute(sql, tuple(data.values()))
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")

def create_db_schema(db_cursor):
    db_cursor.execute('''
        CREATE TABLE IF NOT EXISTS JobPosting (
            applicationDeadline TEXT,
            approximateHoursPerWeek TEXT,
            companyName TEXT,
            compensation TEXT,
            contact TEXT,
            jobDescription TEXT,
            jobId TEXT PRIMARY KEY,
            jobLocation TEXT,
            jobPostingDate TEXT,
            jobTitle TEXT,
            companyLocation TEXT,
            numberOfOpenings INTEGER,
            positionType TEXT,
            preferredProgramClusters TEXT,
            remoteOnSite TEXT,
            requiredQualifications TEXT,
            workTerm TEXT,
            workTermDuration TEXT,
            workTermDurationOther TEXT
        )
    ''')

if __name__ == "__main__":
    logging.basicConfig(filename='run.log', level=logging.INFO, format='%(asctime)s %(message)s')

    parser = argparse.ArgumentParser(description="Parse HTML files in a folder and store data in SQLite DB.")
    parser.add_argument("-d", "--directory", default=os.getcwd(), help="Path to the directory containing HTML files. Default is the current directory.")
    parser.add_argument("--db", default=os.path.join(os.getcwd(), "job_postings.db"), help="SQLite database file to store the parsed data. Default is 'job_postings.db' in the directory specified by -d.")
    parser.add_argument("-v", "--verbose", action="store_true", help="logging.info parsed data.")

    args = parser.parse_args()

    conn = sqlite3.connect(args.db)
    cursor = conn.cursor()
    create_db_schema(cursor)

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
                    store_data_in_db(data, cursor)
                    # Update the progress bar
                    pbar.update(1)

    conn.commit()
    conn.close()
    logging.info("Parsing and storing completed.")

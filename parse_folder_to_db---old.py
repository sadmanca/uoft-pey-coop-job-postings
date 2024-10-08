import argparse
from bs4 import BeautifulSoup
import re
import os
import sqlite3
from tqdm import tqdm
import logging

def extract_job_id_from_html(soup):
    # Try to find job ID in a <h1> tag with the specific class
    header_tag = soup.find('h1', class_='h3 dashboard-header__profile-information-name mobile--small-font color--font--white margin--b--s')
    if header_tag:
        header_text = header_tag.get_text(strip=True)
        match = re.match(r'^(\d+)', header_text)
        if match:
            return match.group(1)

    # If not found, try to find an <h1> tag containing the words "Job ID"
    job_id_tag = soup.find('h1', string=re.compile(r'Job ID', re.IGNORECASE))
    if job_id_tag:
        job_id_text = job_id_tag.get_text(strip=True)
        match = re.search(r'Job ID\s*:\s*(\d+)', job_id_text, re.IGNORECASE)
        if match:
            return match.group(1)

    return None

def parse_html_file(filepath, job_posting_date, verbose=False):
    with open(filepath, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'lxml')

    data = {}
    job_id = extract_job_id_from_html(soup)
    if job_id:
        data['id'] = job_id

    rows = soup.find_all('tr')  # find all table rows

    for row in rows:
        tds = row.find_all('td')  # find all table data cells

        if len(tds) >= 2:
            label_td = tds[0]
            label_text = '\n'.join(label_td.stripped_strings).replace(':', '')

            value_td = tds[1]
            value_text = '\n'.join(value_td.stripped_strings)

            links = value_td.find_all('a')
            for link in links:
                url = link.get('href')
                link_text = link.get_text()
                value_text = value_text.replace(link_text, f'{link_text} ({url})')

            # Map label_text to corresponding database column
            column_mapping = {
                #'Job ID': 'id',
                'Work Study Stream': 'workStudyStream',
                'Position Type': 'positionType',
                'Campus Location': 'campusLocation',
                'Work Study Position Title': 'title',
                '# of Vacancies': 'numPositions',
                'This opportunity usually occurs during the following days/hours': 'weeklySchedule',
                'Hours Per Week': 'hoursPerWeek',
                'Degree/Credential Level': 'degreeLevel',
                'Department / Unit Overview': 'departmentOverview',
                'Position Description': 'description',
                'Qualifications': 'qualifications',
                'Accessibility Considerations': 'accessibilityConsiderations',
                'Commitment to Accessibility': 'accessibilityAccommodations',
                'Skills': 'skills',
                'Scholarship Recipients': 'scholarshipRecipientPreference',
                'Application Deadline': 'applicationDeadline',
                'Application Procedure': 'applicationProcedure',
                'Application Documents Required': 'applicationDocuments',
                'Organization': 'organization',
                'Division': 'division',
                'Department / Unit': 'department',
                'Supervisor\'s Name': 'supervisor',
                'Supervisor\'s Title': 'supervisorTitle',
            }

            # Check if label_text matches any of the predefined columns
            if label_text in column_mapping:
                db_column = column_mapping[label_text]
                # If key already exists, append the value to it
                if db_column in data:
                    data[db_column] += f'\n{value_text}'
                else:
                    data[db_column] = value_text

    return data

def store_data_in_db(data, db_cursor):
    columns = ', '.join([f'"{key}"' for key in data.keys()])
    placeholders = ', '.join(['?' for _ in data.values()])
    sql = f'INSERT OR REPLACE INTO "JobPosting" ({columns}) VALUES ({placeholders})'
    try:
        db_cursor.execute(sql, tuple(data.values()))
    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")

def create_db_schema(db_cursor):
    db_cursor.execute('''
    CREATE TABLE IF NOT EXISTS JobPosting (
        id INTEGER PRIMARY KEY,
        workStudyStream TEXT,
        positionType TEXT,
        campusLocation TEXT,
        title TEXT,
        numPositions INTEGER,
        weeklySchedule TEXT,
        hoursPerWeek TEXT,
        degreeLevel TEXT,
        departmentOverview TEXT,
        description TEXT,
        qualifications TEXT,
        accessibilityConsiderations TEXT,
        accessibilityAccommodations TEXT,
        skills TEXT,
        scholarshipRecipientPreference TEXT,
        applicationDeadline TEXT,
        applicationProcedure TEXT,
        applicationDocuments TEXT,
        organization TEXT,
        division TEXT,
        department TEXT,
        supervisor TEXT,
        supervisorTitle TEXT
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
                    data = parse_html_file(filepath, job_posting_date, args.verbose)
                    store_data_in_db(data, cursor)
                    # Update the progress bar
                    pbar.update(1)

    conn.commit()
    conn.close()
    logging.info("Parsing and storing completed.")

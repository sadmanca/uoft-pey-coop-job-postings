import argparse
from bs4 import BeautifulSoup

def extract_job_id_from_html(soup):
    job_id_element = soup.find('form-static', string='Job ID')
    if job_id_element:
        job_id = job_id_element.find_next_sibling('div', class_='field-widget')
        if job_id:
            return job_id.get_text(strip=True)
    return None

def parse_html_file(filepath, verbose=False):
    with open(filepath, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    data = {}
    job_id = extract_job_id_from_html(soup)
    if job_id:
        data['Job ID'] = job_id

    # Extract job description
    job_description_div = soup.find('div', class_='text-overflow space-top-lg text-gray p-group field-widget-tinymce')
    if job_description_div:
        job_description = job_description_div.get_text(separator='\n', strip=True)
        data['Job Description'] = job_description

    # Extract other details if needed
    form_static_elements = soup.find_all('form-static')
    for form_static in form_static_elements:
        label = form_static.find('div', class_='field-label')
        value = form_static.find('div', class_='field-widget')
        
        if label and value:
            label_text = label.get_text(strip=True).replace(':', '')
            value_text = value.get_text(strip=True)
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

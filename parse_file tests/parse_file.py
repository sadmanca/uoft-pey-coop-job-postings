import argparse
from bs4 import BeautifulSoup

def extract_job_id_from_html(soup):
    # Find job ID in the <p> tag with the specific id
    job_id_tag = soup.find('p', id='sy_formfield_visual_id_WSV1726539863852')
    if job_id_tag:
        return job_id_tag.get_text(strip=True)
    
    return None

def parse_html_file(filepath, verbose=False):
    with open(filepath, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'html.parser')

    data = {}
    job_id = extract_job_id_from_html(soup)
    if job_id:
        data['Job ID'] = job_id

    # Find all the form-static elements with labels and values
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

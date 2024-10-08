import argparse
import os
from bs4 import BeautifulSoup
from tqdm import tqdm

def parse_html_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as file:
        html_content = file.read()

    soup = BeautifulSoup(html_content, 'lxml')

    labels = set()

    rows = soup.find_all('tr')  # find all table rows

    for row in rows:
        tds = row.find_all('td')  # find all table data cells
        
        if len(tds) >= 2:
            label_td = tds[0]
            label_text = '\n'.join(label_td.stripped_strings).replace(':', '')
            labels.add(label_text)

    return labels

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

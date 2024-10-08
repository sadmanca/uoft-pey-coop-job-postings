# UofT Work Study Jobs Database (2024-2025 Fall/Winter)

This repository contains the code for parsing 2000+ HTML pages of UofT work study job postings (from August to September 2024) to a single `sqlite3` database (.db) file.

## Releases

See releases to access the latest `sqlite3` database file (.db) with work study job postings. Other formats are also available (.json, .sql, .csv, .xlsx).

## File Structure

- `parse_folder_to_db.py`: main Python script used for parsing the HTML pages in a folder recursively.
- `requirements.txt`: required imports 

## Getting Started

To get started with this project, clone the repository and install the necessary Python dependencies.

```bash
git clone https://github.com/sadmanca/uoft-work-study-jobs-2024.git
cd uoft-work-study-jobs-2024
pip install -r requirements.txt
```

## Usage

To parse the HTML pages and store the data in a database, run the `parse_folder_to_db.py` script.

```bash
python parse_folder_to_db.py
```

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

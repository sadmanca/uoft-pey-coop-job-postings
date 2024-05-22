# UofT PEY Co-op Job Postings Analysis

This repository contains the code for parsing approximately 1.8k HTML pages of UofT PEY co-op job postings (from September 2023 to May 2024) to a single `sqlite3` database file.

## Releases

See releases to access the latest `sqlite3` database with PEY Co-op job postings.

## File Structure

- `parse_to_db.py`: main Python script used for parsing the HTML pages.
- `requirements.txt`: required imports 

## Getting Started

To get started with this project, clone the repository and install the necessary Python dependencies.

```bash
git clone https://github.com/sadmanca/uoft-pey-coop-job-postings-analysis.git
cd uoft-pey-coop-job-postings-analysis
pip install -r requirements.txt
```

## Usage

To parse the HTML pages and store the data in a database, run the `parse_to_db.py` script.

```bash
python parse_to_db.py
```

## Additional Information

The `index.qmd` file contains additional information about the job postings. This includes details such as the job title, company, location, and job description. This information is used to enrich the data obtained from the HTML pages.

## Contributing

Contributions are welcome! Please read the contributing guidelines before making any changes.

## License

This project is licensed under the MIT License. See the LICENSE file for more details.

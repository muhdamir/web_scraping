# Web Scraping

## Scraping by Inspecting The API Calls from The Browser.
The aim of this approach is to find the underlying API of the website by inspecting the network tab in the browser.
You can see the implementation of this approach through this script `scraper_requests_api.py`

## Scraping Straight Away from The Website
The website can also be scraped straightaway. You can see later in the script, I'm using lxml library to extract information using xpath from the html doc. Refer this script: `scraper_requests_lxml.py`

## Running The Script: for scraping
📝 Please use `python 3.11` to run the script.

install the libraries in requirements.txt
```bash
pip install -r ./requirements.txt
```

Then run the script (please run this one since the data scraped will be 200)
```bash
python ./scraper_requests_api.py
```
or
```bash
python ./scraper_requests_lxml.py
```


## Running The Script: for data migration (from csv to mysql db)

To make things easy, I've provided a docker-compose.yaml file. So we easily start our db service as follows:

```bash
docker-compose up --build
```

Then run the migration script
```bash
python ./data_migration.py
```



# Web Scraping
There are two python script available of which each is using different method.

## Scraping by Inspecting The API Calls from The Browser.
The aim of this approach is to find the underlying API of the website by inspecting the network tab in the browser.

You can see the implementation of this approach through this script `scraper_requests_api.py`

## Scraping Straight Away from The Website
The website can also be scraped straightaway. You can see later in the script, I'm using lxml library to extract information using xpath from the html doc. Refer this script: `scraper_requests_lxml.py`

## Running The Script
📝 Please use `python 3.11` to run the script.

install the libraries in requirements.txt
```bash
pip install -r ./requirements.txt
```

Then run the script
```bash
python ./scraper_requests_api.py
```
or
```bash
python ./scraper_requests_lxml.py
```





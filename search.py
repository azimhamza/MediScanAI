import requests
from xml.etree import ElementTree as ET

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
SEARCH_URL = BASE_URL + "esearch.fcgi"
FETCH_URL = BASE_URL + "efetch.fcgi"

def search_pubmed(query):
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": 100,  # Adjust as needed
        "usehistory": "y",
        "retmode": "xml"
    }

    search_response = requests.get(SEARCH_URL, params=params)
    search_response.raise_for_status()  # Raise exception if invalid response
    search_tree = ET.fromstring(search_response.content)

    webenv = search_tree.find("WebEnv").text
    query_key = search_tree.find("QueryKey").text

    return (webenv, query_key)


def fetch_pubmed(webenv, query_key):
    params = {
        "db": "pubmed",
        "query_key": query_key,
        "WebEnv": webenv,
        "retmode": "xml"
    }

    fetch_response = requests.get(FETCH_URL, params=params)
    fetch_response.raise_for_status()
    return fetch_response.content


def save_xml(content, file_name):
    with open(file_name, 'wb') as f:
        f.write(content)


def main():
    # Adjust your query here
    query = "(COVID-19 OR SARS-CoV-2) AND heart disease"

    webenv, query_key = search_pubmed(query)
    content = fetch_pubmed(webenv, query_key)

    # Save to XML file
    save_xml(content, 'articles.xml')

main()

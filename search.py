import requests
import json
from xml.etree import ElementTree as ET

BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
SEARCH_URL = BASE_URL + "esearch.fcgi"
FETCH_URL = BASE_URL + "efetch.fcgi"

def parse_pubmed_xml(xml_content):
    root = ET.fromstring(xml_content)
    data = []
    for article in root.findall("./PubmedArticle"):
        article_data = {}
        article_info = article.find("MedlineCitation/Article")
        if article_info is not None:
            # Extract article title
            title_info = article_info.find("ArticleTitle")
            if title_info is not None:
                article_data["title"] = title_info.text
            
            # Extract abstract
            abstract_info = article_info.find("Abstract/AbstractText")
            if abstract_info is not None:
                article_data["abstract"] = abstract_info.text
            
            # Extract authors
            authors_info = article_info.findall("AuthorList/Author")
            authors = []
            for author_info in authors_info:
                author_name_parts = [
                    author_info.find(part).text for part in ["LastName", "ForeName"]
                    if author_info.find(part) is not None
                ]
                authors.append(" ".join(author_name_parts))
            if authors:
                article_data["authors"] = authors
            
            # Extract citation
            journal_info = article_info.find("Journal")
            if journal_info is not None:
                journal_title_info = journal_info.find("Title")
                if journal_title_info is not None:
                    article_data["citation"] = journal_title_info.text
            
        # Extract PMC ID
        pmc_id_info = article.find("./PubmedData/ArticleIdList/ArticleId[@IdType='pmc']")
        if pmc_id_info is not None:
            article_data["pmc_id"] = pmc_id_info.text

        article_data["queryContext"] = query;
        
        

        data.append(article_data)
        

    return data

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

def save_json(data, file_name):
    with open(file_name, 'w') as f:
        json.dump(data, f)

def main():
    # Adjust your query here
    query = "(COVID-19 OR SARS-CoV-2) AND heart disease"

    webenv, query_key = search_pubmed(query)
    xml_content = fetch_pubmed(webenv, query_key)
    data = parse_pubmed_xml(xml_content)

    # Save to JSON file
    save_json(data, 'articles.json')

main()

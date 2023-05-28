import mediPrompt as mp

def parse_pubmed_xml(xml_content, query):
    root = mp.ET.fromstring(xml_content)
    data = []
    for article in root.findall("./PubmedArticle"):
        article_data = {}
        article_info = article.find("MedlineCitation/Article")
        if article_info is not None:
            title_info = article_info.find("ArticleTitle")
            if title_info is not None:
                article_data["title"] = title_info.text

            abstract_info = article_info.find("Abstract/AbstractText")
            if abstract_info is not None:
                article_data["abstract"] = abstract_info.text

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

            journal_info = article_info.find("Journal")
            if journal_info is not None:
                journal_title_info = journal_info.find("Title")
                if journal_title_info is not None:
                    article_data["citation"] = journal_title_info.text

        article_data["queryContext"] = query

        data.append(article_data)
    return data


def search_pubmed(query):
    params = {
        "db": "pubmed",
        "term": query,
        "retmax": 100,
        "usehistory": "y",
        "retmode": "xml"
    }

    search_response = mp.requests.get(mp.SEARCH_URL, params=params)
    search_response.raise_for_status()
    search_tree = mp.ET.fromstring(search_response.content)

    webenv = search_tree.find("WebEnv").text
    query_key = search_tree.find("QueryKey").text

    return (webenv, query_key)


def fetch_pubmed(webenv, query_key):
    params = {
        "db": "pubmed",
        "query_key": query_key,
        "WebEnv": webenv,
        "retmax": 100,
        "retmode": "xml"
    }

    fetch_response = mp.requests.get(mp.FETCH_URL, params=params)
    fetch_response.raise_for_status()

    return fetch_response.content


def search_and_fetch(query):
    webenv, query_key = search_pubmed(query)
    fetched_content = fetch_pubmed(webenv, query_key)
    return fetched_content


def search_title_weaviate(title):
    search_params = {
        "query": f"""
        {{
            Get {{
                ResearchArticle(
                    explore: {{nearText: {{query: "{title}", certainty: 0.7}}}}
                    limit: 1
                ) {{
                    title
                    abstract
                    authors
                    citation
                }}
            }}
        }}"""
    }

    search_response = mp.client.query.raw(query=mp.json.dumps(search_params))
    articles = search_response['data']['Get']['ResearchArticle']
    return articles




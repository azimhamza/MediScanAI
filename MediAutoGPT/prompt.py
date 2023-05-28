from nntplib import ArticleInfo
import requests
import json
from xml.etree import ElementTree as ET
import weaviate
from langchain.chat_models import ChatOpenAI
from langchain import PromptTemplate, LLMChain
from langchain.prompts.chat import (
    ChatPromptTemplate,
    SystemMessagePromptTemplate,
    HumanMessagePromptTemplate
)
from langchain.schema import (
    AIMessage,
    HumanMessage,
    SystemMessage
)

from duckduckgo_search import DuckDuckGoSearchRun


from uuid import uuid4
for article in ArticleInfo:
    article['id'] = str(uuid4())  # add a UUID to each article
    weaviate.Client.data_object.create(
        data_object=article, class_name="ResearchArticle")

search = DuckDuckGoSearchRun()


def search_duckduckgo(query):
    search_result = search.run(query)
    summary = "Here are some Articles that might be relevant to your query: \n"


BASE_URL = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/"
SEARCH_URL = BASE_URL + "esearch.fcgi"
FETCH_URL = BASE_URL + "efetch.fcgi"

auth_config = weaviate.AuthApiKey(
    api_key='NvRXfGrL8Ci1Hb3CazufLMIM9s2l3q6SbSsx')
client = weaviate.Client(
    "https://mediscanai-hi0v9ojp.weaviate.network", auth_client_secret=auth_config)

# Initialize the chat model with your API key and a temperature value
chat = ChatOpenAI(
    temperature=0.2, openai_api_key="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")

# Prepare your system message template
system_template = "You are a helpful AI trained to listen to descriptions of symptoms or conditions, offer a preliminary suggestion in JSON format, generate search queries for PubMed, and signal the end of the process with the statement 'process-done'."
system_message_prompt = SystemMessagePromptTemplate.from_template(
    system_template)

# Combine system and human prompts into a chat prompt
chat_prompt = ChatPromptTemplate.from_messages([system_message_prompt])

# Start conversation
conversation = [SystemMessage(content=system_template.format())]


def parse_pubmed_xml(xml_content, query):
    root = ET.fromstring(xml_content)
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

    search_response = requests.get(SEARCH_URL, params=params)
    search_response.raise_for_status()
    search_tree = ET.fromstring(search_response.content)

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

    fetch_response = requests.get(FETCH_URL, params=params)
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

    search_response = client.query.raw(query=json.dumps(search_params))
    articles = search_response['data']['Get']['ResearchArticle']
    return articles


while True:
    # User's turn
    # Replace with your method of obtaining user input
    user_input = input("User: ")
    # Check if user input is a search for a specific title
    if user_input.lower().startswith("search for"):
        title = user_input[11:]  # Extract the title from the user input
        articles = search_title_weaviate(title)

        # Check if any articles were found
        if articles:
            article = articles[0]

            print(
                f"Title: {article['title']}, Explanation: {article['abstract']}")
            continue  # Skip the rest of the loop and wait for the next user input
        else:
            print(f"No article found with title: {title}")
            continue
    conversation.append(HumanMessage(content=user_input))

    # Generate response
    chat_input = chat_prompt.format_prompt().to_messages()
    chat_input.extend(conversation[-1:])  # Add last user's turn to the input
    response = chat(chat_input)

    # Add AI's turn to the conversation
    conversation.append(AIMessage(content=response.content))

    print(f"AI: {response.content}")

    # If the AI signaled the end of the process, perform Weaviate search
    if 'process-done' in response.content:
        # Extract the query terms from the response content
        # modify this as per the actual format of the response.content
        query_terms = response.content.split(':')[-1].strip()

        duckduckgo_summary = search_duckduckgo(query_terms)
        print(duckduckgo_summary)
        # Search the Weaviate index
        search_params = {"query": f"""
        {{
            Get {{
                ResearchArticle(
                    explore: {{nearText: {{query: "{query_terms}", certainty: 0.7}}}}
                    limit: 5
                ) {{
                    title
                    abstract
                    authors
                    citation
                }}
            }}
        }}"""}

        search_response = client.query.raw(query=json.dumps(search_params))
        articles = search_response['data']['Get']['ResearchArticle']

        # Check if there are any articles in Weaviate
        if articles:
            print("Articles in Weaviate:")
            for article in articles:
                print(
                    f"Title: {article['title']}, Authors: {article['authors']}, Citation: {article['citation']}")

            # Continue conversation with user
            continue
        else:
            # If there are no articles in Weaviate, fetch data from Pubmed and store in Weaviate
            fetched_content = search_and_fetch(query_terms)
            articles = parse_pubmed_xml(fetched_content, query_terms)
            for article in articles:
                client.data_object.create(
                    data_object=article, class_name="ResearchArticle")

            # Retrieve and present the new articles to the user
            search_response = client.query.raw(query=json.dumps(search_params))
            articles = search_response['data']['Get']['ResearchArticle']

            if articles:
                print("Articles fetched from Pubmed and stored in Weaviate:")
                for article in articles:
                    print(
                        f"Title: {article['title']}, Authors: {article['authors']}, Citation: {article['citation']}")
            else:
                print("No similar articles found in FAISS database.")
                print("Done.")
                break

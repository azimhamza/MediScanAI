import weaviate
import json

auth_config = weaviate.AuthApiKey(api_key='NvRXfGrL8Ci1Hb3CazufLMIM9s2l3q6SbSsx')

client = weaviate.Client("https://mediscanai-hi0v9ojp.weaviate.network", auth_client_secret=auth_config)

# Define the schema for the ResearchArticle
research_article_schema = {
    "class": "ResearchArticle",
    "description": "A research article from Pubmed",
    "properties": [
        {
            "name": "title",
            "description": "The title of the research article",
            "dataType": ["string"]
        },
        {
            "name": "abstract",
            "description": "The abstract of the research article",
            "dataType": ["string"]
        },
        {
            "name": "authors",
            "description": "The authors of the research article",
            "dataType": ["string"]
        },
        {
            "name": "citation",
            "description": "The citation of the research article",
            "dataType": ["string"]
        },
        {
            "name": "queryContext",
            "description": "The query terms used to retrieve the article",
            "dataType": ["string"]
        },
    ]
}


# Create the ResearchArticle class in Weaviate
client.schema.create_class(research_article_schema)

# Load data from JSON file
with open('articles.json') as f:
    data = json.load(f)

# Insert data into Weaviate
for article in data:
    client.data_object.create(data_object=article, class_name="ResearchArticle")


import os
from elasticsearch import Elasticsearch

ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL")

es_client = Elasticsearch(ELASTICSEARCH_URL)
import sys
import os
import datetime
from uuid import uuid4
from sentence_transformers import SentenceTransformer


model = SentenceTransformer('all-mpnet-base-v2')


def embeddings(query):
    vector = model.encode([query])[0].tolist()
    return vector
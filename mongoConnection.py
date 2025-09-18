from datetime import datetime

from pymongo import MongoClient

def get_collection():
    return collection

# --- Replace with your connection string ---
client = MongoClient("mongodb+srv://housing:YW7JqyAUMKRpYl40@beta-housing-edge.bcbqmns.mongodb.net/edge?retryWrites=true&w=majority")

# Access database (auto-created if not exists)
db = client["transcriptsDB"]

# Access collection (like a SQL table)
collection = db["calls"]

def insert_one(document):
    document["created_at"] = datetime.utcnow()
    document["updated_at"] = datetime.utcnow()
    collection.insert_one(document)

def insert_many(documents):
    collection.insert_many(documents)

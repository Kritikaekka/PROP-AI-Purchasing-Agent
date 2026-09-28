import os

from dotenv import load_dotenv
from pymongo import MongoClient


# Load variables from .env
load_dotenv()


# Get MongoDB connection string
MONGO_URI = os.getenv("MONGO_URI")

if not MONGO_URI:
    raise RuntimeError(
        "MONGO_URI is missing. Check your .env file."
    )


# Connect to MongoDB
client = MongoClient(MONGO_URI)


# Select PROP database
db = client["prop_db"]


# Collections
products_collection = db["products"]
stores_collection = db["stores"]
inventory_collection = db["inventory"]
sales_collection = db["sales_history"]
forecasts_collection = db["forecasts"]
suppliers_collection = db["suppliers"]
purchase_orders_collection = db["purchase_orders"]
transfers_collection = db["transfers"]
decisions_collection = db["agent_decisions"]


def test_connection():
    """
    Test whether MongoDB is reachable.
    """

    try:
        client.admin.command("ping")
        print("MongoDB connection successful!")
        return True

    except Exception as error:
        print("MongoDB connection failed:")
        print(error)
        return False
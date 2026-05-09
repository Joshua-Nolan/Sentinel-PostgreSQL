import os
import json
from pymongo import MongoClient
from dotenv import load_dotenv


class Data_handler:
    """ This is a class that will read in 1 or more JSONL files, and add them to a collection of a mongoDB database.
    """
    client = MongoClient("mongodb://localhost:27017")
    db = client["sentinel_ai"]
    collection = db['logs']

    LOG_FILE = r"../data/Logs/security_log.jsonl"

    def ingest_data(self):
        
        self.collection.drop() # THIS CLEARS THE ENTIRE DATASET COLLECTION ! 
        
    
        logs, logfiles = [], []
        logfiles.append(self.LOG_FILE)
        print(f"\nlog files to append: {logfiles}\n")
        for LOG in logfiles:
            with open(LOG, "r") as f:
                for line in f:
                    logs.append(json.loads(line.strip()))
                    
        result = self.collection.insert_many(logs)
        self.collection.create_index("timestamp")
        self.collection.create_index("event_type")
        self.collection.create_index("source_ip")       
        
        print("index created")        
        
def main():
    DH = Data_handler()
    DH.ingest_data()

    
if __name__ == "__main__":
    main()
    
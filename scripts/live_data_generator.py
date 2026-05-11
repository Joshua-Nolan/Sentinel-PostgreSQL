import os, uuid, json, time, random
from pymongo import MongoClient
from data_generator import DataGenerator as DG
from ingest_logs import Data_handler
from faker import Faker
from alert_pipeline import ThreatDetector

class Live_data_generator:
    
    def __init__(self):
        """
        This creates the constants needed from data_generator BUT 
        internalIPS and usernames will call the methods in data_generator. 
        This script will run infinitely but is only designed to be called from docker
        """
        
        self.fake = Faker() # instace of faker to create fake data
        self.OUTPUT_FOLDER = DG.OUTPUT_FOLDER
        self.OUTPUT_FILE = DG.OUTPUT_FILE
        self.INTERNAL_IPS = DG.INTERNAL_IPS
        self.NUM_logs = DG.NUM_logs
        self.MALICIOUS_IPS = DG.MALICIOUS_IPS
        self.USERNAMES = DG.USERNAMES
        self.HOSTS = DG.HOSTS
        
        print(self.USERNAMES)
        

    ## while forever, kills when docket kills it 
    ## generate data with the weighted scores
    ## write the data to mongoDB
    # i dont think create index?
    ## needs retry loop to check mongoDB is live
def main():
    
    connected = False
    while not connected:
        try:
            client = MongoClient("mongodb://mongoDB:27017")
            client.admin.command("ping")  # actually tests the connection
            print("Connected to MongoDB successfully")
            connected = True
        except Exception as e:
            print(f"MongoDB not ready, retrying in 3 seconds... ({e})")
            time.sleep(3)
    
    
    data_generator = DG()
    Llive_Data_Gernerator = Live_data_generator()
    data_handler = Data_handler()
    Threat_Detector = ThreatDetector()
    print("\n\nData stream starting\n\n")

    EVENT_GENERATORS = [
        (data_generator.successful_login_attempt, 40),       # 40% of logs
        (data_generator.failed_login_attempt, 25),           # 25%
        (data_generator.file_access, 15),            # 15%
        (data_generator.powershell_execution, 10),   # 10%
        (data_generator.suspicious_download, 4),     # 4%
        (data_generator.port_scan, 3),               # 3%
        (data_generator.malware_alert, 2),           # 2%
        (data_generator.privilege_escalation, 1),    # 1%
    ]
    
    if not os.path.exists(data_generator.OUTPUT_FOLDER):
        os.makedirs(data_generator.OUTPUT_FOLDER)
        print(f'Generating {data_generator.NUM_logs} at {data_generator.OUTPUT_FILE}')

        with open(data_generator.OUTPUT_FILE, "w") as f:
            for i in range(data_generator.NUM_logs):
                method = data_generator.weighted_choice(EVENT_GENERATORS)
                log = method()
                log["log_ID"] = str(uuid.uuid4())
                f.write(json.dumps(log)+ "\n")
        
    data_handler.ingest_data() # ingests data logs into mongoDB
    
    
    
    ## creates alerts and creats collection for them - should return info needed for me to later insertr a new data alert into that collection
    db, alerts_collection = Threat_Detector.run()
    
    
    while True:
        time.sleep(30)
        method = data_generator.weighted_choice(EVENT_GENERATORS)
        data = json.loads(json.dumps(method())) ## return a JSON python object
        ## write to the collection for alerts
        result = alerts_collection.insert_one(data)
        if not result.acknowledged:
            print(f'{result.acknowledged} | error in writing to alerts collection') 
            return
        print(result)    
        
        # with alerts_collection.watch() as changes:
        #     for change in changes:
        #         print(f'change found: {change}')
    
    
    
if __name__ == "__main__":
    main()
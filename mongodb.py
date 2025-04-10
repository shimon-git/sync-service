from pymongo import MongoClient
import urllib.parse

class Mongodb():
    def __init__(self, mongodb_conf):
        self.required_conf = ["host", "port", "username", "password", "db", "collection"]
        self.load_config(mongodb_conf)
        self.client = None
        self.db_ref = None
        self.collection_ref = None
        self.required_fields = ["esxi_host_addr", "name", "hostname", "addr", "uuid", "power_state", "vmware_tools", "orphan", "orphan_since", "last_sync_time"]
        self.connect()

    def load_config(self, mongodb_conf):
        for conf in self.required_conf:
            if conf not in mongodb_conf or not mongodb_conf.get(conf, None):
                raise ValueError(f"Missing required configurations in mongodb: mongodb.{conf}")
            setattr(self, conf, mongodb_conf.get(conf))            

        

    def connect(self):
        encoded_username = urllib.parse.quote_plus(self.username)
        encoded_password = urllib.parse.quote_plus(self.password)
        connection_string = f"mongodb://{encoded_username}:{encoded_password}@{self.host}:{self.port}"
        self.client = MongoClient(connection_string) # Connect into mongodb
        self.db_ref = self.client[self.db] # Use the desired db
        self.collection_ref = self.db_ref[self.collection] # Use the desired collection
    
    def disconnect(self):
        if self.client is not None:
            self.client.close()


    ##############################
    #            CRUD            #
    ##############################

    async def create(self, data):
        # Validate required fields
        if not all(field in data for field in self.required_fields):
            print("[WARN] Missing required fields in VM data.")
            return False

        vm_uuid = data.get("uuid")
        vm_name = data.get("name")

        if not vm_uuid or vm_uuid == "N/A":
            vm_uuid = None

        if not vm_name and not vm_uuid:
            print("[ERROR] Missing both UUID and name. Cannot insert.")
            return False

        # Check for existing VM by UUID or name
        existing_vm = await self.get(uuid=vm_uuid) if vm_uuid else await self.get(name=vm_name)

        if existing_vm:
            print(f"[INFO] VM already exists in DB: {vm_name} ({vm_uuid})")
            return False

        # Insert if not exists
        return self.collection_ref.insert_one(data).acknowledged

    
    async def get(self, uuid=None, name=None):
        if not uuid and not name:
            return None
        query_filter = {"name": name} if name else {"uuid": uuid}
        return self.collection_ref.find_one(query_filter)

    async def update(self, data):
        for field in self.required_fields:
            if field not in data:
                print("XXX")
                return False
        query_filter = {"uuid": data.get("uuid")} if data.get("uuid") != "N/A" else {"name": data.get("name")}
        update_operation = {"$set": data}
        return self.collection_ref.update_one(query_filter, update_operation).acknowledged
        
    async def delete(self, data):
        if "uuid" or "name" not in data:
            print("XXX")
            return False
        query_filter = {"uuid": data.get("uuid")} if data.get("uuid") != "N/A" else {"name": data.get("name")}
        return self.collection_ref.delete_one(query_filter).acknowledged



    async def get_all_vms_per_host(self, host_addr):
        if not host_addr:
            return []
        query_filter = {"esxi_host_addr": host_addr}
        return self.collection_ref.find(query_filter)
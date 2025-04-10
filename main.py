from sync import Sync
from mongodb import Mongodb
from server import APIServer
import yaml
import threading
import os
import concurrent.futures
import time
import asyncio


###############################
#          GLOBAL VARS        #
###############################
CONFIG_FILE = os.getenv("CONFIG_FILE", "sync.yaml") # Get the config file from env var name 'CONFIG_FILE' default config file path is'./sync.yaml'
SYNC_IN_PROCESS = False # Flag for sync in process, while sync in process this flag will be 'True' 
FORCE_SYNC_EVENT = threading.Event() # Signal for event triggering

###############################
#          LOAD CONF          #
###############################
# Load config file and return it as a parsed yaml
def load_config():
    with open(CONFIG_FILE, "r") as file:
        return yaml.safe_load(file)

###############################
#      Create Instances       #
###############################
# Create esxi instance which can be later will used for syncing -> return a list of esxi instances
def create_esxi_instances(esxi_conf, mongodb_instance, redis_conf, endpoints):
    sync_instances = []

    for esxi_host in range(len(esxi_conf)):
        sync_instances.append(
            Sync(esxi_conf[esxi_host], mongodb_instance, redis_conf, endpoints)
        )

    return sync_instances

# Create a mongodb instance
def create_mongodb_instance(mongodb_conf):
    return Mongodb(mongodb_conf)

# Create API server instance
def create_api_instance(api_conf, sync_instances):
    return APIServer(
        api_conf,
        sync_status_getter=lambda: SYNC_IN_PROCESS,
        force_sync_trigger=lambda: FORCE_SYNC_EVENT.set(),
        sync_instances=sync_instances
    )

###############################
#          Sync Runner        #
###############################
def perform_sync(sync_instances):
    for instance in sync_instances:
        print(f"[INFO] Syncing with ESXi host: {instance.host}")
        try:
            result = asyncio.run(instance.sync_vms())
            print(f"[SYNC RESULT] {instance.host} → {result}")
        except Exception as e:
            print(f"[ERROR] Failed to sync with {instance.host}: {e}")

def run(sync_instances, interval, timeout):
    global SYNC_IN_PROCESS
    executor = concurrent.futures.ThreadPoolExecutor(max_workers=1)
    
    while True:
        # Wait for the interval or force sync trigger
        FORCE_SYNC_EVENT.wait(timeout=interval)
        print(f"[INFO] Starting sync... (triggered manually or interval={interval}s)")
        
        SYNC_IN_PROCESS = True
        start_time = time.time()
        print("🔁 Syncing...")
        try:
            future = executor.submit(perform_sync, sync_instances)
            future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            print(f"[TIMEOUT] Sync exceeded {timeout} seconds. Operation canceled.")
        except Exception as e:
            print(f"[ERROR] Unexpected error during sync: {e}")
        finally:
            SYNC_IN_PROCESS = False
            FORCE_SYNC_EVENT.clear()
            elapsed = round(time.time() - start_time, 2)
            print(f"[INFO] Sync completed or aborted. Duration: {elapsed}s\n")


def main():
    try:
        config = load_config()
        mongodb_instance = create_mongodb_instance(config['mongodb'])
        sync_instances = create_esxi_instances(config['esxi_hosts'], mongodb_instance, config["redis"] ,config["endpoints"])
        api_instance = create_api_instance(config['api_server'], sync_instances)
        interval = config['sync']['interval']
        timeout = config['sync']['timeout']

        print(f"[INIT] Loaded {len(sync_instances)} ESXi hosts for sync.")
        print(f"[INIT] Sync interval set to {interval} seconds.")


        # Start the run function in a separate thread
        sync_thread = threading.Thread(
            target=run,
            args=(sync_instances, interval, timeout),
            daemon=True  # Automatically stops when main thread exits
        )

        sync_thread.start()
        api_instance.run()
    except Exception as e:
        print(f"[FATAL] Failed to start sync service: {e}")


if __name__ == "__main__":
    main()
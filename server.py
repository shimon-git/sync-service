from fastapi import FastAPI
from pydantic import BaseModel
from typing import List
from fastapi.responses import JSONResponse
import uvicorn

class SyncStatus(BaseModel):
    sync_in_process: bool

class SyncVMs(BaseModel):
    vms: List[str]

class APIServer:
    def __init__(self, server_conf, sync_status_getter, force_sync_trigger, sync_instances):
        """
        param:
            host: IP address to listen on
            port: port number to listen on
            sync_status_getter: A callable function that returns the value of SYNC_IN_PROCESS
            force_sync_trigger: A callable function that trigger a forced sync
        """
        self.required_conf = ["host", "port"]
        self.load_config(server_conf)
        self.sync_status_getter = sync_status_getter
        self.force_sync_trigger = force_sync_trigger
        self.app = FastAPI()
        self.sync_instances = sync_instances
        self.register_routes()


    def make_response(self, ok, message, **kwargs):
        response = {"ok": ok, "message": message,}
        response.update(kwargs)
        return JSONResponse(content=response)


    def load_config(self, server_conf):
        for conf in self.required_conf:
            if conf not in server_conf or not server_conf.get(conf, None):
                raise ValueError(f"Missing required configurations in api server: {conf}")
            setattr(self, conf, server_conf.get(conf))            

    def register_routes(self):
        @self.app.get("/sync/status", response_model=SyncStatus)
        async def get_sync_status():
            return self.make_response(
                ok=True,
                message=f"Sync status checked successfully",
                data=SyncStatus(sync_in_process=self.sync_status_getter()).dict()
            ) 
        
        @self.app.get("/sync/now")
        def force_sync():
            status = None
            
            if self.sync_status_getter():
                status = "already syncing"
            
            self.force_sync_trigger()
            
            status =  "sync triggered"
            
            return self.make_response(
                ok= (status == "sync triggered"),
                message=status
            )
        
        @self.app.post("/sync/vms")
        async def sync_vms(payload: SyncVMs):
            status = None
            results = []
            
            if self.sync_status_getter():
                status = "already syncing"
            
            if not status:
                status =  "sync triggered"
                for sync in self.sync_instances:
                    result = await sync.sync_selected_vms(payload.vms)
                results.append({sync.host: result})

            
            return self.make_response(
                ok=(status != "already syncing"),
                message=status,
                data=results
            )

    
    def run(self):
        uvicorn.run(self.app, host=self.host, port=self.port)
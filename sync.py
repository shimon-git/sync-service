from pyVim.connect import SmartConnect, Disconnect
from pyVmomi import vim
import ssl
from datetime import datetime
import socket
from typing import List
import httpx
import asyncio

class Sync:
    def __init__(self, esxi_conf, mongodb_instance, redis_instance, endpoints):
        self.required_conf = ["host", "port", "username", "password"]
        self.required_endpoints = ["vm-group-service-rename-vm", "auth-service-rename-vm"]
        self.load_config(esxi_conf)
        self.load_endpoints(endpoints)
        self.context = ssl._create_unverified_context() # Disable SSL cert warnings (for self-signed ESXi certs)
        self.mongo = mongodb_instance
        self.redis = redis_instance
        self.endpoints = endpoints

    def load_config(self, esxi_conf):
        for conf in self.required_conf:
            if conf not in esxi_conf or not esxi_conf.get(conf, None):
                raise ValueError(f"Missing required configurations in esxi host under esxi_hosts configurations: {conf}")
            setattr(self, conf, esxi_conf.get(conf))

    def load_endpoints(self, endpoints):
        for endpoint in self.required_endpoints:
            if endpoint not in endpoints or not endpoints.get(endpoint):
                raise ValueError(f"Missing required configurations: endpoints.{endpoint}")
            setattr(self, endpoint, endpoints.get(endpoint).replace("-", "_"))
                


    
    def get_service_instance(self):
        try:
            return SmartConnect(
                host=self.host,
                port=self.port,
                user=self.username,
                pwd=self.password,
                sslContext=self.context
            )
        except vim.fault.InvalidLogin as e:
            print(f"[AUTH ERROR] Invalid credentials for {self.host}: {e}")
        except socket.timeout as e:
            print(f"[TIMEOUT] Connection timed out for {self.host}: {e}")
        except (socket.error, ConnectionRefusedError) as e:
            print(f"[NETWORK ERROR] Cannot reach {self.host}: {e}")
        except Exception as e:
            print(f"[UNKNOWN ERROR] Error connecting to {self.host}: {e}")
        
    def time_gen(self):
        return datetime.now().strftime("%d-%m-%Y: %H:%M:%S")
    

    async def rename_handler(self, renamed_vms):
        await self.redis.rename_vm_in_sessions(renamed_vms)
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            tasks = []

            # Call to VM Group Service
            try:
                tasks.append(client.post(
                    self.vm_group_service_rename_vm,
                    json={"vms": renamed_vms}
                ))
            except Exception as e:
                print(f"[ERROR] Failed to call VM Group rename service: {e}")

            # Individual calls to Auth Service
            for rename_vm in renamed_vms:
                try:
                    tasks.append(client.post(
                        self.auth_service_rename_vm,
                        json={"name": rename_vm.get("old_name"), "new_name": rename_vm.get("new_name")}
                    ))
                except Exception as e:
                    print(f"[ERROR] Failed to call VM Group rename service: {e}")

        # Handle responses
        try:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            for idx, res in enumerate(results):
                if isinstance(res, Exception):
                    print(f"[ERROR] Rename service #{idx+1} failed: {res}")
                elif res.status_code != 200:
                    print(f"[WARN] Rename service #{idx+1} responded with {res.status_code}: {res.text}")
                else:
                    print(f"[INFO] Rename service #{idx+1} succeeded: {res.json()}")
        except Exception as e:
            print(f"[FATAL] Unexpected error during rename service calls: {e}")

    
    def compare_changes(self, db_vm, esxi_vm):
        result = esxi_vm.copy()
        final_result = {}
        # Inherit hostname/addr if ESXi returned 'unknown'
        for field in {"hostname", "addr"}:
            if result[field] == "unknown":
                result[field] = db_vm.get(field, "unknown")

        final_result.update({"result": result})

        # Detect name change
        old_name = db_vm.get("name")
        new_name = result.get("name")

        if old_name != new_name:
            
            print(f"[RENAME DETECTED] VM UUID '{db_vm.get('uuid')}' renamed from '{old_name}' to '{new_name}'")
            final_result.update({"rename": {"old_name": old_name, "new_name": new_name}})

        return final_result


        


    def vm_struct(self, name, hostname, addr, uuid, power_state, vmware_tools, orphan=False, orphan_since=None):
        return {
            "esxi_host_addr": self.host,
            "name": name,
            "hostname": hostname,
            "addr": addr,
            "uuid": uuid,
            "power_state": power_state,
            "vmware_tools": vmware_tools,
            "orphan": orphan,
            "orphan_since": orphan_since,
            "last_sync_time": self.time_gen()
        }

    def get_esxi_vm_list(self):
        output = []

        # Connect to ESXi
        service_instance = self.get_service_instance()
        if not service_instance: return []
        
        try:
            # Retrieve the content
            content = service_instance.RetrieveContent()

            # Get all VMs
            container = content.viewManager.CreateContainerView(
                content.rootFolder,
                [vim.VirtualMachine],
                True
            )
            vms = container.view

            # Iterate through the VMs in order to get their state and UUIDs
            for vm in vms:
                if not vm.config:
                    print(f"[WARN] VM {vm.name} has no config.")
                    continue

                try:
                    if vm and vm.config:
                        uuid = vm.config.uuid
                    else:
                        continue
                except AttributeError:
                    print(f"VM {vm.name} has no UUID attribute!")
                    uuid = "N/A"
                    continue
                
                vm_data = self.vm_struct(
                    name=vm.name,
                    hostname=vm.guest.hostName if vm.guest and vm.guest.hostName else "unknown",
                    addr=vm.guest.ipAddress if vm.guest and vm.guest.ipAddress else "unknown",
                    uuid=uuid,
                    power_state='on' if vm.runtime.powerState == "poweredOn" else "off" if vm.runtime.powerState == "poweredOff" else vm.runtime.powerState,
                    vmware_tools=str(vm.guest.toolsStatus) if vm.guest else "unknown"
                )
                output.append(vm_data)

        except Exception as e:
            print(f"[ERROR] Failed to retrieve VMs from {self.host}: {e}")
        finally:
            if service_instance: Disconnect(service_instance)
        return output
    

    async def compare_vms_against_db(self, esxi_vms):
        db_vms = await self.mongo.get_all_vms_per_host(self.host)
        orphans = []
        vms_to_add = []
        vms_to_update = []
        

        # Create dictionaries for fast access by UUID
        db_vm_dict = {vm.get("uuid"): vm for vm in db_vms if vm.get("uuid")}
        esxi_vm_dict = {vm.get("uuid"): vm for vm in esxi_vms if vm.get("uuid")}

        db_vms_uuids = set(db_vm_dict.keys())
        esxi_vms_uuids = set(esxi_vm_dict.keys())


        # Orphans: in DB but not on host anymore
        orphan_uuids = db_vms_uuids - esxi_vms_uuids
        orphans = [db_vm_dict[uuid] for uuid in orphan_uuids]
        orphan_data = [{"name": vm.get("name"), "orphan_since": vm.get("orphan_since")} for vm in orphans if vm.get("name")]
        
        # To Add: in ESXi but not in DB
        add_uuids = esxi_vms_uuids - db_vms_uuids
        vms_to_add = [esxi_vm_dict[uuid] for uuid in add_uuids]

        # To Update: exists in both, but may have differences
        common_uuids = db_vms_uuids & esxi_vms_uuids
        vms_to_update = [esxi_vm_dict[uuid] for uuid in common_uuids]

        # Update sessions with orphans vms
        if len(orphan_data) > 0:
            await self.redis.update_orphans_in_sessions(orphan_data)

        return {
            "orphans": orphans,
            "add": vms_to_add,
            "update": vms_to_update,
        }
    

    async def sync_vms(self):
        esxi_vms = self.get_esxi_vm_list()
        ok = True
        reactivated_vms = []
        renamed_vms = []
        successfully_added = 0
        successfully_orphaned = 0
        successfully_updated = 0
        added_failures = 0
        updated_failures = 0
        orphaned_failures = 0
        
        if not esxi_vms:
            return {"ok": not ok, "added": 0, "updated": 0, "orphaned": 0}
        
        data_to_sync = await self.compare_vms_against_db(esxi_vms)

        # Create
        for vm in data_to_sync.get("add", []):
            created = await self.mongo.create(vm)
            if not created:
                added_failures+=1
                print(f"[ERROR] Failed to create a new vm {vm} in the DB.")
                ok = False
            else:
                successfully_added+=1
        
        # Orphans
        for vm in data_to_sync.get("orphans", []):
            if not vm.get("orphan", False):
                vm["orphan"] = True
                vm["orphan_since"] = self.time_gen()
            
            vm["last_sync_time"] = self.time_gen()
            updated = await self.mongo.update(vm)
            if not updated:
                orphaned_failures+=1
                print(f"[ERROR] Failed to update an orphaned vm {vm} in the DB.")
                ok = False
            else:
                successfully_orphaned+=1

        
        # update
        for vm in data_to_sync.get("update", []):
            vm_uuid = vm.get("uuid", None)
            vm_name = vm.get("name", None)
            if not vm_uuid or vm_uuid == "N/A" and not vm_name:
                updated_failures+=1
                print(f"[ERROR] Cannot update vm in db because the following vms attributes are missing: ['name', 'uuid'] - vm details: {vm}")
                ok = False
                continue
            
            db_vm = await self.mongo.get(uuid=vm_uuid, name=vm_name)


            compare_results = self.compare_changes(db_vm=db_vm, esxi_vm=vm)
            renamed = compare_results.get("rename")
            updated_vm = compare_results.get("result")

            if renamed:
                renamed_vms.append(renamed)
            

            # ✅ Check for reactivation
            if db_vm.get("orphan") is True:
                updated_vm["orphan"] = False
                updated_vm["orphan_since"] = None
                reactivated_vms.append(updated_vm.get("name"))


            updated = await self.mongo.update(updated_vm)
            if not updated:
                updated_failures+=1
                print(f"[ERROR] Failed to update an orphaned vm {vm} in the DB.")
                ok = False
            else:
                successfully_updated+=1


        # Call here handle reactivation function
        if reactivated_vms:
            await self.redis.move_vms_from_orphans_to_vms(reactivated_vms)

        #Call here handle reactivation function
        if renamed_vms:
            await self.rename_handler(renamed_vms)

        return {
            "ok": ok,
            "added": successfully_added,
            "updated": successfully_updated,
            "orphaned": successfully_orphaned,
            "added_failures": added_failures,
            "updated_failures": updated_failures,
            "orphaned_failures": orphaned_failures,
            "reactivated": reactivated_vms,
            "renamed": renamed_vms
        }
    
    async def sync_selected_vms(self, vm_ids: List[str]):
        esxi_vms = self.get_esxi_vm_list()
        selected_vms = [vm for vm in esxi_vms if vm["uuid"] in vm_ids or vm["name"] in vm_ids]
        if not selected_vms:
            return {"ok": True, "matched": 0, "synced": 0}
        added = updated = failed = 0
        for vm in selected_vms:
            db_vm = await self.mongo.get(uuid=vm["uuid"], name=vm["name"])
            if db_vm:
                updated_vm = self.compare_changes(db_vm=db_vm, esxi_vm=vm).get("result")
                success = await self.mongo.update(updated_vm)
                if success:
                    updated+=1
                else:
                    failed += 1
            else:
                success = await self.mongo.create(vm)
                if success:
                    added += 1
                else:
                    failed += 1

        return {
            "ok": failed == 0,
            "host": self.host,
            "matched": len(selected_vms),
            "added": added,
            "updated": updated,
            "failed": failed
        }
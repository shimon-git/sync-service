import redis.asyncio as redis
import json
import string
import random


class RedisClient():
    def __init__(self, redis_conf):
        self.required_conf = [
            "host",
            "port",
            "session_time"
        ]
        self.check_conf(redis_conf)
        self.connect()


    ###################################
    #               CURD              # 
    ###################################
    async def update(self, key, value):
        ttl = await self.client.ttl(key)
        value = self.serializer(value)
        return await self.client.setex(key, ttl, value)
    
    async def get(self, key):
        value = await self.client.get(key)
        return self.deserializer(value)


    ###################################
    #               Utils             #
    ###################################

    def check_conf(self, redis_conf):
        for conf in self.required_conf:
            if conf not in redis_conf:
                raise ValueError(f"Missing required configuration for redis service: redis.{conf}")
            setattr(self, conf, redis_conf[conf])

    def connect(self):
        self.client = redis.Redis(
            host=self.host,
            port=self.port,
            db=0,
            decode_responses=True
        )


    def serializer(self, value):
        if type(value) is dict:
            return json.dumps(value)
        return value
    
    def deserializer(self, value):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value

    
    async def get_all_sessions(self):
        cursor = 0
        sessions = []

        while True:
            cursor, keys = await self.client.scan(
                cursor=cursor,
                match="*",
                count=100
            )

            sessions.extend(keys)

            if cursor == 0:
                break
        
        return sessions
    

    async def update_orphans_in_sessions(self, orphan_data):
        sessions = await self.get_all_sessions()
        updated_sessions = 0

        new_orphan_names = {vm["name"] for vm in orphan_data if vm.get("name")}

        for session in sessions:
            session_data = await self.get(session)
            if not isinstance(session_data, dict):
                continue

            allowed_vms = set(session_data.get("vms", []))
            current_orphans = set(session_data.get("orphans", []))

            current_orphan_names = {o["name"] for o in current_orphans if isinstance(o, dict) and o.get("name")}

            orphan_to_add = allowed_vms & new_orphan_names

            if not orphan_to_add:
                continue

            session_data["vms"] = list(allowed_vms - orphan_to_add)

            for orphan_vm in orphan_data:
                name = orphan_vm.get("name")
                if name in orphan_to_add and name not in current_orphan_names:
                    current_orphans.append(orphan_vm)
            
            session_data["orphans"] = current_orphans



            await self.update(session, session_data)
            updated_sessions += 1

        return {
            "ok": True,
            "message": "Orphan VMs updated in active Redis sessions.",
            "affected_sessions": updated_sessions
        }
    
    async def move_vms_from_orphans_to_vms(self, reactivated_vms):
        sessions = await self.get_all_sessions()
        updated_sessions = 0

        for session in sessions:
            session_data = self.get(session)
            if not isinstance(session_data, dict):
                continue

            allowed_vms = set(session_data.get("vms", []))
            current_orphans = set(session_data.get("orphans", []))

            # Determine which of the allowed vms are now online
            new_online = current_orphans & set(reactivated_vms)
            if new_online:
                # Remove them from 'orphans' and add to 'vms'
                session_data["vms"] = list(allowed_vms + new_online)
                session_data["orphans"] = list(current_orphans - new_online)

                await self.update(session, session_data)
                updated_sessions += 1

        return {
            "ok": True,
            "message": "Online VMs updated in active Redis sessions.",
            "affected_sessions": updated_sessions
        }
    
    
    async def rename_vm_in_sessions(self, renamed_vms):
        sessions = await self.get_all_sessions()
        updated_sessions = 0
        renamed_pairs = []

        for session in sessions:
            session_data = await self.get(session)
            if not isinstance(session_data, dict):
                continue

            changed = False

            
            vms = set(session_data.get("vms", []))
            orphans = set(session_data.get("orphans", []))
            
            #  and orphans list
            for vm in renamed_vms:
                old_name = vm.get("old_name")
                new_name = vm.get("new_name")
                
                # Update in vms list
                if old_name in vms:
                    vms.remove(old_name)
                    vms.add(new_name)
                    session_data["vms"] = list(vms)
                    changed = True

                # Update in orphans list
                if old_name in orphans:
                    orphans.remove(old_name)
                    orphans.add(new_name)
                    session_data["orphans"] = list(orphans)
                    changed = True

            if changed:
                await self.update(session, session_data)
                renamed_pairs.append({"old_name": old_name, "new_name": new_name})
                updated_sessions += 1



        return {
            "ok": True,
            "message": f"VM name updated in sessions from '{old_name}' to '{new_name}'.",
            "affected_sessions": updated_sessions,
            "renamed": renamed_pairs
        }
#!/usr/bin/env python3
import requests
import json
import time
import sys
import os
import logging
from enum import Enum
from dataclasses import dataclass
from typing import Optional

@dataclass
class ClientEntry:
    owner: str
    mac: Optional[str] = None
    ip: Optional[str] = None
    hostname: Optional[str] = None
    notify: Optional[list[str]] = None

@dataclass
class Config:
    url: str
    cert_path: str
    interval: int
    api_key: str
    api_secret: str
    clients: list[ClientEntry]

def read_api_key(path: str) -> (str, str):
    with open(path, "r") as fd:
        key_raw = fd.readline()
        secret_raw = fd.readline()
        return (key_raw.split("=")[1].strip(), secret_raw.split("=")[1].strip())

def main():
    log_level = int(os.environ["LOG_LEVEL"]) if "LOG_LEVEL" in os.environ else logging.INFO
    logging.getLogger().setLevel(log_level)
    # Setup
    with open("config.json") as fd:
        config = Config(**json.load(fd))

    config.clients = list(map(lambda x: ClientEntry(**x), config.clients))

    os.environ["REQUESTS_CA_BUNDLE"] = config.cert_path
    s = requests.Session()
    s.auth = (config.api_key, config.api_secret)

    logging.info("Loaded config successfully")

    # Main Loop 

    # map of user to online status
    all_users: set[str] = set()
    for c in config.clients:
        all_users.add(c.owner)

    online_users: set[str] = None

    while True:

        r = s.post(f"{config.url}/api/dhcpv4/leases/searchLease/", json={
                "current": 1,
                "inactive": False,
                "rowCount": -1,
                "searchPhrase": "",
                "selected_interfaces": [],
                "sort": {}
            },
            verify=False
        )

        if r.status_code != 200:
            logging.warn(f"Failed to get device list: {r.status_code}")
            continue

        logging.info(f"Completed request in {r.elapsed}")

        data = r.json()

        new_online_users = set()

        logging.debug(f"{len(data['rows'])} entries in response")
        for r in data["rows"]:
            hostname = r["client-hostname"] if "client-hostname" in r else None
            ip = r["address"]
            mac = r["mac"]
            is_online = r["status"] == "online"
            logging.debug(f"{hostname=} {ip=} {mac=} {is_online=}")
            
            for entry in config.clients:
                if (entry.hostname == hostname or entry.ip == ip or entry.mac == mac) and is_online:
                    # matched an online device, add to the set of online users.
                    logging.debug(f"user {entry.owner} is online")
                    new_online_users.add(entry.owner)
                    
        if online_users is not None:
            # Compare old status and new status            
            for user in all_users:
                
                if user in new_online_users and user not in online_users:
                    # Transition to online
                    logging.info(f"{user} transition to online")

                if user in online_users and user not in new_online_users:
                    # Transition to offline
                    logging.info(f"{user} transition to offline")

        user_status = new_online_users
        time.sleep(config.interval)


if __name__ == "__main__":
    sys.exit(main())

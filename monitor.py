#!/usr/bin/env python3
import requests
import json
import time
import sys
import os
import logging
import datetime
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
    interval: int
    api_key: str
    api_secret: str
    clients: list[ClientEntry]
    template: str = "%U went %S at %T"
    ntfy_url: Optional[str] = None
    ntfy_token: Optional[str] = None
    discord_webhook_url: Optional[str] = None
    test_mode: bool = False    

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
            logging.warning(f"Failed to get device list: {r.status_code}")
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
                    logging.debug(f"{user} transition to online")
                    transition(user, True, config)

                if user in online_users and user not in new_online_users:
                    # Transition to offline
                    logging.debug(f"{user} transition to offline")
                    transition(user, False, config)


        if config.test_mode:
            transition("test", False, config)

        online_users = new_online_users
        time.sleep(config.interval)


def format_template(template: str, user: str, online: bool):
    return template.replace("%U", user).replace("%S", "online" if online else "offline").replace("%T", datetime.datetime.now().isoformat())


def transition(user: str, into_online: bool, config: Config): 
    logging.debug(f"{user} {into_online=}")
    content = format_template(config.template, user, into_online)
    if config.ntfy_url is not None:
        # ntfy
        r = requests.post(config.ntfy_url, headers={
                "Authorization": f"Bearer {config.ntfy_token}"
            },
            data=content
        )
        if r.status_code != 200:
            logging.warning(f"Failed to send ntfy notification: {r.status_code}: [{r.content.decode('utf-8')}]")
    elif config.discord_webhook_url is not None:
        # discord
        
        r = requests.post(config.discord_webhook_url, json={
            "content": content
        })
        if r.status_code != 200:
            logging.warning(f"Failed to send discord webhook: {r.status_code}")
    else: 
        # no notif configured
        logging.warning("No notification system configured")


if __name__ == "__main__":
    sys.exit(main())

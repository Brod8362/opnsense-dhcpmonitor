# OPNsense DHCP monitor

Monitors the OPNsense built-in DHCP server and notifies as devices go on/offline.

# Installation

## OPNsense

1. Create a new user in `System > Access > Users`, with the default permission level.
2. Edit the user (which should have no permissions) and add the "Status: DHCP leases" permission
3. Generate an API key for the user, which will prompt you to download a file.
4. Set the API key and secret parameters in the config.

## Docker

```sh
git clone https://github.com/Brod8362/opnsense-dhcpmonitor
cd opnsense-dhcpmonitor
docker build -t dhcpmon .
# Modify me at your whimsy. Make sure to actually make the config file
docker run -v $(pwd)/config.json:/app/config.json dhcpmon .
```

# Config

See example config below. Name this file `config.json`.

```json
{
    "url": "https://opnsense.lan",
    "api_key": "<snip>",
    "api_secret": "<snip>",
    "interval": 60,
    "clients": [
        {
            "owner": "mom",
            "mac": "aa:bb:cc:dd:ee:ff"
        },
        {
            "owner": "dad",
            "hostname": "Dads-iPhone"
        },
        {
            "owner": "smelvin",
            "ip": "192.168.1.5"
        }
    ]
}
```

# OPNsense DHCP monitor

Monitors the OPNsense built-in DHCP server and notifies as devices go on/offline.

# Installation

<tbd>

# Config

See example config below.

```json
{
    "url": "https://opnsense.lan",
    "cert_path": "./cert.pem",
    "api_key": "<snip>",
    "api_secret": "<snip>",
    "interval": 15,
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

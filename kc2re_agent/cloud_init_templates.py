import crypt
import yaml
from typing import cast, Any

UEC_HTTP_PROXY_URL = "http://proxy.uec.ac.jp:8080"
UEC_SOCKS_PROXY_URL = "socks5://socks.cc.uec.ac.jp:1080"
TRANSOCKS_TOML = f"""
proxy_url = "{UEC_SOCKS_PROXY_URL}"
"""
TRANSOCKS_SERVICE = """
[Unit]
Description=transocks: Transparent SOCKS5 proxy
Documentation=https://github.com/cybozu-go/transocks
After=network.target

[Service]
ExecStart=/usr/local/bin/transocks

[Install]
WantedBy=multi-user.target
"""
UFW_BEFORE_RULES = """
*nat
-F
:PREROUTING ACCEPT [0:0]
:INPUT ACCEPT [0:0]
:OUTPUT ACCEPT [0:0]
:POSTROUTING ACCEPT [0:0]
:TRANSOCKS - [0:0]
-A OUTPUT -j TRANSOCKS
-A TRANSOCKS -d 0.0.0.0/8 -j RETURN
-A TRANSOCKS -d 10.0.0.0/8 -j RETURN
-A TRANSOCKS -d 127.0.0.0/8 -j RETURN
-A TRANSOCKS -d 169.254.0.0/16 -j RETURN
-A TRANSOCKS -d 172.16.0.0/12 -j RETURN
-A TRANSOCKS -d 192.168.0.0/16 -j RETURN
-A TRANSOCKS -d 224.0.0.0/4 -j RETURN
-A TRANSOCKS -d 240.0.0.0/4 -j RETURN
-A TRANSOCKS -d 130.153.0.0/16 -j RETURN
-A TRANSOCKS -p tcp -j REDIRECT --to-ports 1081
-A TRANSOCKS -p icmp -j REDIRECT --to-ports 1081
COMMIT
"""


def generate_cloud_init_userdata(
    default_user_name: str, default_user_raw_passwd: str
) -> dict[str, Any]:  # TODO: do not use Any
    hashed_default_user_passwd = crypt.crypt(default_user_raw_passwd)
    return {
        "system_info": {
            "default_user": {
                "name": default_user_name,
                "passwd": hashed_default_user_passwd,
                "lock_passwd": False,
            }
        },
        "ssh_pwauth": True,
        "bootcmd": [
            f"http_proxy={UEC_HTTP_PROXY_URL} https_proxy={UEC_HTTP_PROXY_URL} wget -l -P /usr/local/bin -O /usr/local/bin/transocks https://github.com/otariidae/transocks/releases/download/v1.1.1%2B2cf9915/transocks_x86_64",
            "chmod +x /usr/local/bin/transocks",
        ],
        "write_files": [
            {
                "content": TRANSOCKS_TOML,
                "path": "/etc/transocks.toml",
                "owner": "root:root",
                "permissions": "0644",
            },
            {
                "content": TRANSOCKS_SERVICE,
                "path": "/etc/systemd/system/transocks.service",
                "owner": "root:root",
                "permissions": "0644",
            },
            {
                "content": UFW_BEFORE_RULES,
                "path": "/etc/ufw/before.rules",
                "append": True,
                "owner": "root:root",
                "permissions": "0640",
            },
        ],
        "runcmd": [
            "systemctl daemon-reload",
            "systemctl enable transocks",
            "systemctl start transocks",
            "ufw enable",
            "ufw allow 22",
            "apt update",
            "apt install -y avahi-daemon",
            "systemctl enable avahi-daemon",
            "systemctl start avahi-daemon",
            "ufw allow 5353",
        ],
    }


def generate_cloud_init_userdata_string(
    default_user_name: str, default_user_raw_passwd: str
) -> str:
    userdata = generate_cloud_init_userdata(default_user_name, default_user_raw_passwd)
    return "#cloud-config\n" + cast(str, yaml.dump(userdata))

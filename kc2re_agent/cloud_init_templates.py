CLOUD_INIT_USERDATA = """
#cloud-config
system_info:
  default_user:
    name: {default_user_name}
    passwd: {hashed_default_user_password}
    lock_passwd: false
ssh_pwauth: true

bootcmd:
- http_proxy=http://proxy.uec.ac.jp:8080 https_proxy=http://proxy.uec.ac.jp:8080 wget -l -P /usr/local/bin -O /usr/local/bin/transocks https://github.com/otariidae/transocks/releases/download/v1.1.1/transocks
- chmod +x /usr/local/bin/transocks

write_files:
- content: |
    proxy_url = "socks5://socks.cc.uec.ac.jp:1080"
  path: /etc/transocks.toml
  owner: root:root
  permissions: '0644'
- content: |
    [Unit]
    Description=transocks: Transparent SOCKS5 proxy
    Documentation=https://github.com/cybozu-go/transocks
    After=network.target
    [Service]
    ExecStart=/usr/local/bin/transocks
    [Install]
    WantedBy=multi-user.target
  path: /etc/systemd/system/transocks.service
  owner: root:root
  permissions: '0644'
- content: |
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
  path: /etc/ufw/before.rules
  append: true
  owner: root:root
  perissions: '0640'

runcmd:
- systemctl daemon-reload
- systemctl enable transocks
- systemctl start transocks
- ufw enable
- ufw allow 22
- apt update
- apt install -y avahi-daemon
- systemctl enable avahi-daemon
- systemctl start avahi-daemon
- ufw allow 5353
"""

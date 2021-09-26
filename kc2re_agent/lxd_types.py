from typing import Optional, TypedDict

# https://github.com/lxc/lxd/blob/lxd-4.18/shared/api/instance_state.go#L145
class InstanceStateNetworkAddress(TypedDict):
    family: str
    address: str
    netmask: str
    scope: str


# https://github.com/lxc/lxd/blob/lxd-4.18/shared/api/instance_state.go#L169
class InstanceStateNetworkCounters(TypedDict):
    bytes_recieved: int
    bytes_sent: int
    packets_recieved: int
    packets_sent: int
    errors_recieved: int
    errors_sent: int
    packets_dropped_outbound: int
    packets_dropped_inbound: int


# https://github.com/lxc/lxd/blob/lxd-4.18/shared/api/instance_state.go#L111
class InstanceStateNetwork(TypedDict):
    addresses: list[InstanceStateNetworkAddress]
    counters: InstanceStateNetworkCounters
    hwaddr: str
    mtu: int
    state: str
    type: str


# InstancePost but some keys omitted
# https://github.com/lxc/lxd/blob/lxd-4.18/shared/api/instance.go#L236
class SimpleInstanceSource(TypedDict):
    type: str
    alias: str
    server: Optional[str]
    protocol: Optional[str]
    mode: Optional[str]


# InstancePost but some keys omitted
# https://github.com/lxc/lxd/blob/lxd-4.18/shared/api/instance.go#L24
class SimpleInstancePost(TypedDict):
    name: str
    source: SimpleInstanceSource
    config: dict[str, str]

import crypt
import json
import os
import socket
import urllib.parse
from typing import TypedDict, Union
from pylxd import Client  # type: ignore
from pylxd.models import Instance  # type: ignore
from websocket import WebSocketApp  # type: ignore
from functools import cache
from .simplestreams import SimpleStreamsClient, Product
from .lxd_types import InstanceStateNetwork, SimpleInstancePost
from .messages import (
    AdvertiseHostMessage,
    ImageInfo,
    InstanceInfo,
    InstanceInfoAddress,
    Message,
)
from .cloud_init_templates import CLOUD_INIT_USERDATA


CONTROL_PLANE_URI = os.environ.get("KC2_CONTROL_PLANE_URI", "ws://localhost:8000")
TOKEN = os.environ.get("KC2_CONTROL_PLANE_TOKEN", "")
HOSTNAME = os.environ.get("KC2_HOSTNAME", socket.gethostname())
UBUNTU_IMAGE_SERVER = "https://cloud-images.ubuntu.com/releases"


lxdclient = Client()
ssclient = SimpleStreamsClient(url=UBUNTU_IMAGE_SERVER)


def get_addresses(
    network: dict[str, InstanceStateNetwork]
) -> list[InstanceInfoAddress]:
    ipv4_addrs: list[InstanceInfoAddress] = []
    for interface in network.values():
        if interface["type"] == "loopback":
            continue
        for addr in interface["addresses"]:
            if addr["family"] != "inet":
                continue
            instanceAddr = InstanceInfoAddress(
                address=addr["address"], netmask=addr["netmask"]
            )
            ipv4_addrs.append(instanceAddr)
    return ipv4_addrs


def create_instance_info(instance: Instance) -> InstanceInfo:
    state = instance.state()
    addresses = get_addresses(state.network) if state.network is not None else []
    return {
        "name": instance.name,
        "status": instance.status,
        "addresses": addresses,
    }


def get_instances() -> list[InstanceInfo]:
    containers = lxdclient.containers.all()
    return list(map(create_instance_info, containers))


@cache
def get_suitable_images() -> list[ImageInfo]:
    products = ssclient.list_images()
    suitable_images: list[ImageInfo] = []
    for product in products:
        if product["arch"] != "amd64":
            continue
        aliases = product["aliases"].split(",")
        image_info = ImageInfo(
            aliases=aliases, os=product["os"], release=product["release_title"]
        )
        suitable_images.append(image_info)
    return suitable_images


def create_instance_post(
    name: str, username: str, password: str, alias: str
) -> SimpleInstancePost:
    hashed_password = crypt.crypt(password)
    return {
        "name": name,
        "config": {
            "user.user-data": CLOUD_INIT_USERDATA.format(
                default_user_name=username,
                hashed_default_user_password=hashed_password,
            )
        },
        "source": {
            "type": "image",
            "mode": "pull",
            "server": UBUNTU_IMAGE_SERVER,
            "protocol": "simplestreams",
            "alias": alias,
        },
    }


def create_advertise_host() -> AdvertiseHostMessage:
    return {
        "type": "ADVERTISE_HOST",
        "instances": get_instances(),
        "images": list(get_suitable_images()),
        "host": HOSTNAME,
    }


def on_open(ws: WebSocketApp) -> None:
    print("opened a connection")
    message = json.dumps(create_advertise_host())
    ws.send(message)


def on_message(ws: WebSocketApp, raw_message: str) -> None:
    print("recieved a message")
    message: Message = json.loads(raw_message)
    print(f"> {message}")
    if message["type"] == "QUERY_HOST":
        reply = json.dumps(create_advertise_host())
        ws.send(reply)
        return
    if (
        message["type"] == "COMMAND_START"
        or message["type"] == "COMMAND_STOP"
        or message["type"] == "COMMAND_RESTART"
        or message["type"] == "COMMAND_DESTROY"
        or message["type"] == "COMMAND_CREATE"
    ):
        if message["host"] != HOSTNAME:
            return
        if message["type"] == "COMMAND_CREATE":
            config = create_instance_post(
                name=message["name"],
                username=message["user"],
                password=message["password"],
                alias=message["alias"],
            )
            lxdclient.instances.create(config)
            return

        instance = lxdclient.instances.get(message["instance"])
        if instance is None:
            return
        if message["type"] == "COMMAND_START":
            instance.start()
            print("starting the instance")
            return
        if message["type"] == "COMMAND_STOP":
            instance.stop()
            print("stopping the instance")
            return
        if message["type"] == "COMMAND_RESTART":
            instance.restart()
            print("restarting the instance")
            return
        if message["type"] == "COMMAND_DESTROY":
            instance.delete()
            print("destroying the instance")
            return


def on_error(ws: WebSocketApp, exception: Exception) -> None:
    print("something went wrong")
    print(exception)


qs = urllib.parse.urlencode({"t": TOKEN})
print(f"tring to connect to {CONTROL_PLANE_URI}")

ws = WebSocketApp(
    CONTROL_PLANE_URI + "?" + qs,
    on_open=on_open,
    on_message=on_message,
    on_error=on_error,
)

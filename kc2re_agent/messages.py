from typing import Literal, TypedDict, Union


class InstanceInfoAddress(TypedDict):
    address: str
    netmask: str


class InstanceInfo(TypedDict):
    name: str
    status: str
    addresses: list[InstanceInfoAddress]


class ImageInfo(TypedDict):
    aliases: list[str]
    os: str
    release: str


class QueryHostMessage(TypedDict):
    type: Literal["QUERY_HOST"]


class CommandStartMessage(TypedDict):
    type: Literal["COMMAND_START"]
    host: str
    instance: str


class CommandStopMessage(TypedDict):
    type: Literal["COMMAND_STOP"]
    host: str
    instance: str


class CommandRestartMessage(TypedDict):
    type: Literal["COMMAND_RESTART"]
    host: str
    instance: str


class CommandDestroyMessage(TypedDict):
    type: Literal["COMMAND_DESTROY"]
    host: str
    instance: str


class CommandCreateMessage(TypedDict):
    type: Literal["COMMAND_CREATE"]
    host: str
    alias: str
    name: str
    user: str
    password: str


class AdvertiseHostMessage(TypedDict):
    type: Literal["ADVERTISE_HOST"]
    host: str
    images: list[ImageInfo]
    instances: list[InstanceInfo]


Message = Union[
    QueryHostMessage,
    CommandStartMessage,
    CommandStopMessage,
    CommandRestartMessage,
    CommandDestroyMessage,
    CommandCreateMessage,
]

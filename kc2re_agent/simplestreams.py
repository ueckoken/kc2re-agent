from dataclasses import dataclass
from typing import cast, Optional, TypedDict
import requests

# port of lxc/lxd/shared/simplesreams.go
# based on lxd 4.18

# https://github.com/lxc/lxd/blob/lxd-4.18/shared/simplestreams/index.go#L11
class StreamIndex(TypedDict):
    datatype: str
    path: str
    updated: Optional[str]
    products: list[str]
    format: Optional[str]


# https://github.com/lxc/lxd/blob/lxd-4.18/shared/simplestreams/index.go#L4
class Stream(TypedDict):
    index: dict[str, StreamIndex]
    updated: Optional[str]
    format: str


# https://github.com/lxc/lxd/blob/lxd-4.18/shared/simplestreams/products.go#L48
# some attributes in ProductVersionItem contains hyphen
# cannot use class syntax
# use alternative TypeDict syntax instead
ProductVersionItem = TypedDict(
    "ProductVersionItem",
    {
        "combined_disk1-img_sha256": Optional[str],
        "combined_disk-kvm-img_sha256": Optional[str],
        "combined_uefi1-kvm-img_sha256": Optional[str],
        "combined_rootxz_sha256": Optional[str],
        "combined_sha256": Optional[str],
        "combined_squashfs_sha256": Optional[str],
        "ftype": str,
        "md5": Optional[str],
        "path": str,
        "sha256": Optional[str],
        "size": int,
        "delta_base": Optional[str],
    },
)


# https://github.com/lxc/lxd/blob/lxd-4.18/shared/simplestreams/products.go#L41
class ProductVersion(TypedDict):
    items: dict[str, ProductVersionItem]
    label: Optional[str]
    pubname: Optional[str]


# https://github.com/lxc/lxd/blob/lxd-4.18/shared/simplestreams/products.go#L24
class _Product(TypedDict):
    aliases: str
    arch: str
    os: str
    release: str
    release_codename: Optional[str]
    release_title: str
    supported: Optional[bool]
    supported_eol: Optional[str]
    version: Optional[str]
    versions: dict[str, ProductVersion]


class Product(_Product, total=False):
    # non-standard keys, can be missing
    # https://github.com/lxc/lxd/blob/lxd-4.18/shared/simplestreams/products.go#L36
    variant: str


# https://github.com/lxc/lxd/blob/lxd-4.18/shared/simplestreams/products.go#L14
class Products(TypedDict):
    content_id: str
    datatype: str
    format: str
    license: Optional[str]
    products: dict[str, Product]
    updated: Optional[str]


class SimpleStreamsClient:
    url: str

    def __init__(self, url: str):
        # https://github.com/lxc/lxd/blob/lxd-4.18/client/connection.go#L191
        self.url = url.removesuffix("/")

    def get_stream(self) -> Stream:
        # https://github.com/lxc/lxd/blob/lxd-4.18/shared/simplestreams/simplestreams.go#L152
        response = requests.get(self.url + "/" + "streams/v1/index.json")
        return cast(Stream, response.json())

    # https://github.com/lxc/lxd/blob/lxd-4.18/shared/simplestreams/simplestreams.go#L175
    # example: path="streams/v1/images.json"
    def get_products(self, path: str) -> Products:
        response = requests.get(self.url + "/" + path)
        return cast(Products, response.json())

    # https://github.com/lxc/lxd/blob/lxd-4.18/shared/simplestreams/simplestreams.go#L277
    def list_images(self) -> list[Product]:
        stream = self.get_stream()
        stream_index = stream["index"]
        all_images: list[Product] = []

        # https://github.com/lxc/lxd/blob/lxd-4.18/shared/simplestreams/simplestreams.go#L291
        for entry in stream_index.values():
            if entry["datatype"] != "image-downloads":
                continue
            if len(entry["products"]) == 0:
                continue
            path = entry["path"]
            product = self.get_products(path)
            products = product["products"]
            all_images += products.values()
        return all_images

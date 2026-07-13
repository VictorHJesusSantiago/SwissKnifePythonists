from __future__ import annotations

import ipaddress
from typing import Any


def describe(cidr: str) -> dict[str, Any]:
    network = ipaddress.ip_network(cidr, strict=False)
    hosts = list(network.hosts())
    return {
        "network": str(network.network_address),
        "broadcast": str(network.broadcast_address) if network.version == 4 else None,
        "netmask": str(network.netmask),
        "prefix_length": network.prefixlen,
        "total_addresses": network.num_addresses,
        "usable_hosts": len(hosts),
        "first_host": str(hosts[0]) if hosts else None,
        "last_host": str(hosts[-1]) if hosts else None,
        "is_private": network.is_private,
        "version": network.version,
    }


def split(cidr: str, new_prefix: int) -> list[str]:
    network = ipaddress.ip_network(cidr, strict=False)
    return [str(subnet) for subnet in network.subnets(new_prefix=new_prefix)]


def summarize(cidrs: list[str]) -> list[str]:
    networks = [ipaddress.ip_network(cidr, strict=False) for cidr in cidrs]
    return [str(network) for network in ipaddress.collapse_addresses(networks)]


def contains(cidr: str, address: str) -> bool:
    return ipaddress.ip_address(address) in ipaddress.ip_network(cidr, strict=False)


def overlaps(cidr_a: str, cidr_b: str) -> bool:
    return ipaddress.ip_network(cidr_a, strict=False).overlaps(ipaddress.ip_network(cidr_b, strict=False))

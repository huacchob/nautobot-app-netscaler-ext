"""Create fixtures for tests."""

import json
from pathlib import Path
from typing import Any

from django.contrib.contenttypes.models import ContentType
from nautobot.dcim.models import (
    Device,
    DeviceType,
    Interface,
    Location,
    LocationType,
    Manufacturer,
    Platform,
)
from nautobot.extras.models import (
    ConfigContext,
    Role,
    Secret,
    SecretsGroup,
    SecretsGroupAssociation,
    Status,
)
from nautobot.ipam.models import IPAddress, Namespace, Prefix

from netscaler_ext.models import NetscalerExtExampleModel


def create_netscalerextexamplemodel():
    """Fixture to create necessary number of NetscalerExtExampleModel for tests."""
    NetscalerExtExampleModel.objects.create(name="Test One")
    NetscalerExtExampleModel.objects.create(name="Test Two")
    NetscalerExtExampleModel.objects.create(name="Test Three")


def create_devices_in_orm():
    # Status and Role
    status_name = "Active"
    role_name = "Network"

    # LT
    region_lt_name = "Region"
    country_lt_name = "Country"
    state_lt_name = "State"
    city_lt_name = "City"
    building_lt_name = "Building"

    # Sites
    uncc_site: dict[str, str] = {
        "region_name": "AMRS",
        "country_name": "United States",
        "state_name": "North Carolina",
        "city_name": "Charlotte",
        "building_name": "UNCC",
    }
    sites: list[dict[str, str]] = [uncc_site]

    # Devices
    netscaler_dev: dict[str, str] = {
        "manufacturer_name": "Citrix",
        "device_type_name": "Netscaler-Type",
        "platform_name": "netscaler",
        "network_driver_name": "netscaler",
        "device_name": "netscaler1",
        "location": "UNCC",
        "namespace_name": "Global",
        "prefix_range": "172.18.0.0/16",
        "ip_addr": "172.18.0.8/32",
        "interface_name": "int1",
    }
    nxos_dev: dict[str, str] = {
        "manufacturer_name": "Cisco",
        "device_type_name": "Nxos-Type",
        "platform_name": "cisco_nxos",
        "network_driver_name": "cisco_nxos",
        "device_name": "nxos1",
        "location": "UNCC",
        "namespace_name": "Global",
        "prefix_range": "172.20.0.0/16",
        "ip_addr": "172.20.20.2/32",
        "interface_name": "int1",
    }
    meraki_dev: dict[str, str] = {
        "manufacturer_name": "Cisco",
        "device_type_name": "Meraki-Controller-Type",
        "platform_name": "meraki_controller",
        "network_driver_name": "meraki_controller",
        "device_name": "meraki-controller",
        "location": "UNCC",
        "config_context": "fixtures/config_context/meraki_context.json",
        "context_name": "meraki_endpoints",
    }
    devices: list[dict[str, str]] = [netscaler_dev, nxos_dev, meraki_dev]

    # Secrets
    netscaler_secret: dict[str, str] = {
        "secret1": "NETSCALER_USER",
        "secret2": "NETSCALER_PASS",
        "provider": "environment-variable",
        "secrets_group_name": "NETSCALER",
        "sga_access_type": "Generic",
        "sga1_secret_type": "username",
        "sga2_secret_type": "password",
        "device": "netscaler1",
    }
    nxos_secret: dict[str, str] = {
        "secret1": "NXOS_USER",
        "secret2": "NXOS_PASS",
        "provider": "environment-variable",
        "secrets_group_name": "NXOS",
        "sga_access_type": "Generic",
        "sga1_secret_type": "username",
        "sga2_secret_type": "password",
        "device": "nxos1",
    }
    meraki_secret: dict[str, str] = {
        "secret1": "MERAKI_API_KEY",
        "provider": "environment-variable",
        "secrets_group_name": "MERAKI_SECRET",
        "sga_access_type": "HTTP",
        "sga1_secret_type": "token",
        "device": "meraki-controller",
    }
    secrets: list[dict[str, str]] = [
        netscaler_secret,
        nxos_secret,
        meraki_secret,
    ]

    # Contet types
    device_ct: ContentType = ContentType.objects.get_for_model(model=Device)
    interface_ct: ContentType = ContentType.objects.get_for_model(model=Interface)

    # status
    status, _ = Status.objects.get_or_create(name=status_name)

    # Role
    role, _ = Role.objects.get_or_create(
        name=role_name,
    )

    role.content_types.add(device_ct, interface_ct)

    # Location types
    region_lt, _ = LocationType.objects.get_or_create(
        name=region_lt_name,
    )
    country_lt, _ = LocationType.objects.get_or_create(
        name=country_lt_name,
        parent_id=region_lt.id,
    )
    state_lt, _ = LocationType.objects.get_or_create(
        name=state_lt_name,
        parent_id=country_lt.id,
    )
    city_lt, _ = LocationType.objects.get_or_create(
        name=city_lt_name,
        parent_id=state_lt.id,
    )
    building_lt, _ = LocationType.objects.get_or_create(
        name=building_lt_name,
        parent_id=city_lt.id,
    )
    building_lt.content_types.add(device_ct)

    for site in sites:
        region, _ = Location.objects.get_or_create(
            name=site.get("region_name"),
            defaults={
                "location_type": region_lt,
                "status": status,
            },
        )

        country, _ = Location.objects.get_or_create(
            name=site.get("country_name"),
            defaults={
                "location_type": country_lt,
                "status_id": status.id,
            },
        )

        state, _ = Location.objects.get_or_create(
            name=site.get("state_name"),
            defaults={
                "location_type": state_lt,
                "status_id": status.id,
            },
        )

        city, _ = Location.objects.get_or_create(
            name=site.get("city_name"),
            defaults={
                "location_type": city_lt,
                "status_id": status.id,
            },
        )

        building, _ = Location.objects.get_or_create(
            name=site.get("building_name"),
            defaults={
                "location_type": building_lt,
                "status_id": status.id,
            },
        )

    for dev in devices:
        # Manufacturer
        manufacturer, _ = Manufacturer.objects.get_or_create(
            name=dev.get("manufacturer_name"),
        )

        # Device Type
        dt, _ = DeviceType.objects.get_or_create(
            manufacturer_id=manufacturer.id,
            model=dev.get("device_type_name"),
        )

        # Platform
        plat, _ = Platform.objects.get_or_create(
            name=dev.get("platform_name"),
            manufacturer_id=manufacturer.id,
            network_driver=dev.get("network_driver_name"),
        )

        # Device
        loc = Location.objects.get(
            name=dev.get("location"),
        )
        device, _ = Device.objects.get_or_create(
            name=dev.get("device_name"),
            device_type=dt,
            role=role,
            location=loc,
            status=status,
            platform=plat,
        )

        if dev.get("ip_addr"):
            # Namespace
            namespace, _ = Namespace.objects.get_or_create(
                name=dev.get("namespace_name"),
            )

            # Prefix
            prefix, _ = Prefix.objects.get_or_create(
                prefix=dev.get("prefix_range"),
                namespace=namespace,
                status_id=status.id,
            )

            # IP Address
            ip, _ = IPAddress.objects.get_or_create(
                address=dev.get("ip_addr"),
                status_id=status.id,
            )

            # Interface
            interface, _ = Interface.objects.get_or_create(
                name=dev.get("interface_name"),
                device_id=device.id,
                status_id=status.id,
                role_id=role.id,
                type="virtual",
            )

            interface.ip_addresses.add(ip)
            interface.validated_save()

            device.primary_ip4 = ip
            device.validated_save()

        if dev.get("config_context"):
            try:
                existing_context = ConfigContext.objects.get(name=dev.get("context_name"))
                existing_context.delete()
            except ConfigContext.DoesNotExist:
                pass
            with open(file=Path(__file__).parent.joinpath(dev.get("config_context"))) as f:
                json_data: dict[Any, Any] = json.load(fp=f)
            cntx, _ = ConfigContext.objects.get_or_create(
                name=dev.get("context_name"),
                data=json_data,
            )
            cntx.validated_save()

    for secret in secrets:
        # Secrets
        sg, _ = SecretsGroup.objects.get_or_create(
            name=secret.get("secrets_group_name"),
        )
        if secret.get("secret1") and secret.get("sga1_secret_type"):
            s1, _ = Secret.objects.get_or_create(
                name=secret.get("secret1"),
                provider=secret.get("provider"),
                parameters={"variable": secret.get("secret1")},
            )
            sga1, _ = SecretsGroupAssociation.objects.get_or_create(
                secret=s1,
                access_type=secret.get("sga_access_type"),
                secret_type=secret.get("sga1_secret_type"),
                secrets_group=sg,
            )
        if secret.get("secret2") and secret.get("sga2_secret_type"):
            s2, _ = Secret.objects.get_or_create(
                name=secret.get("secret2"),
                provider=secret.get("provider"),
                parameters={"variable": secret.get("secret2")},
            )
            sga2, _ = SecretsGroupAssociation.objects.get_or_create(
                secret=s2,
                access_type=secret.get("sga_access_type"),
                secret_type=secret.get("sga2_secret_type"),
                secrets_group=sg,
            )

        sg.validated_save()

        device: Device = Device.objects.get(name=secret.get("device"))
        device.secrets_group = sg

        device.validated_save()

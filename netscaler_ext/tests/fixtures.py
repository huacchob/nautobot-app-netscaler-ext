"""Create fixtures for tests."""

import json
from pathlib import Path
from typing import Any

from django.contrib.contenttypes.models import ContentType
from nautobot.dcim.models import Device, DeviceType, Interface, Location, LocationType, Manufacturer, Platform
from nautobot.extras.choices import SecretsGroupAccessTypeChoices, SecretsGroupSecretTypeChoices
from nautobot.extras.models import ConfigContext, Role, Secret, SecretsGroup, SecretsGroupAssociation, Status
from nautobot.ipam.models import IPAddress, Namespace, Prefix

from netscaler_ext.models import NetscalerExtExampleModel

# pylint: disable=too-many-locals, too-many-statements, invalid-name


def create_netscalerextexamplemodel():
    """Fixture to create necessary number of NetscalerExtExampleModel for tests."""
    NetscalerExtExampleModel.objects.create(name="Test One")
    NetscalerExtExampleModel.objects.create(name="Test Two")
    NetscalerExtExampleModel.objects.create(name="Test Three")


def get_json_fixture(folder: str, file_name: str) -> dict[str, Any]:
    """Fixture to return a mock config context for tests.

    Args:
        folder (str): The folder where the config context file is located.
        file_name (str): The name of the config context file.

    Returns:
        dict[str, Any]: The mock config context.
    """
    context_file: Path = Path(__file__).parent.joinpath(
        "fixtures",
        folder,
        file_name,
    )
    with open(file=context_file, mode="r", encoding="utf-8") as file:
        context: dict[str, Any] = json.load(fp=file)
    return context


def create_devices_in_orm() -> None:
    """Create devices in ORM."""
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

    # Secrets
    netscaler_secret: dict[str, str] = {
        "secret1": "NETSCALER_USER",
        "secret2": "NETSCALER_PASS",
        "provider": "environment-variable",
        "secrets_group_name": "NETSCALER",
        "sga_access_type": SecretsGroupAccessTypeChoices.TYPE_GENERIC,
        "sga1_secret_type": SecretsGroupSecretTypeChoices.TYPE_USERNAME,
        "sga2_secret_type": SecretsGroupSecretTypeChoices.TYPE_PASSWORD,
        "device": "netscaler1",
    }
    nxos_secret: dict[str, str] = {
        "secret1": "NXOS_USER",
        "secret2": "NXOS_PASS",
        "provider": "environment-variable",
        "secrets_group_name": "NXOS",
        "sga_access_type": SecretsGroupAccessTypeChoices.TYPE_GENERIC,
        "sga1_secret_type": SecretsGroupSecretTypeChoices.TYPE_USERNAME,
        "sga2_secret_type": SecretsGroupSecretTypeChoices.TYPE_PASSWORD,
        "device": "nxos1",
    }
    meraki_secret: dict[str, str] = {
        "secret1": "MERAKI_API_KEY",
        "provider": "environment-variable",
        "secrets_group_name": "MERAKI_SECRET",
        "sga_access_type": SecretsGroupAccessTypeChoices.TYPE_HTTP,
        "sga1_secret_type": SecretsGroupSecretTypeChoices.TYPE_TOKEN,
        "device": "meraki-controller",
    }
    secrets: list[dict[str, str]] = [
        netscaler_secret,
        nxos_secret,
        meraki_secret,
    ]

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
        "secrets_group": "NETSCALER",
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
        "secrets_group": "NXOS",
    }
    meraki_dev: dict[str, str] = {
        "manufacturer_name": "Cisco",
        "device_type_name": "Meraki-Controller-Type",
        "platform_name": "cisco_meraki",
        "network_driver_name": "cisco_meraki",
        "device_name": "meraki-controller",
        "location": "UNCC",
        "config_context": "fixtures/config_context/meraki_context.json",
        "context_name": "meraki_endpoints",
        "secrets_group": "MERAKI_SECRET",
    }
    devices: list[dict[str, str]] = [
        netscaler_dev,
        nxos_dev,
        meraki_dev,
    ]

    # Contet types
    device_ct: ContentType = ContentType.objects.get_for_model(model=Device)
    interface_ct: ContentType = ContentType.objects.get_for_model(model=Interface)

    # status
    status, _ = Status.objects.get_or_create(name=status_name)
    status.validated_save()

    # Role
    role, _ = Role.objects.get_or_create(
        name=role_name,
    )
    role.validated_save()

    role.content_types.add(device_ct, interface_ct)

    # Location types
    region_lt, _ = LocationType.objects.get_or_create(
        name=region_lt_name,
    )
    region_lt.validated_save()
    country_lt, _ = LocationType.objects.get_or_create(
        name=country_lt_name,
        parent_id=region_lt.id,
    )
    country_lt.validated_save()
    state_lt, _ = LocationType.objects.get_or_create(
        name=state_lt_name,
        parent_id=country_lt.id,
    )
    state_lt.validated_save()
    city_lt, _ = LocationType.objects.get_or_create(
        name=city_lt_name,
        parent_id=state_lt.id,
    )
    city_lt.validated_save()
    building_lt, _ = LocationType.objects.get_or_create(
        name=building_lt_name,
        parent_id=city_lt.id,
    )
    building_lt.validated_save()
    building_lt.content_types.add(device_ct)

    for site in sites:
        region, _ = Location.objects.get_or_create(
            name=site.get("region_name"),
            defaults={
                "location_type": region_lt,
                "status": status,
            },
        )
        region.validated_save()

        Location.objects.get_or_create(
            name=site.get("country_name"),
            defaults={
                "location_type": country_lt,
                "status_id": status.id,
            },
        )

        Location.objects.get_or_create(
            name=site.get("state_name"),
            defaults={
                "location_type": state_lt,
                "status_id": status.id,
            },
        )

        Location.objects.get_or_create(
            name=site.get("city_name"),
            defaults={
                "location_type": city_lt,
                "status_id": status.id,
            },
        )

        Location.objects.get_or_create(
            name=site.get("building_name"),
            defaults={
                "location_type": building_lt,
                "status_id": status.id,
            },
        )

    for secret in secrets:
        # Secrets
        if not secret.get("secrets_group_name"):
            continue
        sg, _ = SecretsGroup.objects.get_or_create(
            name=secret.get("secrets_group_name"),
        )
        if secret.get("secret1") and secret.get("sga1_secret_type"):
            s1, _ = Secret.objects.get_or_create(
                name=secret.get("secret1"),
                provider=secret.get("provider"),
                parameters={"variable": secret.get("secret1")},
            )
            s1.validated_save()
            sga1, _ = SecretsGroupAssociation.objects.get_or_create(
                secret=s1,
                access_type=secret.get("sga_access_type"),
                secret_type=secret.get("sga1_secret_type"),
                secrets_group=sg,
            )
            sga1.validated_save()
        if secret.get("secret2") and secret.get("sga2_secret_type"):
            s2, _ = Secret.objects.get_or_create(
                name=secret.get("secret2"),
                provider=secret.get("provider"),
                parameters={"variable": secret.get("secret2")},
            )
            s2.validated_save()
            sga2, _ = SecretsGroupAssociation.objects.get_or_create(
                secret=s2,
                access_type=secret.get("sga_access_type"),
                secret_type=secret.get("sga2_secret_type"),
                secrets_group=sg,
            )
            sga2.validated_save()

        sg.validated_save()

    for dev in devices:
        # Manufacturer
        manufacturer, _ = Manufacturer.objects.get_or_create(
            name=dev.get("manufacturer_name"),
        )
        manufacturer.validated_save()

        # Device Type
        dt, _ = DeviceType.objects.get_or_create(
            manufacturer_id=manufacturer.id,
            model=dev.get("device_type_name"),
        )
        dt.validated_save()

        # Platform
        plat, _ = Platform.objects.get_or_create(
            name=dev.get("platform_name"),
            manufacturer_id=manufacturer.id,
            network_driver=dev.get("network_driver_name"),
        )
        plat.validated_save()

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
            namespace.validated_save()

            # Prefix
            prefix, _ = Prefix.objects.get_or_create(
                prefix=dev.get("prefix_range"),
                namespace=namespace,
                status_id=status.id,
            )
            prefix.validated_save()

            # IP Address
            ip, _ = IPAddress.objects.get_or_create(
                address=dev.get("ip_addr"),
                status_id=status.id,
            )
            ip.validated_save()

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

        if dev.get("secrets_group"):
            device.secrets_group = SecretsGroup.objects.get(name=dev.get("secrets_group"))

        if dev.get("config_context"):
            if cntx := ConfigContext.objects.filter(name=dev.get("context_name")):
                cntx[0].delete()
            with open(
                file=Path(__file__).parent.joinpath(dev.get("config_context")),
                mode="r",
                encoding="utf-8",
            ) as f:
                json_data: dict[Any, Any] = json.load(fp=f)
            cntx, _ = ConfigContext.objects.get_or_create(
                name=dev.get("context_name"),
                data=json_data,
            )
        device.validated_save()


def delete_devices_in_orm() -> None:
    """Delete created objects in ORM."""
    IPAddress.objects.all().delete()
    Namespace.objects.all().delete()
    Interface.objects.all().delete()
    Device.objects.all().delete()
    Platform.objects.all().delete()
    DeviceType.objects.all().delete()
    Manufacturer.objects.all().delete()
    Location.objects.all().delete()
    LocationType.objects.all().delete()
    Status.objects.all().delete()
    Role.objects.all().delete()
    Secret.objects.all().delete()
    SecretsGroup.objects.all().delete()
    ConfigContext.objects.all().delete()

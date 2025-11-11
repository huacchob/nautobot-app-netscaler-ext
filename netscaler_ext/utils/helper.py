"""Classes and functions for controller dispatcher utils."""

from base64 import b64encode
from logging import Logger
from typing import Any

import jdiff
from jinja2 import exceptions as jinja_errors
from nautobot.apps.choices import (
    SecretsGroupAccessTypeChoices,
    SecretsGroupSecretTypeChoices,
)
from nautobot.core.utils.data import render_jinja2
from nautobot.dcim.models import Controller, Device
from nautobot.extras.models import SecretsGroup, SecretsGroupAssociation
from remote_pdb import RemotePdb


def render_jinja_template(obj: Device, logger: Logger, template: str) -> str:
    """Helper function to render Jinja templates.

    Args:
        obj (Device): The Device object from Nautobot.
        logger (Logger): Logger to log error messages to.
        template (str): A Jinja2 template to be rendered.

    Returns:
        str: The ``template`` rendered.

    Raises:
        ValueError: When there is an error rendering the ``template``.
    """
    try:
        return render_jinja2(template_code=template, context={"obj": obj})
    except jinja_errors.UndefinedError as error:
        error_msg = (
            "`E3019:` Jinja encountered and UndefinedError`, check the template "
            "for missing variable definitions.\n"
            f"Template:\n{template}\n"
            f"Original Error: {error}"
        )
        logger.error(error_msg, extra={"object": obj})
        raise ValueError(error_msg) from error

    except (
        jinja_errors.TemplateSyntaxError
    ) as error:  # Also catches subclass of TemplateAssertionError
        error_msg = (
            f"`E3020:` Jinja encountered a SyntaxError at line number {error.lineno},"
            f"check the template for invalid Jinja syntax.\nTemplate:\n{template}\n"
            f"Original Error: {error}"
        )
        logger.error(error_msg, extra={"object": obj})
        raise ValueError(error_msg) from error
    # Intentionally not catching TemplateNotFound errors since template is passes as a string and not a filename
    except (
        jinja_errors.TemplateError
    ) as error:  # Catches all remaining Jinja errors
        error_msg = (
            "`E3021:` Jinja encountered an unexpected TemplateError; check the template for correctness\n"
            f"Template:\n{template}\n"
            f"Original Error: {error}"
        )
        logger.error(error_msg, extra={"object": obj})
        raise ValueError(error_msg) from error


def base_64_encode_credentials(username: str, password: str) -> str:
    """Encode username and password into base64.

    Args:
        username (str): The username to encode.
        password (str): The password to encode.

    Returns:
        str: Base64 encoded credentials.

    Raises:
        ValueError: If username or password is not a string.
    """
    if not username or not password:
        raise ValueError("Username and/or password not passed, can't encode.")

    credentials_str: bytes = f"{username}:{password}".encode()
    return f"Basic {b64encode(s=credentials_str).decode(encoding='utf-8')}"


def format_base_url_with_endpoint(
    base_url: str,
    endpoint: str,
) -> str:
    """Format base url with API endpoint.

    Args:
        base_url (str): Base url to format.
        endpoint (str): Endpoint to format with.

    Returns:
        str: Formatted url.
    """
    if not base_url or not endpoint:
        raise ValueError(
            "Base or endpoint not passed, can not properly format url.",
        )

    if base_url.endswith("/"):
        base_url = base_url[:-1]

    if endpoint.startswith("/"):
        endpoint = endpoint[1:]

    return f"{base_url}/{endpoint}"


def add_api_path_to_url(api_path: str, base_url: str) -> str:
    """Add API path to base url.

    Args:
        api_path (str): API path, i.e. api/v1
        base_url (str): Controller base url.

    Returns:
        str: Base url with API path.
    """
    if api_path not in base_url:
        return format_base_url_with_endpoint(
            base_url=base_url,
            endpoint=api_path,
        )
    return base_url


def get_api_key(secrets_group: SecretsGroup) -> str:
    """Get controller API Key.

    Args:
        secrets_group (SecretsGroup): SecretsGroup object.

    Raises:
        SecretsGroupAssociation.DoesNotExist: SecretsGroupAssociation access
            type TYPE_HTTP or secret type TYPE_TOKEN does not exist.

    Returns:
        str: API key.
    """
    try:
        api_key: str = secrets_group.get_secret_value(
            access_type=SecretsGroupAccessTypeChoices.TYPE_HTTP,
            secret_type=SecretsGroupSecretTypeChoices.TYPE_TOKEN,
        )
    except SecretsGroupAssociation.DoesNotExist:
        api_key: str = secrets_group.get_secret_value(
            access_type=SecretsGroupAccessTypeChoices.TYPE_GENERIC,
            secret_type=SecretsGroupSecretTypeChoices.TYPE_PASSWORD,
        )
    return api_key


def resolve_controller_url(
    obj: Device,
    controller_type: str,
    logger: Logger,
) -> str:
    """Resolve controller url.

    Args:
        obj (Device): Device object.
        controller_type (str): Name of the controller type.
        logger (Logger): Logger object.

    Returns:
        str: Controller url

    Raises:
        ValueError: Could not find the controller API URL from external integration.
    """
    controller_url: str = ""
    if controller_group := obj.controller_managed_device_group:
        controller: Controller = controller_group.controller
        controller_url = controller.external_integration.remote_url
    elif controllers := obj.controllers.all():
        for cntrlr in controllers:
            if controller_type in cntrlr.platform.name.lower():
                controller_url = cntrlr.external_integration.remote_url
    if not controller_url:
        logger.error("Could not find the Meraki Dashboard API URL")
        raise ValueError("Could not find the Meraki Dashboard API URL")
    return controller_url


def resolve_params(
    parameters: list[str],
    param_mapper: dict[str, str],
) -> dict[Any, Any]:
    """Resolve parameters.

    Args:
        parameters (list[str]): Parameters list.
        param_mapper (dict[str, str]): Parameters mapper.

    Returns:
        dict[Any, Any]: _description_
    """
    params: dict[Any, Any] = {}
    if not parameters or not param_mapper:
        return params
    for param in parameters:
        if param.lower() not in [p.lower() for p in param_mapper]:
            continue
        for k, v in param_mapper.items():
            if k.lower() == param.lower():
                params.update({k: v})
    return params


def resolve_jmespath(
    jmespath_values: dict[str, str],
    api_response: Any,
    logger: Logger,
) -> dict[Any, Any] | list[dict[str, Any]]:
    """Resolve jmespath.

    Args:
        jmespath_values (dict[str, str]): Jmespath dictionary.
        api_response (Any): API response.

    Returns:
        dict[Any, Any] | list[dict[str, Any]]: Resolved jmespath data fields.
    """
    data_fields: dict[str, Any] = {}

    for key, value in jmespath_values.items():
        if "enforceIdleTimeout" in value:
            RemotePdb(host="127.0.0.1", port=4444).set_trace()
        try:
            j_value: Any = jdiff.extract_data_from_json(
                path=value,
                data=api_response,
            )
        except TypeError as exc:
            # JSON key returns a None value, and raising a TypeError when
            # `null` is a valid value for that key
            if "JMSPath returned 'None'." in str(exc):
                j_value = None
            else:
                logger.error(f"Error resolving jmespath for key {key}: {exc}")
                return {}
        except ValueError:
            logger.error(f"ValueError resolving jmespath for key {key}")
            return {}
        data_fields.update({key: j_value})
    lengths: list[int] = [
        len(v) for v in data_fields.values() if isinstance(v, list)
    ]
    if lengths == [1]:
        return data_fields
    if len(lengths) != len(data_fields.values()):
        return data_fields
    if len(set(lengths)) != 1:
        return data_fields
    keys: list[str] = list(data_fields.keys())
    values = zip(*data_fields.values())
    return [dict(zip(keys, v)) for v in values]


def resolve_query(api_endpoint: str, query: list[str]) -> str:
    """Append query to api endpoint.

    Args:
        api_endpoint (str): API endpoint URL.
        query (list[str]): Query list.

    Returns:
        str: API endpoint with query appended.
    """
    if api_endpoint.endswith("/"):
        api_endpoint = api_endpoint[:-1]
    api_endpoint = f"{api_endpoint}?{query.pop(0)}"
    if not query:
        return api_endpoint
    for q in query:
        api_endpoint = f"{api_endpoint}&{q}"
    return api_endpoint

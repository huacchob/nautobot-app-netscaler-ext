# Nautobot Setup for Golden Config Dispatchers

This document outlines the necessary steps to configure your Nautobot environment to effectively utilize the Golden Config Dispatchers, particularly for API-driven controller integrations.

## 1. Platform to Framework Mapping

To ensure Nautobot Golden Config uses the correct dispatcher for each platform, you need to configure the framework mappings.

1. **Navigate to Configuration**:

   - In the Nautobot UI, scroll down the vertical menu bar and click on **Admin**.
   - From the dropdown, select **Admin** again.
   - On the `Site administration` page, click on the **Config** menu item.
     ![Config Site Admin](images/config_site_admin.png)

2. **Configure Golden Configuration Settings**:
   - On the `Configuration` page, scroll down to the **Golden Configuration** section.
   - You can either set a `DEFAULT FRAMEWORK` for all platforms or individually configure the `GET CONFIG FRAMEWORK` (for backup) and `MERGE CONFIG FRAMEWORK` (for remediation) for specific platforms.
   - For API dispatchers, you will typically map the platform (e.g., `cisco_meraki`) to its corresponding dispatcher framework (e.g., `cisco_meraki`).
   - _Note_: You do not need to update both `DEFAULT FRAMEWORK` and the individual GET/MERGE frameworks simultaneously.
     ![Golden Config Framework Mappings](images/golden_config_framework_mappings.png)

## 2. Creating a Secrets Group

A `Secrets Group` is essential for securely storing credentials that the dispatchers will use to authenticate with external controllers.

- The created `Secrets Group` must be compatible with Golden Config. This means it requires at least two `Secrets` associated with it:
  - One with `Access Type: Generic` and `Secret Type: Username`.
  - One with `Access Type: Generic` and `Secret Type: Password`.
  - Optionally, a third `Secret` with `Access Type: Generic` and `Secret Type: Secret` can be added.
- Refer to the [Nautobot: Create Secrets/Secrets Group](https://docs.nautobot.com/projects/core/en/stable/user-guide/platform-functionality/secret/) documentation for detailed instructions on creating secrets.

## 3. Controller Platforms Specific Setup

For dispatchers that interact with external controller platforms (e.g., Cisco Meraki, vManage, APIC), additional setup is required to properly define and manage these controllers within Nautobot.

### 3.1. Location Type for Storing Controllers

The `Location Type` you use for locations that will house your controller objects needs to be configured to accept `Controller` objects.

1. **Navigate to Location Types**:

   - In the Nautobot UI, scroll down the vertical menu bar to the **ORGANIZATION** dropdown.
   - Under the **LOCATIONS** section, click on the **Location Types** menu item.
     ![Location Types Menu Item](images/location_types_menu_item.png)

2. **Edit Location Type**:

   - On the `Location Types` page, click the orange edit pencil icon next to the `Location Type` that will store your controllers.
     ![Location Type Quick Edit](images/object_quick_edit_option.png)

3. **Add Controller Content Type**:
   - On the `Location Type` object's edit page, add `dcim | controller` to the `Content types` field.
   - Click the blue **Update** button to save your changes.
     ![Add Controller To Content Type](images/add_controller_to_content_type.png)

### 3.2. Controller Device Placeholder

It is best practice to create a "controller device placeholder" in Nautobot. This device represents the controller itself (e.g., a Meraki Dashboard, a vManage instance) and is used for system-level API calls, rather than API calls to devices managed by the controller.

- For example, for the Meraki platform, you might have two separate platforms: `cisco_meraki` for the controller placeholder device and `meraki_managed` for devices managed by Meraki (like APs).
- Refer to the [Nautobot: Create A Device](https://docs.nautobot.com/projects/core/en/stable/user-guide/feature-guides/getting-started/creating-devices/) documentation for creating devices.

### 3.3. External Integration

`External Integrations` are used to define the connectivity details for your controller objects, including their remote URL and associated `Secrets Group`.

1. **Navigate to External Integrations**:

   - In the Nautobot UI, scroll down the vertical menu bar to the **EXTENSIBILITY** dropdown.
   - Under the **AUTOMATION** section, click on the **External Integrations** menu item.
     ![Extensibility Menu Item](images/extensibility_menu_item.png)
     ![External Integrations Menu Item](images/external_integrations_menu_item.png)

2. **Create External Integration**:
   - Create a new `External Integration` and configure it with the controller's remote URL and the `Secrets Group` created earlier.

- Refer to the [Nautobot: Create External Integrations](https://docs.nautobot.com/projects/core/en/stable/user-guide/platform-functionality/externalintegration/) documentation for more information.

### 3.4. Controller Creation

Create `Controller` objects in Nautobot to represent your external network controllers.

1. **Navigate to Controllers**:

   - In the Nautobot UI, scroll down the vertical menu bar to the **DEVICES** dropdown.
   - Under the **CONTROLLERS** section, click on the **Controllers** menu item.
     ![Devices Menu Item](images/devices_menu_item.png)
     ![Controllers Menu Item](images/controllers_menu_item.png)

2. **Configure Controller**:
   - When creating a controller, ensure you associate it with the correct `External Integration`, `Platform`, and the `Controller Device Placeholder` created previously.
     ![Create Controller](images/create_controller.png)

- Refer to the [Nautobot: Create Controller](https://docs.nautobot.com/projects/core/en/stable/user-guide/feature-guides/wireless-networks-and-controllers/#controllers) documentation for detailed instructions.

### 3.5. Update Golden Config Settings to Disable Ping Tests

For controller-based dispatchers, especially with cloud-managed controllers or placeholder devices without direct IP connectivity, it's often necessary to disable Golden Config's default ping test.

1. **Navigate to Golden Config Settings**:

   - In the Nautobot UI, scroll down the vertical menu bar to the **GOLDEN CONFIG** dropdown.
   - Under the **SETUP** section, click on the **Golden Config Settings** menu item.
     ![Golden Config Settings Menu Item](images/golden_config_settings_menu_item.png)

2. **Configure Controller-Specific Settings**:

   - Create a separate `Golden Config Settings` object specifically for your controller-based dispatchers.
   - Use a `Dynamic Group` to ensure these settings apply only to your controller placeholder devices.
   - Adjust the `Weight` of this setting to give it higher precedence for controller devices.
     ![Golden Config Settings Weight](images/gc_settings_weight.png)

3. **Disable Backup Test**:
   - Edit the controller-specific `Golden Config Settings` object.
   - **Uncheck** the `Backup Test` box to disable the ping test for devices covered by these settings.
     ![Golden Config Ping Unchecked Box](images/gc_setting_uncheck_ping.png)
     ![Golden Config Ping Test](images/gc_ping_test.png)

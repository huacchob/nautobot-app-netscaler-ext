# Project Overview

This project is a Nautobot App for interacting with Citrix NetScaler devices. It appears to be in an early stage of development or based on a template, as it contains placeholder models and documentation. The app uses Nornir and Netmiko for network automation and provides a framework for authenticating to NetScaler devices and potentially executing commands.

# Building and Running

The project uses Docker and `invoke` for its development environment.

**Key Commands:**

- **Build the Docker image:**
  ```bash
  invoke build
  ```
- **Start the application:**
  ```bash
  invoke start
  ```
- **Stop the application:**
  ```bash
  invoke stop
  ```
- **Run all tests:**
  ```bash
  invoke tests
  ```
- **Run unit tests:**
  ```bash
  invoke unittest
  ```
- **Open a shell in the container:**
  ```bash
  invoke cli
  ```
- **Serve the documentation locally:**
  ```bash
  invoke docs
  ```

# Development Conventions

- **Dependency Management:** The project uses `poetry` for managing Python dependencies.
- **Linting:** `ruff` and `pylint` are used for code linting.
- **Testing:** `pytest` is used for unit testing.
- **Task Automation:** `invoke` is used for automating common development tasks.
- **Documentation:** The project uses `mkdocs` for generating documentation.

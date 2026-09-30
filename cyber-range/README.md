# Cyber Attack and Defense Simulation Platform

A Cyber Range platform designed for simulating cybersecurity attacks and defensive techniques in an isolated virtual environment.

The platform integrates Proxmox VE, Flask, Ansible, Kali Linux, and Splunk to provide an environment for cybersecurity training, attack simulation, automated defense, and security monitoring.

## Overview

The Cyber Attack and Defense Simulation Platform provides an isolated environment where cybersecurity attacks can be simulated and analyzed safely.

The platform combines

 Proxmox VE — Virtualization and Cyber Range infrastructure
 Flask — Centralized web-based control platform
 Ansible — Automation of attack and defense scenarios
 Kali Linux — Security testing and attack environment
 Splunk — Log collection, monitoring, and analysis
 HTML  CSS  JavaScript — Web interface

The system is designed to support Red Team and Blue Team activities within an isolated laboratory environment.

## Architecture

```text
                    ┌─────────────────────┐
                    │     Web Interface   │
                    │   HTMLCSSJS       │
                    └──────────┬──────────┘
                               │
                               ▼
                    ┌─────────────────────┐
                    │    Flask Platform   │
                    │ Central Controller  │
                    └──────────┬──────────┘
                               │
                 ┌─────────────┴─────────────┐
                 │                           │
                 ▼                           ▼
        ┌─────────────────┐        ┌─────────────────┐
        │    Proxmox VE   │        │     Ansible     │
        │ Virtualization  │        │   Automation    │
        └────────┬────────┘        └────────┬────────┘
                 │                          │
                 ▼                          ▼
        ┌─────────────────┐        ┌─────────────────┐
        │ Virtual Machines│        │ Attack  Defense│
        │                 │        │    Playbooks    │
        └────────┬────────┘        └─────────────────┘
                 │
                 ▼
        ┌─────────────────┐
        │     Splunk      │
        │ Monitoring &    │
        │ Log Analysis    │
        └─────────────────┘
```

## Main Components

### Proxmox VE

Proxmox VE is used as the virtualization platform for the Cyber Range infrastructure.

The laboratory environment contains separate virtual machines for the different roles in the simulation.

### Flask

The Flask application provides the centralized interface for controlling and managing the Cyber Range.

It communicates with the virtualization and automation components of the platform.

### Ansible

Ansible is used to automate attack and defense scenarios.

Example scenarios include

 Brute-force attack
 SQL Injection
 Defensive and monitoring actions

### Kali Linux

Kali Linux is used as the security testing environment for Red Team activities and attack simulation.

### Splunk

Splunk is used for collecting, monitoring, and analyzing security-related logs generated during the simulations.

## Project Structure

```text
├── app
│   ├── app.py
│   ├── config.py
│   ├── controllers
│   ├── templates
│   └── static
│
├── ansible
│   ├── playbooks
│   │   ├── bruteforce.yml
│   │   └── sqli.yml
│   └── inventory
│
├── labs
│   └── labs_content.json
│
├── docs
│   ├── architecture.png
│   └── screenshots
│
├── requirements.txt
├── .gitignore
└── README.md
```

## Example Attack Scenarios

### Brute Force

The platform provides a controlled environment for simulating brute-force attacks and observing their effects through the monitoring infrastructure.

### SQL Injection

SQL Injection can be simulated against the designated vulnerable environment in the Cyber Range.

The resulting activity can then be monitored and analyzed using the defensive and logging components.

## Laboratory Environment

The Cyber Range uses isolated virtual machines to separate the different components of the simulation.

Example infrastructure

 VM      Role                            
 ------  ------------------------------- 
 VM 100  Server  Platform               
 VM 101  Kali Linux  Attack Environment 
 VM 102  Victim Environment              

Snapshots can be used to restore the laboratory environment after completing a simulation.

## Installation

### Requirements

Before running the platform, the following components are required

 Proxmox VE
 Python 3
 Flask
 Ansible
 Kali Linux
 Splunk

### 1. Clone the repository

```bash
git clone httpsgithub.comYOUR_USERNAMEcyber-attack-defense-simulation-platform.git
cd cyber-attack-defense-simulation-platform
```

### 2. Create a Python virtual environment

```bash
python -m venv venv
```

Activate it

Windows

```bash
venvScriptsactivate
```

Linux

```bash
source venvbinactivate
```

### 3. Install Python dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure the environment

Create a `.env` file containing the required configuration.

Do not commit credentials, API tokens, passwords, or private keys to the repository.

### 5. Configure the Cyber Range

Create the required virtual machines in Proxmox VE and configure their networking according to the project architecture.

Configure

 Server VM
 Kali Linux VM
 Victim VM
 Required snapshots
 Ansible connectivity
 Splunk monitoring

### 6. Start the Flask application

```bash
python appapp.py
```

The application should then be accessible through the configured web interface.

## Security Notice

This project is intended for educational and authorized cybersecurity testing purposes.

Attack scenarios should only be executed inside the isolated laboratory environment or against systems for which you have explicit authorization.

Do not use the attack automation against systems that you do not own or have permission to test.

## Documentation

Additional documentation and screenshots can be found in the `docs` directory.

The complete graduation project report describes the architecture, implementation, virtual infrastructure, attack scenarios, defensive mechanisms, and monitoring components.

## Project Context

This project was developed as a graduation project for the Cybersecurity and Networking Department.

## Authors

 محمد إسماعيل الشعيبي
 عبد العزيز محمد الأهدل
 محمد علي الأشول
 محمد خالد المسيب

## Supervisor

أ. عصام بهلول

## License

This project is provided for educational and research purposes.

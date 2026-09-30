import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """
    إعدادات المنصة - مبسطة
    """
    # Flask Settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'change-this-in-production')
    DEBUG = os.getenv('DEBUG', 'False') == 'True'
    HOST = '0.0.0.0'  # الاستماع على جميع interfaces
    PORT = int(os.getenv('FLASK_PORT', 5000))
    
    # Proxmox Settings
    PROXMOX_HOST = os.getenv('PROXMOX_HOST', '192.168.10.254')
    PROXMOX_USER = os.getenv('PROXMOX_USER', 'root@pam')
    PROXMOX_TOKEN_NAME = os.getenv('PROXMOX_TOKEN_NAME', 'cyber-range-token')
    PROXMOX_TOKEN_VALUE = os.getenv('PROXMOX_TOKEN_VALUE', 'c72ac9a4-eb00-4511-95db-dfefab6775cb')
    PROXMOX_NODE = os.getenv('PROXMOX_NODE', 'pve')
    PROXMOX_VERIFY_SSL = False
    
    # VM IDs
    VM_SERVER = 100
    VM_ATTACKER = 101
    VM_VICTIM = 102
    
    # Network Settings
    NETWORK_SUBNET = '192.168.10.0/24'
    ATTACKER_IP = '192.168.10.10'
    VICTIM_IP = '192.168.10.20'
    SERVER_IP = '192.168.10.1'
    
    # Snapshot Settings
    SNAPSHOT_NAME = 'CLEAN_STATE'
    
    # Ansible Settings
    ANSIBLE_PLAYBOOKS_DIR = '/opt/cyber-range/automation/playbooks'
    ANSIBLE_TIMEOUT = 300
    
    # Splunk Settings
    SPLUNK_URL = 'http://192.168.10.1:8000'
    
    # Logging
    LOG_DIR = '/opt/cyber-range/logs'
    LOG_LEVEL = 'INFO'

import subprocess
import os
import json
from datetime import datetime

class AnsibleExecutor:
    def __init__(self, playbooks_dir='/opt/cyber-range/automation/playbooks'):
        """
        تهيئة Ansible Executor
        """
        self.playbooks_dir = playbooks_dir
        
        # التحقق من وجود المجلد
        if not os.path.exists(playbooks_dir):
            print(f"Warning: Playbooks directory not found: {playbooks_dir}")
            os.makedirs(playbooks_dir, exist_ok=True)
        
        print(f"✓ Ansible Executor initialized")
        print(f"  Playbooks directory: {playbooks_dir}")
    
    def check_playbook_exists(self, attack_type):
        """
        التحقق من وجود playbook
        """
        playbook_path = os.path.join(self.playbooks_dir, f"{attack_type}.yml")
        exists = os.path.exists(playbook_path)
        
        if exists:
            print(f"✓ Playbook found: {playbook_path}")
        else:
            print(f"✗ Playbook not found: {playbook_path}")
        
        return exists
    
    def run_attack_playbook(self, attack_type, target_ip, extra_vars=None):
        """
        تشغيل playbook هجوم محدد
        
        Args:
            attack_type: نوع الهجوم (bruteforce, sqli, exploit)
            target_ip: عنوان IP الهدف
            extra_vars: متغيرات إضافية (dict)
        
        Returns:
            dict: نتيجة التنفيذ
        """
        try:
            playbook_path = os.path.join(self.playbooks_dir, f"{attack_type}.yml")
            
            if not os.path.exists(playbook_path):
                return {
                    'success': False,
                    'message': f'Playbook not found: {playbook_path}'
                }
            
            # بناء الأمر
            cmd = [
                'ansible-playbook',
                playbook_path,
                '-e', f'target_ip={target_ip}',
                '-v'
            ]
            
            # إضافة متغيرات إضافية
            if extra_vars:
                for key, value in extra_vars.items():
                    cmd.extend(['-e', f'{key}={value}'])
            
            print(f"DEBUG: Running command: {' '.join(cmd)}")
            
            # تنفيذ الأمر
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            output = {
                'success': result.returncode == 0,
                'stdout': result.stdout,
                'stderr': result.stderr,
                'return_code': result.returncode,
                'attack_type': attack_type,
                'target_ip': target_ip,
                'timestamp': datetime.now().isoformat()
            }
            
            if result.returncode == 0:
                print(f"✓ Playbook '{attack_type}' executed successfully")
            else:
                print(f"✗ Playbook '{attack_type}' failed with return code {result.returncode}")
                print(f"Error: {result.stderr}")
            
            return output
        
        except subprocess.TimeoutExpired:
            return {
                'success': False,
                'message': 'Playbook execution timeout (300 seconds)',
                'attack_type': attack_type
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': str(e),
                'attack_type': attack_type
            }
    
    def list_available_playbooks(self):
        """
        عرض قائمة بجميع الـ playbooks المتاحة
        """
        try:
            playbooks = []
            
            if os.path.exists(self.playbooks_dir):
                for file in os.listdir(self.playbooks_dir):
                    if file.endswith('.yml') or file.endswith('.yaml'):
                        playbooks.append(file.replace('.yml', '').replace('.yaml', ''))
            
            return {
                'success': True,
                'playbooks': playbooks
            }
        
        except Exception as e:
            return {
                'success': False,
                'message': str(e)
            }

from flask import Flask, render_template, request, jsonify
from backend.core.proxmox_controller import ProxmoxController
from backend.core.ansible_executor import AnsibleExecutor
from config import Config
import json
import os
import traceback
import time
from datetime import datetime


app = Flask(__name__)
app.config.from_object(Config)


# معرفات الأجهزة
VM_IDS = {
    'server': Config.VM_SERVER,
    'attacker': Config.VM_ATTACKER,
    'victim': Config.VM_VICTIM
}


# تهيئة Controllers
try:
    proxmox = ProxmoxController(
        host=Config.PROXMOX_HOST,
        user=Config.PROXMOX_USER,
        token_name=Config.PROXMOX_TOKEN_NAME,
        token_value=Config.PROXMOX_TOKEN_VALUE
    )
    print("✓ Proxmox controller initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize Proxmox controller: {e}")
    proxmox = None


try:
    ansible = AnsibleExecutor()
    print("✓ Ansible executor initialized successfully")
except Exception as e:
    print(f"✗ Failed to initialize Ansible executor: {e}")
    ansible = None


# تحميل بيانات المختبرات
def load_labs_content():
    try:
        labs_file = os.path.join(os.path.dirname(__file__), 'labs_content.json')
        with open(labs_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, dict) and 'labs' in data:
                return data['labs']
            elif isinstance(data, list):
                return data
            else:
                print("Error: Invalid labs_content.json structure")
                return []
    except FileNotFoundError:
        print("Error: labs_content.json not found")
        return []
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in labs_content.json - {e}")
        return []


@app.route('/')
def index():
    """
    الصفحة الرئيسية - عرض قائمة المختبرات
    """
    labs = load_labs_content()
    return render_template('index.html', labs=labs)


@app.route('/lab/<int:lab_id>')
def lab_page(lab_id):
    """
    صفحة المختبر الفردي
    """
    labs = load_labs_content()
    lab = next((l for l in labs if l['id'] == lab_id), None)
    if not lab:
        return "Lab not found", 404
    return render_template('lab.html', lab=lab, vm_ids=VM_IDS)


@app.route('/api/start-lab', methods=['POST'])
def start_lab():
    """
    بدء المختبر:
    - Red Team: إعادة VMs وتشغيلها فقط (المستخدم ينفذ الهجوم يدوياً)
    - Blue Team: إعادة VMs، تشغيلها، وتنفيذ playbook الهجوم تلقائياً
    """
    try:
        print("=" * 70)
        print("=== DEBUG: start_lab called ===")
        
        if not proxmox:
            return jsonify({
                'success': False,
                'message': 'Proxmox controller not initialized'
            }), 500
        
        data = request.json
        lab_id = data.get('lab_id')
        lab_type = data.get('lab_type')
        
        print(f"DEBUG: Lab ID: {lab_id}, Type: {lab_type}")
        
        labs = load_labs_content()
        lab = next((l for l in labs if l['id'] == lab_id), None)
        
        if not lab:
            return jsonify({'success': False, 'message': 'Lab not found'}), 404
        
        results = []
        vms_to_start = [VM_IDS['attacker'], VM_IDS['victim']]
        
        # ========================================
        # المرحلة 1: إعادة جميع VMs للـ CLEAN_STATE
        # ========================================
        print("DEBUG: Phase 1 - Reverting VMs to CLEAN_STATE...")
        for vmid in vms_to_start:
            print(f"DEBUG: Reverting VM {vmid}")
            revert_result = proxmox.revert_snapshot(vmid)
            
            if not revert_result['success']:
                print(f"ERROR: Failed to revert VM {vmid}")
                return jsonify({
                    'success': False,
                    'message': f"Failed to revert VM {vmid}: {revert_result.get('message', 'Unknown error')}"
                }), 500
            
            results.append(f"VM {vmid}: Reverted to CLEAN_STATE")
            print(f"✓ VM {vmid}: Reverted successfully")
        
        # انتظار قصير بعد الـ revert
        time.sleep(3)
        
        # ========================================
        # المرحلة 2: تشغيل جميع VMs
        # ========================================
        print("DEBUG: Phase 2 - Starting VMs...")
        for vmid in vms_to_start:
            print(f"DEBUG: Starting VM {vmid}")
            start_result = proxmox.start_vm(vmid)
            
            if not start_result['success']:
                print(f"ERROR: Failed to start VM {vmid}")
                return jsonify({
                    'success': False,
                    'message': f"Failed to start VM {vmid}: {start_result.get('message', 'Unknown error')}"
                }), 500
            
            results.append(f"VM {vmid}: Started successfully")
            print(f"✓ VM {vmid}: Started successfully")
        
        # انتظار VMs حتى تكون جاهزة
        print("DEBUG: Waiting for VMs to boot...")
        time.sleep(10)
        
        # ========================================
        # المرحلة 3: تنفيذ playbook (فقط لـ Blue Team)
        # ========================================
        attack_result = None
        
        if lab_type == 'blue':
            print("DEBUG: Blue Team scenario detected")
            print("DEBUG: Will execute attack playbook to generate logs")
            
            if ansible:
                attack_type = lab.get('attack_type', 'bruteforce')
                target_ip = lab.get('target_ip', '192.168.10.20')
                
                print(f"DEBUG: Attack type: {attack_type}")
                print(f"DEBUG: Target IP: {target_ip}")
                
                # التحقق من وجود playbook
                if ansible.check_playbook_exists(attack_type):
                    print(f"DEBUG: Playbook '{attack_type}.yml' exists")
                    print("DEBUG: Waiting additional 10 seconds for SSH to be ready...")
                    time.sleep(10)
                    
                    print(f"DEBUG: Executing playbook: {attack_type}")
                    attack_result = ansible.run_attack_playbook(attack_type, target_ip)
                    
                    if attack_result.get('success'):
                        results.append(f"✓ Attack playbook '{attack_type}' executed successfully")
                        print(f"✓ Playbook executed successfully")
                    else:
                        error_msg = attack_result.get('message', 'Unknown error')
                        results.append(f"⚠ Attack playbook failed: {error_msg}")
                        print(f"✗ Playbook execution failed: {error_msg}")
                else:
                    results.append(f"⚠ Warning: Playbook '{attack_type}.yml' not found")
                    print(f"WARNING: Playbook '{attack_type}.yml' not found")
            else:
                results.append("⚠ Warning: Ansible executor not available")
                print("WARNING: Ansible executor not initialized")
        
        elif lab_type == 'red':
            print("DEBUG: Red Team scenario detected")
            print("DEBUG: No playbook will run - User will execute attack manually")
            results.append("Red Team mode: Open Kali console and execute attack manually")
        
        else:
            print(f"WARNING: Unknown lab type: {lab_type}")
        
        print("=" * 70)
        print("✓ Lab started successfully")
        print("=" * 70)
        
        return jsonify({
            'success': True,
            'results': results,
            'message': 'Lab started successfully',
            'lab_type': lab_type,
            'attack_executed': attack_result is not None and attack_result.get('success', False),
            'attack_output': attack_result,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"ERROR in start_lab: {error_trace}")
        return jsonify({
            'success': False,
            'message': str(e),
            'error_type': type(e).__name__,
            'traceback': error_trace
        }), 500


@app.route('/api/stop-lab', methods=['POST'])
def stop_lab():
    """
    إيقاف جميع أجهزة المختبر
    """
    try:
        print("=== DEBUG: stop_lab called ===")
        
        if not proxmox:
            return jsonify({
                'success': False,
                'message': 'Proxmox controller not initialized'
            }), 500
        
        results = []
        for vmid in [VM_IDS['attacker'], VM_IDS['victim']]:
            print(f"DEBUG: Stopping VM {vmid}")
            stop_result = proxmox.stop_vm(vmid)
            results.append(stop_result)
            
            if stop_result.get('success'):
                print(f"✓ VM {vmid} stopped")
            else:
                print(f"✗ Failed to stop VM {vmid}")
        
        return jsonify({
            'success': True,
            'results': results,
            'message': 'Lab stopped successfully'
        })
    
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"ERROR in stop_lab: {error_trace}")
        return jsonify({
            'success': False,
            'message': str(e),
            'traceback': error_trace
        }), 500


@app.route('/api/get-console-url', methods=['POST'])
def get_console_url():
    """
    الحصول على رابط الوصول للجهاز
    """
    try:
        print("=== DEBUG: get_console_url called ===")
        
        if not proxmox:
            print("ERROR: Proxmox controller is None")
            return jsonify({
                'success': False,
                'message': 'Proxmox controller not initialized. Check API credentials.'
            }), 500
        
        data = request.json
        console_type = data.get('type')
        
        print(f"DEBUG: Console type requested: {console_type}")
        
        if console_type == 'novnc':
            vmid = VM_IDS['attacker']
            print(f"DEBUG: Getting noVNC URL for VM {vmid}")
            
            try:
                result = proxmox.get_novnc_url(vmid)
                print(f"DEBUG: Proxmox result: {result}")
                
                return jsonify(result)
            
            except Exception as e:
                error_trace = traceback.format_exc()
                print(f"ERROR in get_novnc_url: {error_trace}")
                return jsonify({
                    'success': False,
                    'message': f'Error getting noVNC URL: {str(e)}',
                    'error_type': type(e).__name__,
                    'traceback': error_trace
                }), 500
        
        elif console_type == 'splunk':
            print(f"DEBUG: Returning Splunk dynamic config")
            return jsonify({
                'success': True,
                'use_dynamic_host': True,
                'console_type': 'splunk',
                'port': 8000,
                'message': 'Splunk Dashboard'
            })
        
        else:
            print(f"ERROR: Unknown console type: {console_type}")
            return jsonify({
                'success': False,
                'message': f'Unknown console type: {console_type}'
            }), 400
    
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"ERROR in get_console_url: {error_trace}")
        return jsonify({
            'success': False,
            'message': str(e),
            'error_type': type(e).__name__,
            'traceback': error_trace
        }), 500


@app.route('/api/vm-status/<int:vmid>')
def vm_status(vmid):
    """
    الحصول على حالة جهاز محدد
    """
    try:
        if not proxmox:
            return jsonify({
                'success': False,
                'message': 'Proxmox controller not initialized'
            }), 500
        
        if vmid not in [100, 101, 102]:
            return jsonify({
                'success': False,
                'message': 'Invalid VM ID'
            }), 400
        
        status = proxmox.get_vm_status(vmid)
        return jsonify(status)
    
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"ERROR in vm_status: {error_trace}")
        return jsonify({
            'success': False,
            'message': str(e),
            'traceback': error_trace
        }), 500


@app.route('/api/all-vms-status')
def all_vms_status():
    """
    الحصول على حالة جميع الأجهزة
    """
    try:
        if not proxmox:
            return jsonify({
                'success': False,
                'message': 'Proxmox controller not initialized'
            }), 500
        
        status = proxmox.get_all_vms_status()
        return jsonify(status)
    
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"ERROR in all_vms_status: {error_trace}")
        return jsonify({
            'success': False,
            'message': str(e),
            'traceback': error_trace
        }), 500


@app.route('/api/verify-lab', methods=['POST'])
def verify_lab():
    """
    التحقق من جاهزية المختبر
    """
    try:
        if not proxmox:
            return jsonify({
                'success': False,
                'message': 'Proxmox controller not initialized'
            }), 500
        
        data = request.json
        lab_id = data.get('lab_id')
        
        labs = load_labs_content()
        lab = next((l for l in labs if l['id'] == lab_id), None)
        
        if not lab:
            return jsonify({'success': False, 'message': 'Lab not found'}), 404
        
        # التحقق من الأجهزة
        vms_to_check = [VM_IDS['attacker'], VM_IDS['victim']]
        verification_results = []
        all_ok = True
        
        for vmid in vms_to_check:
            verify_result = proxmox.verify_snapshot_exists(vmid)
            if verify_result['success']:
                verification_results.append(f"✓ VM {vmid}: CLEAN_STATE snapshot exists")
            else:
                verification_results.append(f"✗ VM {vmid}: CLEAN_STATE snapshot missing")
                all_ok = False
        
        # التحقق من playbook في حالة Blue Team فقط
        if lab['type'] == 'blue' and ansible:
            attack_type = lab.get('attack_type')
            if ansible.check_playbook_exists(attack_type):
                verification_results.append(f"✓ Playbook '{attack_type}.yml' exists")
            else:
                verification_results.append(f"✗ Playbook '{attack_type}.yml' not found")
                all_ok = False
        
        return jsonify({
            'success': all_ok,
            'message': 'Lab is ready' if all_ok else 'Lab has missing components',
            'verification_results': verification_results
        })
    
    except Exception as e:
        error_trace = traceback.format_exc()
        print(f"ERROR in verify_lab: {error_trace}")
        return jsonify({
            'success': False,
            'message': str(e),
            'traceback': error_trace
        }), 500


@app.route('/dashboard')
def dashboard():
    """
    لوحة تحكم المنصة
    """
    return render_template('dashboard.html', vm_ids=VM_IDS)


@app.route('/api/system-info')
def system_info():
    """
    عرض معلومات النظام
    """
    return jsonify({
        'platform': 'Cyber Range Platform',
        'mode': 'Port Forwarding',
        'internal_network': '192.168.10.0/24',
        'alpine_ip': '192.168.10.1',
        'proxmox_internal_ip': Config.PROXMOX_HOST,
        'flask_port': Config.PORT,
        'splunk_port': 8000,
        'vm_ids': VM_IDS,
        'proxmox_status': 'connected' if proxmox else 'disconnected',
        'ansible_status': 'available' if ansible else 'unavailable'
    })


# Error handlers
@app.errorhandler(404)
def not_found(e):
    return jsonify({'success': False, 'message': 'Resource not found'}), 404


@app.errorhandler(500)
def internal_error(e):
    return jsonify({'success': False, 'message': 'Internal server error'}), 500


if __name__ == '__main__':
    print("=" * 70)
    print("🛡️  Cyber Range Platform")
    print("=" * 70)
    print(f"Mode: Port Forwarding")
    print(f"Internal Network: 192.168.10.0/24")
    print(f"Alpine Control Node: 192.168.10.1")
    print(f"Proxmox Internal IP: {Config.PROXMOX_HOST}")
    print("")
    print(f"VM Configuration:")
    print(f"  - Server (Control): VM {VM_IDS['server']}")
    print(f"  - Attacker (Kali):  VM {VM_IDS['attacker']}")
    print(f"  - Victim (Ubuntu):  VM {VM_IDS['victim']}")
    print("")
    print(f"Component Status:")
    print(f"  - Proxmox Controller: {'✓ Connected' if proxmox else '✗ Failed'}")
    print(f"  - Ansible Executor:   {'✓ Available' if ansible else '✗ Unavailable'}")
    print("")
    print("Lab Behavior:")
    print("  🔴 Red Team Labs:")
    print("     - VMs are prepared and started")
    print("     - User executes attacks manually via Kali console")
    print("     - No automated playbook execution")
    print("")
    print("  🔵 Blue Team Labs:")
    print("     - VMs are prepared and started")
    print("     - Attack playbook runs automatically to generate logs")
    print("     - User analyzes attack data in Splunk dashboard")
    print("")
    print("=" * 70)
    print("Required Port Forwarding on Proxmox Host:")
    print("  Port 5000 → 192.168.10.1:5000  (Flask Web App)")
    print("  Port 8000 → 192.168.10.254:8000 (Splunk)")
    print("")
    print("Access URLs:")
    print("  Platform:  http://<PROXMOX_IP>:5000")
    print("  Splunk:    http://<PROXMOX_IP>:8000")
    print("  Proxmox:   https://<PROXMOX_IP>:8006")
    print("=" * 70)
    
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)

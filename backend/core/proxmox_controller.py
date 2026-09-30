from proxmoxer import ProxmoxAPI
import time
import traceback
import urllib.parse

class ProxmoxController:
    def __init__(self, host, user, token_name, token_value):
        """
        التهيئة باستخدام API Token
        host: IP الداخلي للاتصال بـ Proxmox API (192.168.10.254)
        """
        try:
            self.proxmox = ProxmoxAPI(
                host,
                user=user,
                token_name=token_name,
                token_value=token_value,
                verify_ssl=False
            )
            self.node = 'pve'
            self.snapshot_name = 'CLEAN_STATE'
            self.host = host
            
            # اختبار الاتصال
            version = self.proxmox.version.get()
            print(f"✓ Connected to Proxmox {version['version']}")
            print(f"  Host: {self.host}")
            print(f"  Node: {self.node}")
            
        except Exception as e:
            print(f"✗ Failed to initialize Proxmox API: {e}")
            print(traceback.format_exc())
            raise
    
    def get_novnc_url(self, vmid):
        """
        الحصول على رابط noVNC مع vncticket مضمن في الـ URL
        """
        try:
            print(f"DEBUG: Getting noVNC URL for VM {vmid}")
            
            # التحقق من حالة الجهاز
            status_result = self.get_vm_status(vmid)
            
            if not status_result['success']:
                return {
                    'success': False,
                    'message': 'Cannot get VM status'
                }
            
            vm_status = status_result['status']['status']
            print(f"DEBUG: VM {vmid} status: {vm_status}")
            
            if vm_status != 'running':
                return {
                    'success': False,
                    'message': f'VM {vmid} is not running (status: {vm_status}). Please start the lab first.'
                }
            
            # الحصول على VNC proxy مع websocket
            print(f"DEBUG: Requesting VNC proxy for VM {vmid}")
            vnc_data = self.proxmox.nodes(self.node).qemu(vmid).vncproxy.post(websocket=1)
            print(f"DEBUG: VNC Data received: {vnc_data}")
            
            ticket = vnc_data.get('ticket')
            port = vnc_data.get('port')
            
            if not ticket or not port:
                return {
                    'success': False,
                    'message': f'Invalid VNC data: ticket={ticket}, port={port}'
                }
            
            # الحصول على اسم الجهاز
            vm_config = self.proxmox.nodes(self.node).qemu(vmid).config.get()
            vm_name = vm_config.get('name', f'VM-{vmid}')
            
            # ترميز ticket للـ URL
            encoded_ticket = urllib.parse.quote(ticket, safe='')
            
            # بناء websocket path مع vncticket مضمن
            websocket_path = f"api2/json/nodes/{self.node}/qemu/{vmid}/vncwebsocket?port={port}&vncticket={encoded_ticket}"
            
            print(f"DEBUG: VNC Details:")
            print(f"  - VM Name: {vm_name}")
            print(f"  - Port: {port}")
            print(f"  - Ticket (first 30 chars): {ticket[:30]}...")
            print(f"  - Encoded Ticket (first 40 chars): {encoded_ticket[:40]}...")
            print(f"  - WebSocket Path: {websocket_path}")
            
            # إرجاع البيانات للـ frontend ليبني الرابط بنفسه
            return {
                'success': True,
                'vmid': vmid,
                'vm_name': vm_name,
                'port': port,
                'ticket': encoded_ticket,
                'websocket_path': websocket_path,
                'node': self.node,
                'use_dynamic_host': True  # علامة لبناء الرابط في Frontend
            }
        
        except Exception as e:
            error_msg = f"Error in get_novnc_url: {str(e)}"
            error_trace = traceback.format_exc()
            print(f"ERROR: {error_msg}")
            print(error_trace)
            return {
                'success': False,
                'message': error_msg,
                'error_type': type(e).__name__,
                'traceback': error_trace
            }
    
    def revert_snapshot(self, vmid):
        """
        إعادة الجهاز لحالة CLEAN_STATE
        """
        try:
            print(f"DEBUG: Reverting VM {vmid} to {self.snapshot_name}")
            
            # الحصول على الحالة الحالية
            status = self.proxmox.nodes(self.node).qemu(vmid).status.current.get()
            current_status = status['status']
            
            print(f"DEBUG: Current VM status: {current_status}")
            
            # إيقاف الجهاز إذا كان يعمل
            if current_status == 'running':
                print(f"DEBUG: Stopping VM {vmid}...")
                self.proxmox.nodes(self.node).qemu(vmid).status.stop.post()
                time.sleep(5)
            
            # إعادة Snapshot
            print(f"DEBUG: Rolling back to snapshot {self.snapshot_name}...")
            self.proxmox.nodes(self.node).qemu(vmid).snapshot(self.snapshot_name).rollback.post()
            time.sleep(3)
            
            print(f"DEBUG: VM {vmid} successfully reverted to {self.snapshot_name}")
            return {
                'success': True,
                'message': f'VM {vmid} reverted to {self.snapshot_name}'
            }
        
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"ERROR in revert_snapshot: {error_trace}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def start_vm(self, vmid):
        """
        تشغيل الجهاز الافتراضي ومزامنة الوقت
        """
        try:
            print(f"DEBUG: Starting VM {vmid}...")
            self.proxmox.nodes(self.node).qemu(vmid).status.start.post()
            time.sleep(5)
            
            # محاولة مزامنة الوقت
            self.sync_vm_time(vmid)
            
            print(f"DEBUG: VM {vmid} started successfully")
            return {
                'success': True,
                'message': f'VM {vmid} started'
            }
        
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"ERROR in start_vm: {error_trace}")
            return {
                'success': False,
                'message': str(e)
            }

    def stop_vm(self, vmid):
        """
        إيقاف الجهاز الافتراضي
        """
        try:
            print(f"DEBUG: Stopping VM {vmid}...")
            self.proxmox.nodes(self.node).qemu(vmid).status.stop.post()
            
            print(f"DEBUG: VM {vmid} stopped successfully")
            return {
                'success': True,
                'message': f'VM {vmid} stopped'
            }
        
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"ERROR in stop_vm: {error_trace}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_vm_status(self, vmid):
        """
        الحصول على حالة الجهاز
        """
        try:
            status = self.proxmox.nodes(self.node).qemu(vmid).status.current.get()
            return {
                'success': True,
                'status': status
            }
        
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"ERROR in get_vm_status: {error_trace}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def get_all_vms_status(self):
        """
        الحصول على حالة جميع الأجهزة
        """
        try:
            vms = self.proxmox.nodes(self.node).qemu.get()
            vm_status = []
            
            for vm in vms:
                if vm['vmid'] in [100, 101, 102]:
                    vm_status.append({
                        'vmid': vm['vmid'],
                        'name': vm['name'],
                        'status': vm['status'],
                        'uptime': vm.get('uptime', 0),
                        'cpu': vm.get('cpu', 0),
                        'mem': vm.get('mem', 0),
                        'maxmem': vm.get('maxmem', 0)
                    })
            
            return {
                'success': True,
                'vms': vm_status
            }
        
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"ERROR in get_all_vms_status: {error_trace}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def verify_snapshot_exists(self, vmid):
        """
        التحقق من وجود CLEAN_STATE snapshot
        """
        try:
            print(f"DEBUG: Checking snapshot {self.snapshot_name} for VM {vmid}")
            
            snapshots = self.proxmox.nodes(self.node).qemu(vmid).snapshot.get()
            snapshot_names = [snap['name'] for snap in snapshots]
            
            print(f"DEBUG: Available snapshots for VM {vmid}: {snapshot_names}")
            
            if self.snapshot_name in snapshot_names:
                print(f"DEBUG: Snapshot {self.snapshot_name} exists for VM {vmid}")
                return {
                    'success': True,
                    'exists': True,
                    'snapshots': snapshot_names
                }
            else:
                print(f"WARNING: Snapshot {self.snapshot_name} not found for VM {vmid}")
                return {
                    'success': False,
                    'exists': False,
                    'message': f'Snapshot {self.snapshot_name} not found for VM {vmid}',
                    'available_snapshots': snapshot_names
                }
        
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"ERROR in verify_snapshot_exists: {error_trace}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def create_snapshot(self, vmid, snapshot_name=None):
        """
        إنشاء snapshot جديد
        """
        try:
            if snapshot_name is None:
                snapshot_name = self.snapshot_name
            
            print(f"DEBUG: Creating snapshot {snapshot_name} for VM {vmid}")
            
            from datetime import datetime
            self.proxmox.nodes(self.node).qemu(vmid).snapshot.post(
                snapname=snapshot_name,
                description=f'Cyber Range Clean State - {datetime.now().isoformat()}'
            )
            
            print(f"DEBUG: Snapshot {snapshot_name} created successfully for VM {vmid}")
            return {
                'success': True,
                'message': f'Snapshot {snapshot_name} created for VM {vmid}'
            }
        
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"ERROR in create_snapshot: {error_trace}")
            return {
                'success': False,
                'message': str(e)
            }
    
    def delete_snapshot(self, vmid, snapshot_name):
        """
        حذف snapshot
        """
        try:
            print(f"DEBUG: Deleting snapshot {snapshot_name} for VM {vmid}")
            
            self.proxmox.nodes(self.node).qemu(vmid).snapshot(snapshot_name).delete()
            
            print(f"DEBUG: Snapshot {snapshot_name} deleted successfully for VM {vmid}")
            return {
                'success': True,
                'message': f'Snapshot {snapshot_name} deleted for VM {vmid}'
            }
        
        except Exception as e:
            error_trace = traceback.format_exc()
            print(f"ERROR in delete_snapshot: {error_trace}")
            return {
                'success': False,
                'message': str(e)
            }


    def sync_vm_time(self, vmid):
        """
        مزامنة وقت الـ VM بعد البدء
        """
        try:
            print(f"DEBUG: Syncing time for VM {vmid}")
            
            # انتظر حتى يكون الجهاز جاهزاً
            time.sleep(10)
            
            # تنفيذ أمر مزامنة الوقت
            # يحتاج qemu-guest-agent مثبت على الـ VM
            result = self.proxmox.nodes(self.node).qemu(vmid).agent.post('exec', command='timedatectl set-ntp true')
            
            print(f"DEBUG: Time sync result: {result}")
            return {'success': True, 'message': f'Time synced for VM {vmid}'}
        
        except Exception as e:
            print(f"WARNING: Could not sync time for VM {vmid}: {e}")
            # لا نفشل العملية إذا فشلت مزامنة الوقت
            return {'success': False, 'message': str(e)}

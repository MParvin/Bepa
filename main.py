#!/usr/bin/env python3

import psutil
import ipaddress
import time
import subprocess
import os
from datetime import datetime
from dotenv import load_dotenv

class NetworkMonitor:
    def __init__(self):
        load_dotenv()
        ip_ranges_str = os.getenv('TARGET_IP_RANGES', '10.10.0.0/8,172.16.0.0/12,192.168.0.0/16')
        self.target_ranges = []
        
        for range_str in ip_ranges_str.split(','):
            range_str = range_str.strip()
            if range_str:
                try:
                    self.target_ranges.append(ipaddress.ip_network(range_str))
                except ValueError as e:
                    print(f"Warning: Invalid IP range '{range_str}': {e}")
        
        if not self.target_ranges:
            print("Warning: No valid IP ranges configured. Using defaults.")
            exit(1)
        
        # Parse exclude ranges
        exclude_ranges_str = os.getenv('EXCLUDE_IP_RANGES', '192.168.1.1/32')
        self.exclude_ranges = []
        
        for range_str in exclude_ranges_str.split(','):
            range_str = range_str.strip()
            if range_str:
                try:
                    self.exclude_ranges.append(ipaddress.ip_network(range_str))
                except ValueError as e:
                    print(f"Warning: Invalid exclude IP range '{range_str}': {e}")
        
        self.alerted_connections = set()
        
        if os.geteuid() != 0:
            print("Warning: Running without root privileges. Some connections might not be visible.")
    
    def send_notification(self, title, message):
        """Send desktop notification using notify-send (works on Fedora/GNOME)"""
        try:
            user = os.environ.get('SUDO_USER', os.environ.get('USER', 'root'))
            cmd = [
                'notify-send',
                '--urgency=critical',
                '--icon=dialog-warning',
                title,
                message
            ]
            if user != 'root' and os.geteuid() == 0:
                subprocess.run(['sudo', '-u', user, 'DISPLAY=:0'] + cmd, 
                             capture_output=True, text=True)
            else:
                subprocess.run(cmd, capture_output=True, text=True)
                
        except Exception as e:
            print(f"Failed to send notification: {e}")
    
    def is_target_ip(self, ip_str):
        """Check if IP address is in any of the target ranges"""
        try:
            ip = ipaddress.ip_address(ip_str)
            for target_range in self.target_ranges:
                if ip in target_range:
                    return True, str(target_range)
            return False, None
        except (ipaddress.AddressValueError, ValueError):
            return False, None
    
    def is_excluded_ip(self, ip_str):
        """Check if IP address is in any of the exclude ranges"""
        try:
            ip = ipaddress.ip_address(ip_str)
            for exclude_range in self.exclude_ranges:
                if ip in exclude_range:
                    return True, str(exclude_range)
            return False, None
        except (ipaddress.AddressValueError, ValueError):
            return False, None
    
    def get_process_name(self, pid):
        """Get process name from PID"""
        try:
            process = psutil.Process(pid)
            return process.name()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            return "Unknown"
    
    def monitor_connections(self):
        """Monitor network connections continuously"""
        print(f"Starting network monitor at {datetime.now()}")
        print(f"Monitoring connections to: {[str(r) for r in self.target_ranges]}")
        if self.exclude_ranges:
            print(f"Excluding connections to: {[str(r) for r in self.exclude_ranges]}")
        else:
            print("No IP ranges excluded from monitoring")
        print("Press Ctrl+C to stop\n")
        
        try:
            while True:
                connections = psutil.net_connections(kind='inet')
                
                for conn in connections:
                    if (conn.status == psutil.CONN_ESTABLISHED and 
                        conn.raddr and conn.laddr):
                        
                        remote_ip = conn.raddr.ip
                        remote_port = conn.raddr.port
                        local_port = conn.laddr.port
                        
                        is_excluded, excluded_range = self.is_excluded_ip(remote_ip)
                        if is_excluded:
                            continue
                        
                        is_target, matched_range = self.is_target_ip(remote_ip)
                        
                        if is_target:
                            conn_id = f"{remote_ip}:{remote_port}"

                            if conn_id not in self.alerted_connections:
                                process_name = self.get_process_name(conn.pid) if conn.pid else "Unknown"

                                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                                print(f"[{timestamp}] ALERT: Connection to {remote_ip}:{remote_port}")
                                print(f"  Process: {process_name} (PID: {conn.pid})")
                                print(f"  Matched range: {matched_range}")
                                print(f"  Local port: {local_port}")
                                print()

                                title = "Bepa Alert"
                                message = (f"Connection detected to monitored range!\n"
                                         f"Target: {remote_ip}:{remote_port}\n"
                                         f"Process: {process_name}\n"
                                         f"Range: {matched_range}")
                                self.send_notification(title, message)
                                self.alerted_connections.add(conn_id)

                active_connections = {f"{conn.raddr.ip}:{conn.raddr.port}"
                                    for conn in connections
                                    if conn.raddr and conn.status == psutil.CONN_ESTABLISHED}
                self.alerted_connections &= active_connections
                monitor_interval = int(os.getenv('MONITOR_INTERVAL', '2'))
                time.sleep(monitor_interval)
        except KeyboardInterrupt:
            print("\nStopping network monitor...")
        except Exception as e:
            print(f"Error during monitoring: {e}")

def main():
    print("Network Traffic Monitor for Fedora Linux")
    print("=" * 50)
    try:
        subprocess.run(['which', 'notify-send'], capture_output=True, check=True)
    except subprocess.CalledProcessError:
        print("Warning: notify-send not found. Install with then run this script again")
        print("Notifications may not work properly.\n")
    monitor = NetworkMonitor()
    monitor.monitor_connections()

if __name__ == "__main__":
    main()

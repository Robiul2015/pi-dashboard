import paramiko
import ipaddress

HOST = "10.10.11.155"
USER = "pi"
PASS = "999nadia"

def _assert_local_network(host):
    """Abort if the target host is not a private/local IP."""
    try:
        ip = ipaddress.ip_address(host)
        if not ip.is_private:
            raise SystemExit(f"ERROR: {host} is not a local/private IP. Refusing to connect to external hosts.")
    except ValueError:
        raise SystemExit(f"ERROR: {host!r} is a hostname, not a local IP. Use a private IP address only.")

def main():
    _assert_local_network(HOST)
    print("Connecting to Pi to check status...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(HOST, username=USER, password=PASS, timeout=10)

        print("=== DISK SPACE ===")
        stdin, stdout, stderr = ssh.exec_command("df -h /")
        print(stdout.read().decode())

        print("=== PROJECT FILES ===")
        stdin, stdout, stderr = ssh.exec_command("ls -la ~/pi-dashboard")
        print(stdout.read().decode())

        print("=== PYTHON PIP LIST ===")
        stdin, stdout, stderr = ssh.exec_command("~/pi-dashboard/venv/bin/pip list")
        print(stdout.read().decode())
    finally:
        ssh.close()

if __name__ == "__main__":
    main()

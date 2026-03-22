import paramiko
import ipaddress
import os
import sys

# Force UTF-8 output so Pi's pip progress bars don't crash on Windows console
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

HOST = "10.10.11.155"
USER = "pi"
PASS = "999nadia"
REMOTE_DIR = "/home/pi/pi-dashboard"

SKIP = {'.git', '__pycache__', 'venv', '.venv', 'deploy_pi.py', 'check_pi.py',
        '.env', 'token.json', 'credentials.json', 'dashboard.log'}

def _assert_local_network(host):
    """Abort if the target host is not a private/local IP."""
    try:
        ip = ipaddress.ip_address(host)
        if not ip.is_private:
            raise SystemExit(f"ERROR: {host} is not a local/private IP. Refusing to deploy to external hosts.")
    except ValueError:
        raise SystemExit(f"ERROR: {host!r} is a hostname, not a local IP. Use a private IP address only.")

def run_cmd(ssh, cmd):
    print(f"Running: {cmd}")
    stdin, stdout, stderr = ssh.exec_command(cmd)

    for line in iter(stdout.readline, ""):
        print(line, end="")
    for line in iter(stderr.readline, ""):
        print(f"ERR: {line}", end="")

    exit_status = stdout.channel.recv_exit_status()
    print(f"Exit status: {exit_status}\n")
    return exit_status

def sftp_upload_dir(sftp, local_dir, remote_dir):
    try:
        sftp.mkdir(remote_dir)
    except IOError:
        pass

    for item in os.listdir(local_dir):
        if item in SKIP:
            continue

        local_path = os.path.join(local_dir, item)
        remote_path = f"{remote_dir}/{item}"

        if os.path.isfile(local_path):
            print(f"Uploading {local_path} to {remote_path}")
            sftp.put(local_path, remote_path)
        elif os.path.isdir(local_path):
            sftp_upload_dir(sftp, local_path, remote_path)

def main():
    _assert_local_network(HOST)
    print(f"Connecting to {USER}@{HOST}...")
    ssh = paramiko.SSHClient()
    ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        ssh.connect(HOST, username=USER, password=PASS, timeout=10)
    except Exception as e:
        print(f"Failed to connect: {e}")
        return

    print("Connected successfully!")

    run_cmd(ssh, "sudo apt-get update && sudo apt-get install -y python3-venv python3-pip git")

    print("Opening SFTP session...")
    sftp = ssh.open_sftp()

    run_cmd(ssh, f"mkdir -p {REMOTE_DIR}")

    local_workspace = os.path.dirname(os.path.abspath(__file__))
    sftp_upload_dir(sftp, local_workspace, REMOTE_DIR)

    run_cmd(ssh, f"if [ ! -f {REMOTE_DIR}/.env ]; then cp {REMOTE_DIR}/.env.example {REMOTE_DIR}/.env; fi")

    sftp.close()

    print("Setting up remote virtual environment...")
    run_cmd(ssh, f"cd {REMOTE_DIR} && python3 -m venv venv")
    run_cmd(ssh, f"cd {REMOTE_DIR} && mkdir -p tmp && TMPDIR={REMOTE_DIR}/tmp ./venv/bin/pip install --no-cache-dir -r requirements.txt")

    print("Installing Waveshare 3.5 LCD Drivers...")
    run_cmd(ssh, "rm -rf LCD-show && git clone https://github.com/waveshare/LCD-show.git")
    run_cmd(ssh, "chmod +x LCD-show/LCD35-show")

    print("Executing LCD driver setup. THE PI WILL REBOOT NOW...")
    try:
        ssh.exec_command("cd LCD-show && sudo ./LCD35-show")
    except Exception:
        pass

    print("Deployment script finished. The Pi should be rebooting with the Waveshare screen active!")
    ssh.close()

if __name__ == "__main__":
    main()

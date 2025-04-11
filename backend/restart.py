import os
import sys
import subprocess
import time
import signal

def restart_system():
    """Reset the database and restart the web server."""
    
    # Get parent directory
    current_dir = os.path.dirname(os.path.abspath(__file__)) or '.'
    
    # Step 1: Kill any running web server processes
    print("Looking for running web server processes...")
    try:
        # Find processes running web_server.py
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        processes = result.stdout.split('\n')
        server_processes = []
        
        for process in processes:
            if 'python web_server.py' in process and 'grep' not in process:
                parts = process.split()
                if len(parts) > 1:
                    pid = parts[1]
                    server_processes.append(pid)
        
        if server_processes:
            print(f"Found {len(server_processes)} web server processes: {', '.join(server_processes)}")
            for pid in server_processes:
                print(f"Terminating process {pid}...")
                try:
                    os.kill(int(pid), signal.SIGTERM)
                except (ProcessLookupError, PermissionError) as e:
                    print(f"Error terminating process {pid}: {e}")
        else:
            print("No running web server processes found.")
    except Exception as e:
        print(f"Error checking for processes: {e}")
    
    # Step 2: Wait a moment for processes to terminate
    print("Waiting for processes to terminate...")
    time.sleep(2)
    
    # Step 3: Reset the database
    print("Resetting the database...")
    try:
        # Use the correct path for reset_db.py in the backend directory
        reset_script = os.path.join(current_dir, 'reset_db.py')
        subprocess.run(['python', reset_script, '--auto'], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error resetting database: {e}")
        return
    
    print("\nRestart complete! The system has been reset.")
    print("\nTo start the web server again, run:")
    print("python web_server.py")

if __name__ == "__main__":
    restart_system()
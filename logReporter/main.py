# This is a sample Python script.

# Press Shift+F10 to execute it or replace it with your code.
# Press Double Shift to search everywhere for classes, files, tool windows, actions, and settings.

# SFTP server details
from datetime import datetime

import paramiko as paramiko
from flask import app, render_template, Flask

app = Flask(__name__)

sftp_servers = [
    {'name': 'sftp-1', 'hostname': '127.0.0.1', 'port': 2222, 'username': 'sftp', 'password': 'pass',
     'directory': '/uploads/'},
    {'name': 'sftp-2', 'hostname': '127.0.0.1', 'port': 2200, 'username': 'sftp', 'password': 'pass',
     'directory': '/uploads/'},
    {'name': 'sftp-3', 'hostname': '127.0.0.1', 'port': 2201, 'username': 'sftp', 'password': 'pass',
     'directory': '/uploads/'},
]


def convert_to_datetime(date_str, time_str):
    try:
        return datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M:%S")
    except ValueError:
        return datetime.min


def fetch_logs_from_server(server):
    logs = {}
    try:
        transport = paramiko.Transport((server['hostname'], server['port']))
        transport.connect(username=server['username'], password=server['password'])

        sftp = paramiko.SFTPClient.from_transport(transport)
        files = sftp.listdir(server['directory'])

        for file in files:
            if file.endswith('.txt'):  # Ensure we're only processing .txt files
                with sftp.open(server['directory'] + file, 'r') as f:
                    logs[file] = f.read()  # Read the file as a string

        sftp.close()
        transport.close()
    except Exception as e:
        print(f"Failed to fetch logs from {server['hostname']}: {e}")

    return logs


@app.route('/logs', methods=['GET'])
def fetch_logs():
    all_logs = {}

    for server in sftp_servers:
        logs = fetch_logs_from_server(server)
        server_key = server['name']

        # Dictionary to hold logs organized by sender
        sender_logs = {}
        sender_counts = {}

        for filename, content in logs.items():
            content_str = content if isinstance(content, str) else content.decode('utf-8').strip()

            # Split the content into date, time, and sender name
            try:
                date, time, sender_name = content_str.split(', ')
                log_entry = {
                    'filename': filename,
                    'date': date,
                    'time': time,
                    'senderName': sender_name,
                    'content': content_str
                }
            except ValueError:
                # Handle cases where content is not in the expected format
                log_entry = {
                    'filename': filename,
                    'content': content_str,  # Fallback to raw content if split fails
                }

            # Initialize the sender's log array and count if they don't exist
            if sender_name not in sender_logs:
                sender_logs[sender_name] = []
                sender_counts[sender_name] = 0

            # Append the log entry to the correct sender's log array
            sender_logs[sender_name].append(log_entry)
            sender_counts[sender_name] += 1

        # Sort logs for each sender by date and time
        for sender_name in sender_logs:
            sender_logs[sender_name].sort(key=lambda x: convert_to_datetime(x.get('date', '1970-01-01'), x.get('time', '00:00:00')))

        # Add the sender logs and counts to the server's key
        all_logs[server_key] = {
            'logs': sender_logs,
            'counts': sender_counts
        }

    return all_logs


@app.route('/logs/html', methods=['GET'])
def fetch_logs_html():
    logs = fetch_logs()
    return render_template('logs_report.html', all_logs=logs)


# Press the green button in the gutter to run the script.
if __name__ == '__main__':
    app.run(debug=True)

# See PyCharm help at https://www.jetbrains.com/help/pycharm/

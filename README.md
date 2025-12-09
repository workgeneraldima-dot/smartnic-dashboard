# FPGA Smart NIC DDoS Dashboard

FastAPI-based web dashboard for monitoring FPGA Smart NIC DDoS detection alerts. The backend listens for UDP messages from the FPGA, persists events to MySQL, and exposes REST APIs consumed by the Bootstrap/Chart.js frontend.

## Features
- UDP listener parses CSV/JSON alerts from the FPGA and stores them in MySQL.
- REST API for events, statistics, blocked IPs, and configuration.
- Responsive Bootstrap UI with charts (Chart.js) and auto-refreshing tables.
- Settings page to adjust thresholds and ML toggle values.

## Getting Started (step by step)
These instructions assume no prior FastAPI or MySQL experience. Commands are shown for Linux/macOS shells; Windows PowerShell is similar.

1) **Install prerequisites**
   - Python 3.10+ (`python --version` to confirm).
   - A running MySQL or MariaDB server you can connect to.
   - Git (if you need to clone the repo).

2) **Create a database/user in MySQL** (do this once)
   - If your MySQL user has `CREATE DATABASE` privileges, the app will auto-create the `smartnic_dashboard` database and all tables at startup (default behavior). You can skip the manual SQL and just ensure your `DATABASE_URL` user has permissions.
   - Otherwise, run these commands once to provision a dedicated user and database:
     ```sql
     CREATE DATABASE smartnic_dashboard;
     CREATE USER 'smartnic'@'localhost' IDENTIFIED BY 'smartnic_pass';
     GRANT ALL PRIVILEGES ON smartnic_dashboard.* TO 'smartnic'@'localhost';
     FLUSH PRIVILEGES;
     ```

3) **Clone the project and enter the folder**
   ```bash
   git clone <your-fork-or-repo-url> smartnic-dashboard
   cd smartnic-dashboard
   ```

4) **(Recommended) Create and activate a virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows use: .venv\Scripts\activate
   ```

5) **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```

6) **Set environment variables** (replace credentials with your own)
   ```bash
   export DATABASE_URL="mysql+pymysql://smartnic:smartnic_pass@localhost:3306/smartnic_dashboard"
   export UDP_HOST=0.0.0.0
   export UDP_PORT=5005
   # Optional: change API prefix or disable auto table creation
   # export API_PREFIX="/api"
   # export AUTO_CREATE_TABLES=true
   ```
   > Tip: Add these exports to your shell profile so you do not retype them.

7) **Start the web server**
   ```bash
   uvicorn app:app --reload --host 0.0.0.0 --port 8000
   ```
   On startup the app will create the tables automatically if `AUTO_CREATE_TABLES=true` (default).

8) **Open the dashboard**
   Visit `http://localhost:8000/` in your browser. The navigation bar links to Dashboard, Live Events, Blocked IPs, and Settings.

9) **Send a test FPGA alert (optional)**
   In a separate terminal, you can simulate the FPGA by sending a UDP line:
   ```bash
   echo "2025-12-10T20:15:34Z,10.0.0.5,192.168.1.10,SYN_FLOOD,BLOCKED,15000" | nc -u -w1 127.0.0.1 5005
   ```
   Refresh the dashboard to see the event appear and the IP listed under Blocked IPs.

10) **Stop the server**
    Press `Ctrl+C` in the terminal running `uvicorn`.

## FPGA Payload Format
Example UDP payload:
```
2025-12-10T20:15:34Z,10.0.0.5,192.168.1.10,SYN_FLOOD,BLOCKED,15000
```
Fields: timestamp, source_ip, destination_ip, attack_type, decision, packet_count.

## Database Schema
SQLAlchemy models define the required tables:
- `events`: individual detection events.
- `blocked_ips`: active/unblocked sources flagged by the FPGA.
- `config`: key/value settings (e.g., thresholds, ML enable flag).

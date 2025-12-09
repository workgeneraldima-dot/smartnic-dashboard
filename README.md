# SmartNIC DDoS Dashboard

A FastAPI-based dashboard for monitoring FPGA Smart NIC DDoS detection events. It exposes REST APIs, a Bootstrap-based UI, and a UDP listener to receive event logs from the FPGA.

## Features
- UDP listener for FPGA log lines (CSV or JSON)
- MySQL/SQLite database storage for events, blocked IPs, and configuration
- REST APIs for events, stats, blocked IPs, and configuration management
- Bootstrap dashboard with Chart.js visualizations and live tables

## Running locally
1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set environment variables as needed:
   - `DATABASE_URL` (default: `sqlite:///./data.db`)
   - `FPGA_UDP_HOST` (default: `0.0.0.0`)
   - `FPGA_UDP_PORT` (default: `5005`)
   - `LISTENER_ENABLED` (default: `true`)
3. Start the server:
   ```bash
   uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
4. Open http://localhost:8000/ in your browser.

## Simulating FPGA traffic
Send a CSV log line over UDP:
```bash
echo "2025-12-10T20:15:34Z,10.0.0.5,192.168.1.10,SYN_FLOOD,BLOCKED,15000" \
  | nc -u -w1 127.0.0.1 5005
```

## Project structure
- `app/main.py` – FastAPI application and startup hooks
- `app/routes_api.py` – REST API endpoints
- `app/routes_web.py` – Web routes and template rendering
- `app/fpga_listener.py` – UDP listener for FPGA events
- `app/models.py` – SQLAlchemy models
- `app/db.py` – Database engine and session utilities
- `templates/` – Bootstrap/Jinja HTML templates
- `static/` – JavaScript assets for the frontend

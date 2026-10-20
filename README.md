
# Solar OT Watchman

A local prototype for monitoring simulated solar-farm inverter telemetry and detecting selected Operational Technology (OT) security events.

## 1. Project Overview

Solar OT Watchman is a Python-based prototype designed to demonstrate how a solar farm's inverter network can be monitored for unusual activity.

The project simulates three solar inverters communicating over Modbus TCP. A telemetry poller collects readings, a rule-based monitor evaluates events, and a Streamlit dashboard displays inverter data, device inventory, security alerts, and event history.

**Important:** This project runs in a controlled local environment using simulated devices and synthetic security events. It does not connect to or monitor a real solar farm.

## 2. Objectives

- Monitor telemetry from simulated solar inverters.
- Maintain an inventory of known devices.
- Detect unknown devices and suspicious Modbus write activity.
- Identify sensitive activity occurring outside configured maintenance hours.
- Detect bursts of events within a short period.
- Display telemetry and security events through a dashboard.
- Demonstrate basic OT monitoring concepts in a safe local lab.

## 3. Features

### Inverter Simulation

- Three simulated solar inverters: `INV-01`, `INV-02`, and `INV-03`.
- Local Modbus TCP communication.
- Simulated power, voltage, and setpoint register values.

### Telemetry Monitoring

- Periodic polling of the simulated inverters.
- Recording of telemetry and events in JSON Lines (`.jsonl`) files.
- Display of the latest recorded inverter readings.

### Security Event Detection

The rule-based monitor supports the following alert categories:

| Alert | Description |
|---|---|
| `UNKNOWN_DEVICE` | An event references a device that is not in the configured inventory. |
| `UNAUTHORIZED_WRITE` | A Modbus write event is observed and flagged for investigation. |
| `OUTSIDE_MAINTENANCE_WINDOW` | Sensitive activity occurs outside configured maintenance hours. |
| `TRAFFIC_BURST` | Multiple events occur within a short configured time window. |

These alerts are rule-based indicators. They do not independently prove that a real attack has occurred.

### Streamlit Dashboard

- Inverter inventory and configured endpoints.
- Power, voltage, and setpoint readings.
- Event and alert counts.
- Security alert summaries.
- Recent event history.

## 4. Technology Stack

- **Python** — application logic and monitoring.
- **PyModbus** — simulated Modbus TCP communication.
- **Streamlit** — dashboard interface.
- **Pandas** — data handling and display.
- **JSON Lines** — event logging.
- **Standalone Python test scripts** — basic functional validation.

## 5. Project Structure

```text
solar-ot-watchman/
├── app.py
├── config.py
├── requirements.txt
├── README.md
├── sensor/
│   ├── monitor.py
│   └── poller.py
├── simulators/
│   └── inverter.py
├── tests/
│   ├── test_inverter.py
│   ├── test_monitor.py
│   ├── test_unauthorized_write.py
│   └── test_unknown_device.py
└── logs/
    ├── events.jsonl
    └── test_events.jsonl
```

## 6. Requirements

- Python 3.12 recommended.
- pip package manager.
- Linux or WSL Ubuntu environment.
- Python dependencies listed in `requirements.txt`.

## 7. Installation and Setup

### Step 1: Open the project directory

```bash
cd ~/solar-ot-watchman
```

### Step 2: Create a virtual environment

```bash
python3 -m venv .venv
```

### Step 3: Activate the virtual environment

```bash
source .venv/bin/activate
```

### Step 4: Install dependencies

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

The `requirements.txt` file specifies the versions used by this project.

## 8. Running the Prototype

Run each component in a separate terminal. In every terminal, navigate to the project directory and activate the virtual environment.

### Step 1: Start the simulated inverters

```bash
cd ~/solar-ot-watchman
source .venv/bin/activate
PYTHONPATH=. python simulators/inverter.py
```

Keep this terminal running. The simulators use local TCP ports `5020`, `5021`, and `5022`.

### Step 2: Start the Streamlit dashboard

Open another terminal and run:

```bash
cd ~/solar-ot-watchman
source .venv/bin/activate
streamlit run app.py
```

Open the local URL printed in the terminal. Streamlit commonly uses:

`http://localhost:8501`

If the default port is occupied, Streamlit may select another port. Use the URL printed in the terminal. For example, the dashboard may be available at `http://localhost:8502`.

### Step 3: Start the telemetry poller

Open a third terminal and run:

```bash
cd ~/solar-ot-watchman
source .venv/bin/activate
PYTHONPATH=. python sensor/poller.py
```

The poller collects readings from the simulated inverters and records events in the log files.

Keep the simulator running while the poller is active.

### Stopping the application

Press `Ctrl+C` in the terminal running a component to stop it.

## 9. Running the Tests

Run the following commands from the project root with the virtual environment activated.

### Inverter simulator test

```bash
PYTHONPATH=. python tests/test_inverter.py
```

### Monitor rule tests

```bash
PYTHONPATH=. python tests/test_monitor.py
```

### Unauthorized-write test

```bash
PYTHONPATH=. python tests/test_unauthorized_write.py
```

### Unknown-device test

```bash
PYTHONPATH=. python tests/test_unknown_device.py
```

The monitor tests cover normal reads, unknown devices, write events, sensitive activity outside maintenance hours, and traffic bursts.

The unauthorized-write test modifies a setpoint on a local simulated inverter and attempts to restore the original value during cleanup. Run it only against the included local simulator.

## 10. Configuration

The `config.py` file defines the known devices, allowed hosts, maintenance window, and enabled alert categories.

The prototype uses the following local inverter endpoints:

| Device | Host | Port |
|---|---|---:|
| `INV-01` | `127.0.0.1` | `5020` |
| `INV-02` | `127.0.0.1` | `5021` |
| `INV-03` | `127.0.0.1` | `5022` |

The configured maintenance window is 09:00–17:00. The monitor uses this configuration when evaluating applicable sensitive activity.

These endpoints are loopback addresses for local simulation, not real equipment addresses.

## 11. Event Logs

Events are stored in JSON Lines (`.jsonl`) files under the `logs/` directory.

Each line represents an individual JSON event. The active logs can contain telemetry records and security-related events, which the dashboard uses to display recent activity.

**Data freshness:** The dashboard displays recorded data. If the poller is stopped, the displayed telemetry is historical and should not be interpreted as a live reading.

## 12. Detection Logic

The prototype uses predefined rules rather than a machine-learning model.

- **Device inventory check:** Compares the event's device identity with the configured list of known devices.
- **Write-event detection:** Flags observed Modbus write activity for investigation.
- **Maintenance-window check:** Evaluates applicable sensitive activity against the configured hours.
- **Traffic-burst detection:** Identifies multiple events occurring within a short time window.

These rules demonstrate basic monitoring concepts. They are not a replacement for production-grade OT network monitoring, authentication, access control, or incident response.

## 13. Limitations

- All devices are simulated locally.
- The prototype does not passively capture arbitrary network packets.
- The monitor evaluates events provided to it; it does not automatically discover every device on a real network.
- Detection depends on the configured rules and available event data.
- The dashboard displays logged events and may show historical readings when polling is inactive.
- The system has not been validated for deployment in a production solar farm.

## 14. Safety Considerations

This project is intended for an isolated local lab.

- Use the included simulator for testing.
- Do not direct test scripts at real industrial equipment.
- Do not interpret a generated alert as conclusive evidence of an attack.
- Keep the prototype separate from operational solar-farm networks.

## 15. Future Improvements

Potential future improvements include:

- Configurable alert thresholds and maintenance schedules.
- More detailed event correlation and severity scoring.
- Exportable incident reports.
- Improved test coverage and automated test execution.
- Integration with a dedicated packet-capture or monitoring system in an authorized lab.
- Authentication and role-based access for dashboard users.

## 16. License

No license has been specified for this project yet.

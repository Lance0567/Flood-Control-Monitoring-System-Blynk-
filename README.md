# 🌊 IoT-Based Flood Monitoring and Real-Time Early Warning System
**A Solar-Powered, Multi-Sensor Prototype for Environmental Observation**

![Status](https://img.shields.io/badge/status-active-success)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi%204-blue)
![Language](https://img.shields.io/badge/language-Python%203-yellow)
![Connectivity](https://img.shields.io/badge/connectivity-GSM%20%7C%20Cloudflare-orange)

## 📌 Project Overview
This project is a functional engineering prototype I designed and built for real-time water level observation and automated alerting. Modeled specifically for the environmental constraints of the **Yawa River in Legazpi City**, the system moves beyond simple monitoring by implementing a hybrid detection logic that combines ultrasonic distance polling with visual marker validation.

Unlike standard IoT projects, I designed this system for **functional sustainability** in off-grid locations, utilizing a dedicated solar power regulation circuit and a GSM-based failover for critical SMS alerts.

---

## 🧠 System Architecture & Logic Flow
I utilized a Raspberry Pi 4 as the central compute node to manage concurrent threads for sensor polling, image processing, and remote telemetry.



### Detection Strategy
1.  **Primary Sensing:** Continuous polling via an A02YYUW waterproof ultrasonic sensor to measure distance to the water surface.
2.  **Visual Validation:** A NoIR camera captures frames of physical gauge markers to confirm level breaches visually.
3.  **Rate-of-Rise Calculation:** The firmware calculates the velocity of the rising water to determine the urgency of the alert.
4.  **Tiered Response:** Logic-driven SMS alerts (Early Warning, Critical, or Forced Evacuation) are dispatched via the SIM800L GSM module.

---

## 🧰 Hardware Design Decisions

| Component | Choice | Engineering Reasoning |
| :--- | :--- | :--- |
| **Controller** | Raspberry Pi 4 | Necessary for handling the Flask-based MJPEG stream and Python-based image processing concurrently. |
| **Distance Sensor** | A02YYUW Ultrasonic | Waterproof (IP67) and non-contact; avoids debris interference common in river environments. |
| **Camera** | Pi Camera v3 NoIR | Allows for effective nighttime monitoring when paired with IR illumination, without using visible light. |
| **Telemetry** | SIM800L GSM | Provides a redundant communication path for SMS alerts when local internet backhauls fail during storms. |
| **Power** | Solar + 5V Regulated | Ensures 24/7 operation in remote riverside locations without grid access. |

> **Technical Note:** To protect the Raspberry Pi’s 3.3V GPIO pins from the 5V logic of the GSM module and sensors, I implemented **resistor-based voltage dividers** across all high-voltage signal lines.

---

## 💻 Software Implementation

The system runs a custom Python stack I wrote for low-latency data availability and secure remote access:

* **Logic Engine:** Python 3 utilizing `Picamera2` and GPIO interrupts.
* **Web Stack:** A **Flask** server handles the MJPEG live stream and serves a local web gallery.
* **IoT Integration:** **Blynk** serves as the mobile control interface and real-time data visualization layer.
* **Secure Tunneling:** **Cloudflare Tunnel** securely exposes the local Flask server to the public web via HTTPS without the security risks of port forwarding.

---

## 🛠️ Implementation Challenges & Trade-offs
* **Power Management:** The Pi 4’s high power draw necessitated an **on-demand capture model**. The camera and high-bandwidth streaming only trigger during specific user-requested intervals or when the ultrasonic sensor detects a threshold breach.
* **Signal Integrity:** During GSM transmission, the SIM800L creates significant current spikes. I had to integrate large decoupling capacitors across the module's power rails to prevent system brownouts and reboots during alert dispatches.
* **Environmental Noise:** Ultrasonic sensors can produce "ghost" readings from surface ripples or heavy rain. To address this, the firmware implements a moving average filter to ensure data stability before triggering logic states.

---

## 📈 Testing & Validation Metrics
I evaluated the prototype based on strict operational criteria:
* **Day vs. Night Reliability:** Validated the NoIR camera's ability to distinguish level markers in zero-visible-light conditions using IR.
* **Response Time:** Measured the latency between a detected water level breach and the receipt of an SMS alert on mobile networks.
* **Power Autonomy:** Tested the solar-battery cycle under continuous operation to validate functional sustainability over multiple days.

---

## 📂 Project Structure
```text
.
├── main.py               # Main logic & sensor polling thread
├── combined_server.py    # Flask server (MJPEG stream + image gallery)
├── camera_module.py      # PiCamera abstraction for capture/stream
├── captured_photos.py    # Local storage & timestamping logic
├── static/               # Web assets and photo storage
└── requirements.txt      # Dependency list
```
---

## 🚀 Getting Started

### 1 Clone the Repository
```bash
git clone https://github.com/Lance0567/Flood-Control-Monitoring-System-Blynk-.git
cd ust-flood-control
```

### 2. Install Dependencies
```bash
pip3 install -r requirements.txt
```

### 3. Run the Application
```bash
python3 main.py
```

### 4. Start Cloudflare Tunnel
```bash
cloudflared tunnel run myblnktunnel
```

## 📱 Blynk Configuration
| Widget | Virtual Pin | Description |
| :--- | :--- | :--- |
| `Button (Push)` | V0 | Capture photo |
| `Button (Switch)` | V1 | Start / stop live stream |
| `Video Stream` | — | Live camera feed |
| `Gallery / WebView` | — | Captured images |

### Video Stream URL:
```url
[https://pi.ustfloodcontrol.site/livecam
```

## 🔐 Security Notes
* No ports are exposed on the router
* All traffic is encrypted via HTTPS
* Cloudflare handles authentication and routing

## 🎓 Academic Use
This prototype is suitable for:
* Thesis and capstone projects
* Disaster risk reduction research
* Smart city and environmental monitoring studies
* Technical demonstrations and system defense

## 🛠️ Future Improvements
* Water level sensor integration
* AI-based flood detection
* SMS / push alert notifications
* Historical image and data analytics
* Edge-based motion detection

## 📜 License
* This project is licensed under the MIT License.
* You are free to use, modify, and distribute this work with attribution.

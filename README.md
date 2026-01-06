# 🌊 UST Flood Control Monitoring System  
**Solar-Powered IoT Flood Monitoring with Real-Time Camera Streaming**

![Status](https://img.shields.io/badge/status-active-success)
![Platform](https://img.shields.io/badge/platform-Raspberry%20Pi-blue)
![IoT](https://img.shields.io/badge/IoT-Blynk-green)
![License](https://img.shields.io/badge/license-MIT-lightgrey)

---

## 📌 Project Overview

The **UST Flood Control Monitoring System** is a **solar-powered, Raspberry Pi–based IoT prototype** designed for **real-time flood monitoring and visual inspection**.

The system integrates:
- Live camera streaming  
- Remote photo capture  
- Cloud-based dashboard (Blynk)  
- Secure public access via Cloudflare Tunnel  
- Off-grid solar power system  

This project is intended for **academic research, disaster preparedness, and smart city flood mitigation applications**.

---

## 🎯 Objectives

- Provide **real-time visual monitoring** of flood-prone areas  
- Enable **remote access** from any device or network  
- Operate using **renewable solar energy**  
- Centralize control and monitoring using **Blynk**  
- Serve as a **research-grade prototype** for flood early warning systems  

---

## 🧠 System Architecture
```text
Solar Panel
↓
Charge Controller → Battery
↓
Raspberry Pi
├─ Camera Module
├─ Flask Streaming Server
├─ Blynk Control Logic
└─ Cloudflare Tunnel
↓
Blynk.Console (Desktop) / Blynk.App (Mobile)
```

## 🧰 Hardware Components

- Raspberry Pi 4  
- Raspberry Pi Camera Module  
- Solar Panel  
- Solar Charge Controller  
- Rechargeable Battery  
- Weatherproof Electrical Enclosure  
- Status LEDs  
- Mounting Pole & Bracket  

---

## 💻 Software Stack

| Component | Technology |
|---------|-----------|
| OS | Raspberry Pi OS |
| Programming Language | Python 3 |
| Camera | Picamera2 |
| Web Server | Flask |
| Streaming | MJPEG |
| IoT Dashboard | Blynk |
| Secure Access | Cloudflare Tunnel |

---

## 📸 Key Features

### ✅ Live Camera Streaming
- Real-time MJPEG video feed  
- Accessible via permanent HTTPS URL  

### ✅ Remote Photo Capture
- Triggered via **Blynk Virtual Pin (V0)**  
- Images saved locally with **timestamp**  
- Ready for gallery / carousel display  

### ✅ Live Stream Control
- Toggle live camera server via **Virtual Pin (V1)**  

### ✅ Secure Public Access
- Cloudflare Tunnel exposes the server without port forwarding  
- Custom domain:
https://pi.ustfloodcontrol.site

### ✅ Cross-Platform Dashboard
- **Blynk.Console** (Desktop)  
- **Blynk.App** (Mobile)  

---

## 📂 Project Structure
```text
.
├── main.py # Entry point
├── combined_server.py # Flask server (stream + images)
├── camera_module.py # PiCamera abstraction
├── captured_photos.py # Photo capture & storage logic
├── static/
│   └── photos/ # Captured images
├── requirements.txt
└── README.md
```
---

## 🚀 Getting Started

### 1 Clone the Repository
```bash
git clone https://github.com/Lance0567/ust-flood-control.git
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

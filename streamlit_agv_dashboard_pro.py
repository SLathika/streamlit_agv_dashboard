from flask import Flask, jsonify, render_template_string
import threading
import time
import random
import math
from datetime import datetime

app = Flask(__name__)

# ----------------------------------------------------------
#   ENHANCED AGV DATA SIMULATION
# ----------------------------------------------------------
agv_data = {
    "AGV1": {"x": 0, "y": 0, "status": "idle", "battery": 100, "speed": 0, "task": "No Task"},
    "AGV2": {"x": 0, "y": 0, "status": "idle", "battery": 100, "speed": 0, "task": "No Task"},
    "AGV3": {"x": 0, "y": 0, "status": "idle", "battery": 100, "speed": 0, "task": "No Task"},
    "AGV4": {"x": 0, "y": 0, "status": "idle", "battery": 100, "speed": 0, "task": "No Task"}
}

statuses = ["moving", "waiting", "avoiding", "idle", "charging", "loading"]
tasks = ["Picking Order #123", "Moving to Zone A", "Returning to Base", 
         "Inventory Scan", "Charging", "Package Delivery"]

last_positions = {agv: (0, 0) for agv in agv_data.keys()}
alert_message = "System Stable ✓ All AGVs operating normally."
system_uptime = datetime.now()

# ----------------------------------------------------------
#   ENHANCED BACKGROUND AGV SIMULATION
# ----------------------------------------------------------
def update_fake_data():
    global alert_message
    
    # Initialize with different starting positions
    base_positions = {
        "AGV1": (2, 2),
        "AGV2": (-2, 2),
        "AGV3": (2, -2),
        "AGV4": (-2, -2)
    }
    
    for agv, pos in base_positions.items():
        agv_data[agv]["x"] = pos[0]
        agv_data[agv]["y"] = pos[1]
        last_positions[agv] = pos

    while True:
        alerts = []
        
        for agv in agv_data:
            prev_x, prev_y = last_positions[agv]
            
            # Simulate more realistic movement with inertia
            move_x = random.uniform(-1.5, 1.5) * 0.7 + (agv_data[agv]["x"] - prev_x) * 0.3
            move_y = random.uniform(-1.5, 1.5) * 0.7 + (agv_data[agv]["y"] - prev_y) * 0.3
            
            new_x = round(agv_data[agv]["x"] + move_x, 2)
            new_y = round(agv_data[agv]["y"] + move_y, 2)
            
            # Keep within bounds
            new_x = max(-8, min(8, new_x))
            new_y = max(-8, min(8, new_y))
            
            agv_data[agv]["x"] = new_x
            agv_data[agv]["y"] = new_y
            
            # Calculate speed based on distance moved
            dist = math.hypot(new_x - prev_x, new_y - prev_y)
            agv_data[agv]["speed"] = round(dist * 2.0, 2)
            last_positions[agv] = (new_x, new_y)
            
            # Status updates with state persistence
            if random.random() < 0.1:  # 10% chance to change status
                agv_data[agv]["status"] = random.choice(statuses)
                if agv_data[agv]["status"] in ["moving", "loading"]:
                    agv_data[agv]["task"] = random.choice(tasks)
            
            # Battery simulation with different drain rates
            if agv_data[agv]["status"] == "moving":
                drain = random.uniform(0.3, 1.0)
            elif agv_data[agv]["status"] == "charging":
                drain = -random.uniform(1.0, 2.0)  # Charging
            else:
                drain = random.uniform(0.1, 0.3)
            
            agv_data[agv]["battery"] = max(0, min(100, agv_data[agv]["battery"] - drain))
            
            # Generate alerts
            if agv_data[agv]["status"] == "avoiding":
                alerts.append(f"⚠️ {agv}: Collision avoidance active")
            if agv_data[agv]["battery"] < 15:
                alerts.append(f"🔋 {agv}: Low battery ({agv_data[agv]['battery']:.1f}%)")
            if agv_data[agv]["battery"] < 5:
                alerts.append(f"🚨 {agv}: CRITICAL battery level!")
            if agv_data[agv]["speed"] > 3.5:
                alerts.append(f"⚡ {agv}: High speed ({agv_data[agv]['speed']} m/s)")
        
        # Update global alert message
        if alerts:
            alert_message = " | ".join(alerts[:3])  # Show up to 3 alerts
        else:
            uptime = datetime.now() - system_uptime
            hours = uptime.seconds // 3600
            minutes = (uptime.seconds % 3600) // 60
            alert_message = f"✓ System Normal | Uptime: {hours}h {minutes}m"
        
        time.sleep(1.0)  # Update every second

# ----------------------------------------------------------
#   DASHBOARD ROUTE (Single decorator)
# ----------------------------------------------------------
@app.route("/")
def dashboard():
    """Main dashboard page"""
    return render_template_string("""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>AGV Traffic Dashboard</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<style>
    :root {
        --primary: #0a1f44;
        --secondary: #0d47a1;
        --accent: #4fc3f7;
        --success: #00e676;
        --warning: #ffeb3b;
        --danger: #ff5252;
        --idle: #b0bec5;
        --card-bg: #0e2b57;
        --panel-bg: #062042;
    }
    
    body {
        margin: 0;
        padding: 0;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        background: var(--primary);
        color: white;
        overflow-x: hidden;
    }
    
    .header {
        text-align: center;
        padding: 20px;
        background: linear-gradient(135deg, var(--secondary), #1565c0);
        font-size: 2rem;
        font-weight: 700;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
        position: relative;
    }
    
    .header::after {
        content: '';
        position: absolute;
        bottom: 0;
        left: 0;
        right: 0;
        height: 3px;
        background: linear-gradient(90deg, transparent, var(--accent), transparent);
    }
    
    .alert-box {
        width: 90%;
        max-width: 1200px;
        margin: 20px auto;
        padding: 15px 20px;
        background: #153d7e;
        border-left: 6px solid var(--accent);
        border-radius: 8px;
        font-size: 1.1rem;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        gap: 10px;
    }
    
    .alert-box.warning { border-left-color: var(--warning); }
    .alert-box.danger { border-left-color: var(--danger); }
    
    .stats-bar {
        display: flex;
        justify-content: center;
        gap: 20px;
        margin: 20px auto;
        width: 90%;
        max-width: 1200px;
        flex-wrap: wrap;
    }
    
    .stat-card {
        background: var(--card-bg);
        padding: 15px 25px;
        border-radius: 10px;
        text-align: center;
        min-width: 150px;
        box-shadow: 0 5px 15px rgba(0, 0, 0, 0.2);
    }
    
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
        color: var(--accent);
    }
    
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.8;
    }
    
    #agvContainer {
        display: flex;
        justify-content: center;
        gap: 25px;
        flex-wrap: wrap;
        margin: 30px auto;
        width: 95%;
        max-width: 1400px;
    }
    
    .agv-card {
        background: var(--card-bg);
        width: 280px;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.3);
        transition: all 0.3s ease;
        border-top: 4px solid var(--accent);
    }
    
    .agv-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 15px 30px rgba(0, 0, 0, 0.4);
    }
    
    .agv-title {
        font-size: 1.5rem;
        font-weight: 700;
        color: var(--accent);
        margin-bottom: 15px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    
    .agv-status {
        padding: 4px 12px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    
    .agv-data {
        margin: 10px 0;
        display: flex;
        justify-content: space-between;
    }
    
    .battery-container {
        margin-top: 15px;
    }
    
    .battery-bar {
        height: 20px;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
        overflow: hidden;
        margin-top: 5px;
    }
    
    .battery-fill {
        height: 100%;
        border-radius: 10px;
        transition: width 0.5s ease;
    }
    
    .warehouse-title {
        text-align: center;
        color: var(--accent);
        margin: 40px 0 20px;
        font-size: 1.8rem;
    }
    
    #warehousePanel {
        width: 95%;
        max-width: 1200px;
        margin: 0 auto 50px;
        background: var(--panel-bg);
        padding: 20px;
        border-radius: 12px;
        border: 3px solid var(--accent);
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.4);
    }
    
    #warehouseSVG {
        width: 100%;
        height: 500px;
        background: #0f355f;
        border-radius: 8px;
    }
    
    .shelf {
        fill: #1e88e5;
        stroke: #06336b;
        stroke-width: 2;
        rx: 5;
    }
    
    .charging-station {
        fill: #ff9800;
        stroke: #e65100;
        stroke-width: 2;
    }
    
    .agv-robot {
        transition: transform 0.5s ease;
    }
    
    .robot-body {
        stroke: white;
        stroke-width: 2;
    }
    
    .footer {
        text-align: center;
        padding: 20px;
        background: rgba(0, 0, 0, 0.3);
        margin-top: 40px;
        font-size: 0.9rem;
        color: rgba(255, 255, 255, 0.7);
    }
    
    @media (max-width: 768px) {
        .header { font-size: 1.5rem; }
        .agv-card { width: 100%; max-width: 400px; }
        .stats-bar { gap: 10px; }
        .stat-card { min-width: 120px; padding: 12px 15px; }
    }
</style>
</head>

<body>
    <div class="header">
        <i class="fas fa-robot"></i> AI-Driven Multi-AGV Traffic Dashboard
    </div>
    
    <div id="alertBox" class="alert-box">
        <i class="fas fa-info-circle"></i> <span id="alertText">Loading system...</span>
    </div>
    
    <div class="stats-bar">
        <div class="stat-card">
            <div class="stat-value" id="totalAgvs">4</div>
            <div class="stat-label">Total AGVs</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="movingAgvs">0</div>
            <div class="stat-label">Active AGVs</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="avgBattery">0%</div>
            <div class="stat-label">Avg Battery</div>
        </div>
        <div class="stat-card">
            <div class="stat-value" id="totalAlerts">0</div>
            <div class="stat-label">Active Alerts</div>
        </div>
    </div>
    
    <div id="agvContainer">
        <!-- AGV cards will be populated by JavaScript -->
    </div>
    
    <h2 class="warehouse-title">
        <i class="fas fa-warehouse"></i> Warehouse Visualization
    </h2>
    
    <div id="warehousePanel">
        <svg id="warehouseSVG" viewBox="0 0 1000 600">
            <!-- Warehouse floor -->
            <rect width="100%" height="100%" fill="#0f355f"/>
            
            <!-- Grid pattern -->
            <defs>
                <pattern id="grid" x="0" y="0" width="50" height="50" patternUnits="userSpaceOnUse">
                    <path d="M 50 0 L 0 0 0 50" fill="none" stroke="#1a4a7a" stroke-width="1"/>
                </pattern>
            </defs>
            <rect width="100%" height="100%" fill="url(#grid)" opacity="0.3"/>
            
            <!-- Shelving units -->
            <rect class="shelf" x="100" y="100" width="800" height="40"/>
            <rect class="shelf" x="100" y="250" width="800" height="40"/>
            <rect class="shelf" x="100" y="400" width="800" height="40"/>
            
            <!-- Charging stations -->
            <rect class="charging-station" x="50" y="500" width="60" height="30" rx="5"/>
            <rect class="charging-station" x="890" y="500" width="60" height="30" rx="5"/>
            <text x="80" y="520" fill="white" text-anchor="middle" font-size="12">Charging</text>
            <text x="920" y="520" fill="white" text-anchor="middle" font-size="12">Charging</text>
            
            <!-- AGV robots will be placed here -->
            <g id="agvMarkers"></g>
            
            <!-- Legend -->
            <g transform="translate(800, 30)">
                <rect width="180" height="120" fill="rgba(13, 71, 161, 0.8)" rx="5"/>
                <text x="90" y="30" fill="white" text-anchor="middle" font-weight="bold">AGV Status</text>
                
                <circle cx="30" cy="55" r="8" fill="#00e676"/>
                <text x="50" y="60" fill="white" font-size="14">Moving</text>
                
                <circle cx="30" cy="80" r="8" fill="#ffeb3b"/>
                <text x="50" y="85" fill="white" font-size="14">Waiting</text>
                
                <circle cx="30" cy="105" r="8" fill="#ff5252"/>
                <text x="50" y="110" fill="white" font-size="14">Avoiding</text>
            </g>
        </svg>
    </div>
    
    <div class="footer">
        <p>AGV Traffic Monitoring System | Real-time Simulation | Last Update: <span id="lastUpdate">--:--:--</span></p>
        <p>Use Ctrl+R to refresh | Data updates every second</p>
    </div>

<script>
function agvColor(status) {
    const colors = {
        "moving": "#00e676",
        "waiting": "#ffeb3b",
        "avoiding": "#ff5252",
        "idle": "#b0bec5",
        "charging": "#ff9800",
        "loading": "#9c27b0"
    };
    return colors[status] || "#b0bec5";
}

function getStatusIcon(status) {
    const icons = {
        "moving": "fas fa-running",
        "waiting": "fas fa-pause",
        "avoiding": "fas fa-exclamation-triangle",
        "idle": "fas fa-power-off",
        "charging": "fas fa-bolt",
        "loading": "fas fa-box"
    };
    return icons[status] || "fas fa-robot";
}

function getBatteryColor(percent) {
    if (percent >= 60) return "#00e676";
    if (percent >= 30) return "#ffeb3b";
    return "#ff5252";
}

async function loadData() {
    try {
        const [dataRes, alertRes] = await Promise.all([
            fetch('/data'),
            fetch('/alert')
        ]);
        
        const data = await dataRes.json();
        const alertText = await alertRes.text();
        
        // Update alert box
        const alertBox = document.getElementById('alertBox');
        const alertSpan = document.getElementById('alertText');
        alertSpan.textContent = alertText;
        
        // Update alert box styling based on content
        if (alertText.includes('CRITICAL') || alertText.includes('⚠️')) {
            alertBox.className = 'alert-box danger';
        } else if (alertText.includes('Warning') || alertText.includes('Low')) {
            alertBox.className = 'alert-box warning';
        } else {
            alertBox.className = 'alert-box';
        }
        
        // Calculate stats
        let movingCount = 0;
        let totalBattery = 0;
        let alertCount = 0;
        
        // Generate AGV cards
        let html = "";
        for (let agv in data) {
            const d = data[agv];
            
            // Update stats
            if (d.status === "moving") movingCount++;
            totalBattery += d.battery;
            if (d.battery < 20 || d.status === "avoiding") alertCount++;
            
            html += `
                <div class="agv-card">
                    <div class="agv-title">
                        <span><i class="fas fa-robot"></i> ${agv}</span>
                        <span class="agv-status" style="background: ${agvColor(d.status)}20; color: ${agvColor(d.status)};">
                            <i class="${getStatusIcon(d.status)}"></i> ${d.status.toUpperCase()}
                        </span>
                    </div>
                    
                    <div class="agv-data">
                        <span><i class="fas fa-map-marker-alt"></i> Position:</span>
                        <span>x: ${d.x.toFixed(2)}, y: ${d.y.toFixed(2)}</span>
                    </div>
                    
                    <div class="agv-data">
                        <span><i class="fas fa-tachometer-alt"></i> Speed:</span>
                        <span>${d.speed.toFixed(2)} m/s</span>
                    </div>
                    
                    <div class="agv-data">
                        <span><i class="fas fa-tasks"></i> Task:</span>
                        <span>${d.task || 'No Task'}</span>
                    </div>
                    
                    <div class="battery-container">
                        <div class="agv-data">
                            <span><i class="fas fa-battery-full"></i> Battery:</span>
                            <span>${d.battery.toFixed(1)}%</span>
                        </div>
                        <div class="battery-bar">
                            <div class="battery-fill" 
                                 style="width: ${d.battery}%; background: ${getBatteryColor(d.battery)};">
                            </div>
                        </div>
                    </div>
                </div>`;
        }
        
        document.getElementById("agvContainer").innerHTML = html;
        
        // Update stats
        document.getElementById("movingAgvs").textContent = movingCount;
        document.getElementById("avgBattery").textContent = `${(totalBattery / 4).toFixed(1)}%`;
        document.getElementById("totalAlerts").textContent = alertCount;
        
        // Update warehouse visualization
        updateWarehouse(data);
        
        // Update last update time
        const now = new Date();
        document.getElementById("lastUpdate").textContent = 
            `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`;
            
    } catch (error) {
        console.error('Error loading data:', error);
        document.getElementById("alertText").textContent = "Error connecting to server. Retrying...";
    }
}

function updateWarehouse(data) {
    const svgNS = "http://www.w3.org/2000/svg";
    const container = document.getElementById("agvMarkers");
    
    // Clear existing markers
    while (container.firstChild) {
        container.removeChild(container.firstChild);
    }
    
    // Define warehouse bounds for mapping
    const warehouseWidth = 800;
    const warehouseHeight = 400;
    const offsetX = 100;
    const offsetY = 100;
    
    // Create AGV markers
    Object.entries(data).forEach(([agvName, agv], index) => {
        // Map simulated coordinates to SVG coordinates
        const x = offsetX + ((agv.x + 10) / 20) * warehouseWidth;
        const y = offsetY + ((10 - agv.y) / 20) * warehouseHeight;
        
        // Create AGV group
        const agvGroup = document.createElementNS(svgNS, "g");
        agvGroup.setAttribute("class", "agv-robot");
        agvGroup.setAttribute("id", `agv-${index}`);
        
        // Create robot body (circle)
        const body = document.createElementNS(svgNS, "circle");
        body.setAttribute("cx", x);
        body.setAttribute("cy", y);
        body.setAttribute("r", 15);
        body.setAttribute("fill", agvColor(agv.status));
        body.setAttribute("stroke", "white");
        body.setAttribute("stroke-width", "2");
        body.setAttribute("class", "robot-body");
        
        // Create robot direction indicator
        const direction = document.createElementNS(svgNS, "path");
        direction.setAttribute("d", `M ${x} ${y-12} L ${x} ${y-20}`);
        direction.setAttribute("stroke", "white");
        direction.setAttribute("stroke-width", "2");
        direction.setAttribute("fill", "none");
        
        // Create AGV label
        const label = document.createElementNS(svgNS, "text");
        label.setAttribute("x", x);
        label.setAttribute("y", y + 30);
        label.setAttribute("text-anchor", "middle");
        label.setAttribute("fill", "white");
        label.setAttribute("font-size", "12");
        label.setAttribute("font-weight", "bold");
        label.textContent = agvName;
        
        // Add battery indicator
        const battery = document.createElementNS(svgNS, "rect");
        battery.setAttribute("x", x - 12);
        battery.setAttribute("y", y + 15);
        battery.setAttribute("width", 24);
        battery.setAttribute("height", 4);
        battery.setAttribute("fill", "#555");
        battery.setAttribute("rx", "2");
        
        const batteryFill = document.createElementNS(svgNS, "rect");
        batteryFill.setAttribute("x", x - 12);
        batteryFill.setAttribute("y", y + 15);
        batteryFill.setAttribute("width", (24 * agv.battery / 100));
        batteryFill.setAttribute("height", 4);
        batteryFill.setAttribute("fill", getBatteryColor(agv.battery));
        batteryFill.setAttribute("rx", "2");
        
        // Add elements to group
        agvGroup.appendChild(body);
        agvGroup.appendChild(direction);
        agvGroup.appendChild(battery);
        agvGroup.appendChild(batteryFill);
        agvGroup.appendChild(label);
        
        // Add hover effect
        agvGroup.addEventListener('mouseenter', () => {
            body.setAttribute("r", 18);
            label.setAttribute("font-size", "14");
        });
        
        agvGroup.addEventListener('mouseleave', () => {
            body.setAttribute("r", 15);
            label.setAttribute("font-size", "12");
        });
        
        container.appendChild(agvGroup);
    });
}

// Initial load
loadData();

// Auto-refresh every second
setInterval(loadData, 1000);

// Keyboard shortcuts
document.addEventListener('keydown', (e) => {
    if (e.ctrlKey && e.key === 'r') {
        e.preventDefault();
        loadData();
    }
});
</script>
</body>
</html>
""")

# ----------------------------------------------------------
#   API ROUTES
# ----------------------------------------------------------
@app.route("/data")
def get_data():
    """Return current AGV data"""
    return jsonify(agv_data)

@app.route("/alert")
def get_alert():
    """Return current alert message"""
    return alert_message

@app.route("/status")
def get_status():
    """Return system status summary"""
    moving = sum(1 for agv in agv_data.values() if agv["status"] == "moving")
    charging = sum(1 for agv in agv_data.values() if agv["status"] == "charging")
    avg_battery = sum(agv["battery"] for agv in agv_data.values()) / len(agv_data)
    
    return jsonify({
        "total_agvs": len(agv_data),
        "active_agvs": moving,
        "charging_agvs": charging,
        "average_battery": round(avg_battery, 1),
        "system_status": "operational" if "CRITICAL" not in alert_message else "warning",
        "timestamp": datetime.now().isoformat()
    })

# ----------------------------------------------------------
#   START BACKGROUND THREAD + FLASK
# ----------------------------------------------------------
if __name__ == "__main__":
    # Start simulation thread
    sim_thread = threading.Thread(target=update_fake_data, daemon=True)
    sim_thread.start()
    
    # Run Flask app
    print("=" * 60)
    print("AGV Traffic Dashboard")
    print("=" * 60)
    print(f"Dashboard URL: http://127.0.0.1:5000")
    print(f"Data API: http://127.0.0.1:5000/data")
    print(f"Alert API: http://127.0.0.1:5000/alert")
    print(f"Status API: http://127.0.0.1:5000/status")
    print("=" * 60)
    print("Press Ctrl+C to stop")
    
    app.run(host='0.0.0.0', port=5000, debug=False)
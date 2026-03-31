let map, markersLayer, nodesLayer;
let currentLimit = 20;
let currentNodeFilter = "all";
let streetLayer, satelliteLayer;
let lastOfflineAlertSignature = "";
let lastAlertSignature = "";

const API_BASE = "http://127.0.0.1:8000/api";

function initMap() {
  map = L.map("map").setView([24.597, 53.306], 8);

  streetLayer = L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    attribution: "&copy; OpenStreetMap contributors"
  });

  satelliteLayer = L.tileLayer(
    "https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}",
    {
      attribution: "&copy; Google"
    }
  );

  streetLayer.addTo(map);

  markersLayer = L.layerGroup().addTo(map);
  nodesLayer = L.layerGroup().addTo(map);
}

function setStreetView() {
  if (map.hasLayer(satelliteLayer)) map.removeLayer(satelliteLayer);
  if (!map.hasLayer(streetLayer)) streetLayer.addTo(map);
}

function setSatelliteView() {
  if (map.hasLayer(streetLayer)) map.removeLayer(streetLayer);
  if (!map.hasLayer(satelliteLayer)) satelliteLayer.addTo(map);
}

function resetMapView() {
  map.setView([24.597, 53.306], 8);
}

async function focusLatestAlert() {
  try {
    const res = await fetch(`${API_BASE}/events?limit=${currentLimit}`);
    const data = await res.json();

    const latestAlert = data.find(e => e.status === "alert" && e.lat != null && e.lon != null);

    if (latestAlert) {
      map.setView([latestAlert.lat, latestAlert.lon], 14);
    }
  } catch (e) {
    console.error("Focus alert error:", e);
  }
}

function shahedLabel() {
  return `Shahed<br>detected`;
}

function formatTimeGST(timestamp) {
  if (!timestamp) return "N/A";

  try {
    const date = new Date(timestamp);
    return date.toLocaleString("en-GB", {
      timeZone: "Asia/Dubai",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit"
    }).replace(",", "");
  } catch {
    return timestamp.replace("T", " ").split(".")[0];
  }
}

function getNodeColor(state) {
  if (state === "alert") return "red";
  if (state === "resolved") return "green";
  if (state === "online") return "green";
  if (state === "warning") return "yellow";
  if (state === "offline") return "yellow";
  return "green";
}

function getNodeLabel(state) {
  if (state === "alert") return "ALERT";
  if (state === "resolved") return "ONLINE";
  if (state === "online") return "ONLINE";
  if (state === "warning") return "OFFLINE";
  if (state === "offline") return "OFFLINE";
  return "ONLINE";
}

function createDivIconForState(state) {
  if (state === "alert") {
    return L.divIcon({
      className: "",
      html: `<div class="pulse-marker"></div>`,
      iconSize: [22, 22],
      iconAnchor: [11, 11]
    });
  }

  if (state === "resolved") {
    return L.divIcon({
      className: "",
      html: `<div class="node-dot-green"></div>`,
      iconSize: [18, 18],
      iconAnchor: [9, 9]
    });
  }

  if (state === "warning" || state === "online") {
    return L.divIcon({
      className: "",
      html: `<div class="node-dot-yellow"></div>`,
      iconSize: [18, 18],
      iconAnchor: [9, 9]
    });
  }

  return L.divIcon({
    className: "",
    html: `<div class="node-dot-gray"></div>`,
    iconSize: [18, 18],
    iconAnchor: [9, 9]
  });
}

function playAlarmRepeated(times = 4) {
  const audio = document.getElementById("alarm-sound");
  if (!audio) return;

  let playCount = 0;

  const playNext = () => {
    if (playCount >= times) {
      audio.onended = null;
      return;
    }

    playCount += 1;
    audio.currentTime = 0;
    audio.play().catch(err => {
      console.warn("Audio play blocked:", err);
    });
  };

  audio.onended = playNext;
  playNext();
}

async function loadEvents() {
  try {
    const [eventsRes, nodesRes] = await Promise.all([
      fetch(`${API_BASE}/events?limit=${currentLimit}`),
      fetch(`${API_BASE}/nodes?status=${currentNodeFilter}`)
    ]);

    const events = await eventsRes.json();
    const nodes = await nodesRes.json();

    renderTable(events);
    renderAlertMarkers(events);
    renderNodes(nodes);
    renderNodeInventory(nodes);
    checkOfflineNodes(nodes);
    checkNewActiveAlerts(events);
  } catch (e) {
    console.error("Error loading dashboard data:", e);
  }
}

function checkNewActiveAlerts(events) {
  const activeAlerts = events.filter(e => e.status === "alert");
  const signature = activeAlerts.map(e => e.id).sort((a, b) => a - b).join("|");

  if (signature && signature !== lastAlertSignature) {
    lastAlertSignature = signature;
    playAlarmRepeated(4);
  }

  if (!signature) {
    lastAlertSignature = "";
  }
}

function renderTable(data) {
  const tbody = document.getElementById("events-body");

  if (!data || data.length === 0) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center; padding:20px; color:#94a3b8;">No alerts detected by nodes.</td></tr>`;
    document.getElementById("total-events").innerText = 0;
    document.getElementById("active-alerts").innerText = 0;
    document.getElementById("resolved-events").innerText = 0;
    return;
  }

  tbody.innerHTML = data.map(event => {
    const lat = typeof event.lat === "number" ? event.lat.toFixed(4) : "No GPS";
    const lon = typeof event.lon === "number" ? event.lon.toFixed(4) : "";

    const statusBadge = event.status === "resolved"
      ? `<span class="badge-resolved">resolved</span>`
      : `<span class="badge-alert">alert</span>`;

    const classLabel = event.event_class === "motor_objetivo"
      ? shahedLabel()
      : event.event_class;

    return `
      <tr>
        <td>${event.id}</td>
        <td><strong>${event.node_id}</strong></td>
        <td>${formatTimeGST(event.timestamp)}</td>
        <td>${lat}${lon ? `, ${lon}` : ""}</td>
        <td>${classLabel}</td>
        <td>${event.confidence ? (event.confidence * 100).toFixed(0) + "%" : "0%"}</td>
        <td>${statusBadge}</td>
        <td>${event.status === "alert" ? `<button class="resolve-btn" onclick="resolveEvent(${event.id})">Resolve</button>` : "OK"}</td>
      </tr>
    `;
  }).join("");

  document.getElementById("total-events").innerText = data.length;
  document.getElementById("active-alerts").innerText = data.filter(e => e.status === "alert").length;
  document.getElementById("resolved-events").innerText = data.filter(e => e.status === "resolved").length;
}

function renderAlertMarkers(events) {
  markersLayer.clearLayers();

  const alerts = events.filter(e => e.status === "alert" && e.lat != null && e.lon != null);

  alerts.forEach(e => {
    L.circleMarker([e.lat, e.lon], {
      radius: 12,
      color: "red",
      weight: 3,
      fillColor: "red",
      fillOpacity: 0.25
    })
      .addTo(markersLayer)
      .bindPopup(`
        <b>CRITICAL ALERT</b><br>
        Node: ${e.node_id}<br>
        Coordinates: ${e.lat?.toFixed(6)}, ${e.lon?.toFixed(6)}<br>
        Class: Shahed detected<br>
        Confidence: ${e.confidence ? (e.confidence * 100).toFixed(0) + "%" : "0%"}<br>
        Status: ${e.status}<br>
        Time: ${formatTimeGST(e.timestamp)}
      `);
  });
}

function renderNodes(nodes) {
  nodesLayer.clearLayers();

  nodes.forEach(node => {
  if (node.lat == null || node.lon == null) return;
  if (node.state === "offline") return;



    const marker = L.marker([node.lat, node.lon], {
      icon: createDivIconForState(node.state)
    });

    marker.bindPopup(`
      <b>Node:</b> ${node.node_id}<br>
      <b>Status:</b> ${getNodeLabel(node.state)}<br>
      <b>Coordinates:</b> ${node.lat?.toFixed(6)}, ${node.lon?.toFixed(6)}<br>
      <b>Last seen:</b> ${formatTimeGST(node.last_seen)}<br>
      <b>Latest class:</b> ${node.latest_event_class === "motor_objetivo" ? "Shahed detected" : (node.latest_event_class || "N/A")}<br>
      <b>Confidence:</b> ${node.latest_confidence ? (node.latest_confidence * 100).toFixed(0) + "%" : "N/A"}<br>
      <b>Active alerts:</b> ${node.active_alert_count}
    `);

    marker.addTo(nodesLayer);
  });
}

function renderNodeInventory(nodes) {
  const container = document.getElementById("nodes-list-content");

  if (!nodes || nodes.length === 0) {
    container.innerHTML = `<p style="color: #94a3b8; font-size: 12px; text-align: center;">No nodes found.</p>`;
    return;
  }

  const filterBar = `
    <div style="display:flex; gap:8px; margin-bottom:10px; flex-wrap:wrap;">
      <button class="map-btn" onclick="setNodeFilter('all')">All</button>
      <button class="map-btn" onclick="setNodeFilter('online')">Online</button>
      <button class="map-btn" onclick="setNodeFilter('warning')">Warning</button>
      <button class="map-btn" onclick="setNodeFilter('offline')">Offline</button>
      <button class="map-btn" onclick="setNodeFilter('resolved')">Resolved</button>
      <button class="map-btn" onclick="setNodeFilter('alert')">Alert</button>
    </div>
  `;

  const items = nodes.map(node => {
    const cls =
      node.state === "alert" ? "node-offline" :
      node.state === "resolved" ? "node-online" :
      node.state === "warning" ? "node-warning" :
      node.state === "online" ? "node-online" :
      "node-offline";

    const coords = (node.lat != null && node.lon != null)
      ? `${node.lat.toFixed(4)}, ${node.lon.toFixed(4)}`
      : "No GPS";

    return `
      <div class="node-item" onclick="focusNode(${node.lat ?? "null"}, ${node.lon ?? "null"})" style="cursor:pointer;">
        <div>
          <div><strong>${node.node_id}</strong></div>
          <div style="font-size:11px; color:#94a3b8;">${coords}</div>
          <div style="font-size:11px; color:#94a3b8;">Last seen: ${formatTimeGST(node.last_seen)}</div>
        </div>
        <div class="${cls}" style="font-weight:bold;">${getNodeLabel(node.state)}</div>
      </div>
    `;
  }).join("");

  container.innerHTML = filterBar + items;
}

function focusNode(lat, lon) {
  if (lat == null || lon == null) return;
  map.setView([lat, lon], 14);
}

function setNodeFilter(filter) {
  currentNodeFilter = filter;
  loadEvents();
}

function checkOfflineNodes(nodes) {
  const offline = nodes.filter(n => n.state === "offline");
  const signature = offline.map(n => n.node_id).sort().join("|");

  if (offline.length > 0 && signature !== lastOfflineAlertSignature) {
    lastOfflineAlertSignature = signature;
    alert(`Node disconnected: ${offline.map(n => n.node_id).join(", ")}`);
  }

  if (offline.length === 0) {
    lastOfflineAlertSignature = "";
  }
}

function toggleInventory() {
  document.getElementById("inventory-panel").classList.toggle("inventory-hidden");
}

function changeLimit(val) {
  currentLimit = parseInt(val, 10);
  loadEvents();
}

async function resolveEvent(id) {
  try {
    const res = await fetch(`${API_BASE}/events/${id}/resolve`, {
      method: "PUT"
    });

    const data = await res.json();
    console.log("Resolve response:", data);
    await loadEvents();
  } catch (e) {
    console.error("Resolve error:", e);
  }
}

async function filterByDate() {
  const date = document.getElementById("dateFilter").value;
  if (!date) {
    loadEvents();
    return;
  }

  try {
    const res = await fetch(`${API_BASE}/events/by-date?date=${date}`);
    const data = await res.json();
    renderTable(data);
    renderAlertMarkers(data);
  } catch (e) {
    console.error("Date filter error:", e);
  }
}

function clearDateFilter() {
  document.getElementById("dateFilter").value = "";
  loadEvents();
}

try {
  initMap();
  loadEvents();
  setInterval(loadEvents, 5000);
} catch (error) {
  console.error("Critical System Error:", error);
}
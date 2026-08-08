const userInput = document.getElementById("user-id");
const radiusInput = document.getElementById("radius");
const saveUserButton = document.getElementById("save-user");
const reloadZonesButton = document.getElementById("reload-zones");
const alertsList = document.getElementById("alerts");

const userStorageKey = "geotracking_user_id";
const markers = new Map();
let map;
let ws;
let geozoneLayers = [];
let initialViewportApplied = false;
const odessaCoordinates = [46.4825, 30.7233];

function getUserId() {
  return userInput.value.trim();
}

function headers() {
  return {
    "Content-Type": "application/json",
    "X-User-Id": getUserId(),
  };
}

function showAlert(text) {
  const item = document.createElement("li");
  item.textContent = text;
  alertsList.prepend(item);
  while (alertsList.children.length > 30) {
    alertsList.removeChild(alertsList.lastChild);
  }
}

function initializeMap() {
  map = L.map("map").setView(odessaCoordinates, 11);
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors",
  }).addTo(map);

  map.on("click", async (event) => {
    const userId = getUserId();
    if (!userId) {
      showAlert("Set User ID before creating geozones.");
      return;
    }
    const payload = {
      name: `Zone ${new Date().toISOString()}`,
      latitude: event.latlng.lat,
      longitude: event.latlng.lng,
      radius_meters: Number(radiusInput.value || 500),
    };
    await fetch("/api/v1/geozones", {
      method: "POST",
      headers: headers(),
      body: JSON.stringify(payload),
    });
    await loadGeozones();
  });
}

async function loadGeozones(shouldSetInitialView = false) {
  geozoneLayers.forEach((layer) => layer.remove());
  geozoneLayers = [];

  if (!getUserId()) {
    return;
  }

  const response = await fetch("/api/v1/geozones", {
    method: "GET",
    headers: headers(),
  });
  if (!response.ok) {
    showAlert("Failed to load geozones.");
    return;
  }
  const zones = await response.json();
  if (shouldSetInitialView && zones.length > 0 && !initialViewportApplied) {
    const firstZone = zones[0];
    map.setView([firstZone.latitude, firstZone.longitude], 12);
    initialViewportApplied = true;
  }
  zones.forEach((zone) => {
    const circle = L.circle([zone.latitude, zone.longitude], {
      radius: zone.radius_meters,
      color: "#4f7cff",
      fillOpacity: 0.15,
    }).addTo(map);
    circle.bindPopup("Loading geozone details...");
    circle.on("click", async () => {
      await openGeozonePopup(zone.id, circle);
    });
    geozoneLayers.push(circle);
  });
}

async function fetchGeozoneById(geozoneId) {
  const response = await fetch(`/api/v1/geozones/${geozoneId}`, {
    method: "GET",
    headers: headers(),
  });
  if (!response.ok) {
    throw new Error("Failed to fetch geozone details.");
  }
  return response.json();
}

async function deleteGeozoneById(geozoneId) {
  const response = await fetch(`/api/v1/geozones/${geozoneId}`, {
    method: "DELETE",
    headers: headers(),
  });
  if (!response.ok) {
    throw new Error("Failed to delete geozone.");
  }
}

function createGeozonePopupElement(geozone, circle) {
  const wrapper = document.createElement("div");
  const title = document.createElement("strong");
  title.textContent = geozone.name;
  wrapper.appendChild(title);

  const details = document.createElement("div");
  details.textContent = `${Math.round(geozone.radius_meters)}m`;
  wrapper.appendChild(details);

  const removeButton = document.createElement("button");
  removeButton.type = "button";
  removeButton.className = "danger-button";
  removeButton.textContent = "Delete geozone";
  removeButton.addEventListener("click", async (event) => {
    event.preventDefault();
    event.stopPropagation();
    try {
      await deleteGeozoneById(geozone.id);
      circle.closePopup();
      showAlert(`Deleted geozone: ${geozone.name}`);
      await loadGeozones();
    } catch (_) {
      showAlert("Failed to delete geozone.");
    }
  });
  wrapper.appendChild(removeButton);
  return wrapper;
}

async function openGeozonePopup(geozoneId, circle) {
  try {
    const geozone = await fetchGeozoneById(geozoneId);
    const popupElement = createGeozonePopupElement(geozone, circle);
    circle.setPopupContent(popupElement);
    circle.openPopup();
  } catch (_) {
    circle.setPopupContent("Failed to load geozone details.");
    circle.openPopup();
  }
}

function upsertDeviceMarker(event) {
  const key = event.device_id;
  const latLng = [event.latitude, event.longitude];
  const marker = markers.get(key);
  if (marker) {
    marker.setLatLng(latLng);
    return;
  }
  const created = L.marker(latLng).addTo(map);
  created.bindPopup(`Device: ${event.device_id}`);
  markers.set(key, created);
}

function connectSocket() {
  if (!getUserId()) {
    return;
  }
  if (ws) {
    ws.close();
  }

  const protocol = window.location.protocol === "https:" ? "wss" : "ws";
  ws = new WebSocket(`${protocol}://${window.location.host}/ws?user_id=${encodeURIComponent(getUserId())}`);
  ws.onmessage = (message) => {
    try {
      const event = JSON.parse(message.data);
      if (event.type === "location") {
        upsertDeviceMarker(event);
      } else if (event.type === "alert") {
        showAlert(`${event.device_id} entered ${event.geozone_name}`);
      }
    } catch (_) {
      showAlert("Received invalid event payload.");
    }
  };
}

function saveUser() {
  const userId = getUserId();
  localStorage.setItem(userStorageKey, userId);
  initialViewportApplied = false;
  connectSocket();
  loadGeozones(true);
}

function restoreUser() {
  const saved = localStorage.getItem(userStorageKey);
  if (saved) {
    userInput.value = saved;
  }
}

saveUserButton.addEventListener("click", saveUser);
reloadZonesButton.addEventListener("click", () => loadGeozones());

restoreUser();
initializeMap();
if (getUserId()) {
  connectSocket();
  loadGeozones(true);
}

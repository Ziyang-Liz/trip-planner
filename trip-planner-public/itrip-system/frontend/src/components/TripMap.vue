<script setup lang="ts">
import { onMounted, onBeforeUnmount, watch, ref } from "vue";
import L from "leaflet";
import "leaflet/dist/leaflet.css";

type Place = {
  name: string;
  lat: number | string;
  lon: number | string;
  tags?: string[];
  estimated_cost?: number;
};

const props = defineProps<{
  places: Place[];
}>();

const mapRef = ref<HTMLDivElement | null>(null);

let map: L.Map | null = null;
let markerLayer: L.LayerGroup | null = null;
let routeLayer: L.Polyline | null = null;

function escapeHtml(value: unknown) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function createMarkerIcon(index: number) {
  return L.divIcon({
    className: "custom-marker",
    html: `<div class="marker-pin">${index}</div>`,
    iconSize: [32, 32],
    iconAnchor: [16, 16]
  });
}

function drawPlaces() {
  if (!map || !markerLayer) return;

  markerLayer.clearLayers();

  if (routeLayer) {
    map.removeLayer(routeLayer);
    routeLayer = null;
  }

  const validPlaces = props.places
    .map((place) => ({
      ...place,
      lat: Number(place.lat),
      lon: Number(place.lon)
    }))
    .filter((place) => !Number.isNaN(place.lat) && !Number.isNaN(place.lon));

  if (validPlaces.length === 0) {
    map.setView([-27.47, 153.03], 11);
    return;
  }

  const latlngs: [number, number][] = [];

  validPlaces.forEach((place, index) => {
    const latlng: [number, number] = [place.lat, place.lon];
    latlngs.push(latlng);

    const popupContent = `
      <strong>${escapeHtml(place.name)}</strong><br/>
      Tags: ${escapeHtml((place.tags || []).join(", ") || "general")}<br/>
      Estimated cost: $${escapeHtml(place.estimated_cost ?? 0)}
    `;

    L.marker(latlng, {
      icon: createMarkerIcon(index + 1)
    })
      .addTo(markerLayer!)
      .bindPopup(popupContent);
  });

  if (latlngs.length >= 2) {
    routeLayer = L.polyline(latlngs, {
      weight: 4
    }).addTo(map);

    map.fitBounds(L.latLngBounds(latlngs), {
      padding: [40, 40],
      animate: false
    });
  } else {
    map.setView(latlngs[0], 13);
  }
}

onMounted(() => {
  if (!mapRef.value) return;

  map = L.map(mapRef.value, { zoomAnimation: false }).setView([-27.47, 153.03], 11);

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
    attribution: "&copy; OpenStreetMap contributors"
  }).addTo(map);

  markerLayer = L.layerGroup().addTo(map);

  drawPlaces();
});

watch(
  () => props.places,
  () => {
    drawPlaces();
  },
  { deep: true }
);

onBeforeUnmount(() => {
  map?.stop();
  map?.remove();
  map = null;
});
</script>

<template>
  <div class="map-wrapper">
    <div ref="mapRef" class="map"></div>
  </div>
</template>

<style scoped>
.map-wrapper {
  width: 100%;
  height: 460px;
  border-radius: 22px;
  overflow: hidden;
  background: #e2e8f0;
  box-shadow: 0 10px 28px rgba(15, 23, 42, 0.08);
}

.map {
  width: 100%;
  height: 100%;
}

:deep(.custom-marker) {
  background: transparent;
  border: none;
}

:deep(.marker-pin) {
  width: 32px;
  height: 32px;
  border-radius: 50%;
  background: #14735f;
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  font-weight: 800;
  border: 3px solid white;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
}
</style>

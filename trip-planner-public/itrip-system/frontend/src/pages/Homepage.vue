<script setup lang="ts">
import { ref, computed } from "vue";
import { useRouter } from "vue-router";

const router = useRouter();

const startDate = ref("");
const endDate = ref("");

const origin = ref("Brisbane");
const destination = ref("Brisbane");
const budget = ref(800);
const preference = ref("Nature");
const loading = ref(false);

const preferences = [
  "Popular",
  "Nature",
  "Culture",
  "Food",
  "Adventure",
  "Relaxation"
];

const featuredHotels = ref([
  {
    id: 1,
    name: "Sydney Harbour Hotel",
    price: 220,
    rating: 4.7,
    image:
      "https://images.unsplash.com/photo-1506744038136-46273834b3fb?auto=format&fit=crop&w=900&q=80"
  },
  {
    id: 2,
    name: "Relax Ocean Resort",
    price: 349,
    rating: 4.8,
    image:
      "https://images.unsplash.com/photo-1507525428034-b723cf961d3e?auto=format&fit=crop&w=900&q=80"
  },
  {
    id: 3,
    name: "Mountain View Retreat",
    price: 180,
    rating: 4.6,
    image:
      "https://images.unsplash.com/photo-1500530855697-b586d89ba3ee?auto=format&fit=crop&w=900&q=80"
  }
]);

const popularDestinations = ref([
  {
    id: 1,
    name: "Melbourne, Australia",
    tags: "Art + Culture + Food",
    plan: "3-Day Itinerary",
    image:
      "https://images.unsplash.com/photo-1514395462725-fb4566210144?auto=format&fit=crop&w=900&q=80"
  },
  {
    id: 2,
    name: "Gold Coast, Australia",
    tags: "Beach + Surfing + Fun",
    plan: "4-Day Itinerary",
    image:
      "https://images.unsplash.com/photo-1500375592092-40eb2168fd21?auto=format&fit=crop&w=900&q=80"
  },
  {
    id: 3,
    name: "Cairns, Australia",
    tags: "Nature + Adventure",
    plan: "5-Day Itinerary",
    image:
      "https://images.unsplash.com/photo-1501785888041-af3ef285b470?auto=format&fit=crop&w=900&q=80"
  }
]);

const totalDays = computed(() => {
  if (!startDate.value || !endDate.value) {
    return 3;
  }

  const start = new Date(startDate.value);
  const end = new Date(endDate.value);

  const diff =
    Math.ceil((end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1;

  return diff > 0 ? diff : "";
});

async function generatePlan() {
  if (!startDate.value || !endDate.value) {
    alert("Please select both start date and end date.");
    return;
  }

  if (new Date(endDate.value) < new Date(startDate.value)) {
    alert("End date cannot be earlier than start date.");
    return;
  }

  if (!origin.value || !destination.value) {
    alert("Please enter origin and destination.");
    return;
  }

  loading.value = true;

  try {
    const query = new URLSearchParams({
      origin: origin.value,
      destination: destination.value,
      days: String(totalDays.value),
      budget: String(budget.value),
      preference: preference.value || "Popular"
    }).toString();

    const res = await fetch(`/plan/?${query}`);

    if (!res.ok) {
      const failure = await res.json().catch(() => null);
      throw new Error(typeof failure?.detail === "string"
        ? failure.detail
        : `Unable to generate a plan (${res.status}). Check your inputs and try again.`);
    }

    const data = await res.json();

    localStorage.setItem("trip_result", JSON.stringify(data));
    localStorage.setItem(
      "trip_search",
      JSON.stringify({
        origin: origin.value,
        destination: destination.value,
        startDate: startDate.value,
        endDate: endDate.value,
        days: totalDays.value,
        budget: budget.value,
        preference: preference.value
      })
    );

    router.push("/planner");
  } catch (error: any) {
    console.error("Failed to generate trip plan:", error);
    alert(error.message || "Failed to generate trip plan.");
  } finally {
    loading.value = false;
  }
}
</script>

<template>
  <div class="home-page">
    <header class="navbar">
      <div class="logo">Intelligent Trip Planning System</div>

      <nav class="nav-links">
        <a href="#">Home</a>
        <a href="#">Route Planner</a>
        <a href="#">Attractions</a>
        <a href="#">Weather</a>
        <a href="#">Hotels</a>
        <a href="#">My Plan</a>
      </nav>
    </header>

    <section class="hero">
      <div class="hero-left">
        <p class="eyebrow">Smart Travel Assistant</p>
        <h1>Plan Your Perfect Trip Smartly</h1>
        <p>
          Generate travel plans using weather forecasts, attraction data,
          budget estimation, and preference-based itinerary recommendations.
        </p>
      </div>

      <div class="hero-right">
        <div class="hero-map-bg">
          <div class="map-label">
            <h3>Map Preview</h3>
            <p>Recommended places can be displayed here later.</p>
          </div>
        </div>
      </div>
    </section>

    <section class="search-panel">
      <div class="top-row">
        <div class="field">
          <label>Start Date</label>
          <input v-model="startDate" type="date" required />
        </div>

        <div class="field">
          <label>End Date</label>
          <input v-model="endDate" type="date" required />
        </div>

        <div class="field">
          <label>From</label>
          <input v-model="origin" type="text" placeholder="e.g. Brisbane" />
        </div>

        <div class="field">
          <label>To</label>
          <input v-model="destination" type="text" placeholder="e.g. Sydney" />
        </div>

        <div class="field">
          <label>Travel Days</label>
          <input :value="totalDays" type="number" readonly />
        </div>

        <div class="field">
          <label>Budget</label>
          <input
            v-model.number="budget"
            type="number"
            min="0"
            placeholder="e.g. 800"
          />
        </div>
      </div>

      <div class="preference-card">
        <h3>Preferences</h3>
        <p class="sub-text">
          Choose your travel preference. The backend will use this together
          with weather and attraction tags to generate recommendations.
        </p>

        <div class="preference-options">
          <button
            v-for="item in preferences"
            :key="item"
            type="button"
            :class="['pref-btn', preference === item ? 'active' : '']"
            @click="preference = item"
          >
            {{ item }}
          </button>

          <button type="button" class="clear-btn" @click="preference = 'Popular'">
            Use Popular
          </button>
        </div>

        <div class="summary-box">
          <p><strong>Origin:</strong> {{ origin || "Not selected" }}</p>
          <p><strong>Destination:</strong> {{ destination || "Not selected" }}</p>
          <p><strong>Days:</strong> {{ totalDays }}</p>
          <p><strong>Budget:</strong> ${{ budget }}</p>
          <p><strong>Preference:</strong> {{ preference }}</p>
        </div>

        <button class="generate-btn" @click="generatePlan" :disabled="loading">
          {{ loading ? "Generating..." : "Generate Plan" }}
        </button>
      </div>
    </section>

    <section class="content-section">
      <div class="section-header">
        <h2>Featured Hotels</h2>
        <button class="view-btn">View All Hotels</button>
      </div>

      <div class="card-grid">
        <div class="card" v-for="hotel in featuredHotels" :key="hotel.id">
          <img :src="hotel.image" :alt="hotel.name" />

          <div class="card-body">
            <h3>{{ hotel.name }}</h3>
            <p class="price">${{ hotel.price }} / night</p>
            <p class="rating">⭐ {{ hotel.rating }}</p>
          </div>
        </div>
      </div>
    </section>

    <section class="content-section">
      <div class="section-header">
        <h2>Popular Destinations</h2>
        <button class="view-btn">View All Destinations</button>
      </div>

      <div class="card-grid">
        <div class="card" v-for="place in popularDestinations" :key="place.id">
          <img :src="place.image" :alt="place.name" />

          <div class="card-body">
            <h3>{{ place.name }}</h3>
            <p class="plan">{{ place.plan }}</p>
            <p class="tags">{{ place.tags }}</p>
          </div>
        </div>
      </div>
    </section>
  </div>
</template>

<style scoped>
* {
  box-sizing: border-box;
}

.home-page {
  min-height: 100vh;
  background: linear-gradient(to bottom, #f8fafc, #eef6f2);
  color: #1f2937;
  font-family: Arial, Helvetica, sans-serif;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 24px 48px;
  background: rgba(255, 255, 255, 0.95);
  border-bottom: 1px solid #e5e7eb;
  position: sticky;
  top: 0;
  z-index: 10;
}

.logo {
  font-size: 24px;
  font-weight: 800;
  color: #184e42;
}

.nav-links {
  display: flex;
  gap: 24px;
}

.nav-links a {
  text-decoration: none;
  color: #374151;
  font-weight: 500;
}

.nav-links a:hover {
  color: #1f7a67;
}

.hero {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 24px;
  align-items: center;
  padding: 48px;
}

.eyebrow {
  color: #1f7a67;
  font-weight: 800;
  margin-bottom: 12px;
}

.hero-left h1 {
  font-size: 52px;
  line-height: 1.1;
  margin-bottom: 16px;
  color: #0f172a;
}

.hero-left p {
  font-size: 18px;
  color: #4b5563;
  max-width: 600px;
}

.hero-right {
  display: flex;
  justify-content: center;
  align-items: center;
}

.hero-map-bg {
  width: 100%;
  height: 300px;
  border-radius: 28px;
  background:
    radial-gradient(circle at 20% 30%, #bfe8dd, transparent 30%),
    radial-gradient(circle at 80% 60%, #cfd8e3, transparent 30%),
    linear-gradient(135deg, #d8efe7, #edf6f1);
  box-shadow: 0 14px 34px rgba(0, 0, 0, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
}

.map-label {
  text-align: center;
  background: rgba(255, 255, 255, 0.75);
  padding: 28px;
  border-radius: 22px;
}

.map-label h3 {
  margin: 0 0 8px;
  color: #0f172a;
}

.map-label p {
  margin: 0;
  color: #64748b;
}

.search-panel {
  margin: 0 48px 32px;
  background: rgba(255, 255, 255, 0.92);
  border-radius: 24px;
  padding: 28px;
  box-shadow: 0 12px 32px rgba(0, 0, 0, 0.08);
}

.top-row {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 16px;
}

.field {
  display: flex;
  flex-direction: column;
}

.field label {
  font-size: 14px;
  font-weight: 700;
  margin-bottom: 8px;
  color: #334155;
}

.field input {
  padding: 12px 14px;
  border: 1px solid #d1d5db;
  border-radius: 12px;
  font-size: 15px;
  outline: none;
  background: white;
}

.field input:focus {
  border-color: #1f7a67;
}

.preference-card {
  margin-top: 24px;
  background: #f8fbfa;
  border: 1px solid #e5eeea;
  border-radius: 20px;
  padding: 24px;
}

.preference-card h3 {
  font-size: 24px;
  margin-bottom: 8px;
}

.sub-text {
  color: #6b7280;
  margin-bottom: 18px;
}

.preference-options {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 18px;
}

.pref-btn,
.clear-btn,
.generate-btn,
.view-btn {
  border: none;
  border-radius: 12px;
  cursor: pointer;
  transition: 0.2s ease;
}

.pref-btn,
.clear-btn {
  padding: 10px 16px;
  background: white;
  border: 1px solid #d1d5db;
  font-weight: 600;
}

.pref-btn.active {
  background: #2d6a5c;
  color: white;
  border-color: #2d6a5c;
}

.clear-btn {
  background: #f3f4f6;
}

.summary-box {
  display: grid;
  grid-template-columns: repeat(5, 1fr);
  gap: 12px;
  margin: 20px 0;
}

.summary-box p {
  margin: 0;
  background: white;
  border: 1px solid #e2e8f0;
  padding: 12px;
  border-radius: 14px;
  color: #475569;
}

.generate-btn {
  padding: 14px 26px;
  background: linear-gradient(135deg, #2d6a5c, #3f8c7a);
  color: white;
  font-size: 16px;
  font-weight: 700;
}

.generate-btn:hover {
  opacity: 0.92;
}

.generate-btn:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.content-section {
  padding: 0 48px 40px;
}

.section-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 18px;
}

.section-header h2 {
  font-size: 32px;
  color: #0f172a;
}

.view-btn {
  padding: 10px 16px;
  background: white;
  border: 1px solid #d1d5db;
  font-weight: 600;
}

.card-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 22px;
}

.card {
  overflow: hidden;
  border-radius: 22px;
  background: white;
  box-shadow: 0 10px 24px rgba(0, 0, 0, 0.08);
}

.card img {
  width: 100%;
  height: 220px;
  object-fit: cover;
}

.card-body {
  padding: 18px;
}

.card-body h3 {
  margin: 0 0 10px;
  font-size: 24px;
  color: #111827;
}

.price,
.rating,
.plan,
.tags {
  margin: 6px 0;
  color: #4b5563;
  font-size: 16px;
}

@media (max-width: 1200px) {
  .top-row,
  .summary-box {
    grid-template-columns: repeat(2, 1fr);
  }

  .hero,
  .card-grid {
    grid-template-columns: 1fr;
  }

  .nav-links {
    display: none;
  }
}

@media (max-width: 700px) {
  .navbar,
  .hero,
  .search-panel,
  .content-section {
    padding-left: 20px;
    padding-right: 20px;
  }

  .search-panel {
    margin-left: 20px;
    margin-right: 20px;
  }

  .top-row,
  .summary-box {
    grid-template-columns: 1fr;
  }

  .hero-left h1 {
    font-size: 36px;
  }
}
</style>

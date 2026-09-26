<script setup lang="ts">
import { computed, ref, watch } from "vue";
import TripMap from "./TripMap.vue";

const props = defineProps<{ plan: any; searchInfo?: any }>();
const dayIndex = ref(0);
const selectedDate = ref("");
const rows = ref<any[]>([]);
const eventType = ref("late_departure");
const currentTime = ref("");
const plannedDeparture = ref("");
const horizonEnd = ref("");
const rainStart = ref("");
const rainEnd = ref("");
const delay = ref(40);
const latitude = ref<number | string>("");
const longitude = ref<number | string>("");
const budget = ref(0);
const committedCost = ref<number | string>(0);
const committedVerified = ref(false);
const transportCost = ref<number | string>("");
const confirmed = ref(false);
const loading = ref(false);
const error = ref("");
const response = ref<any>(null);
const selectedAlternative = ref(0);
const browserElapsed = ref(0);
const days = computed(() => props.plan?.daily_plan || []);
const actionLabels: Record<string, string> = { completed: "已完成，不变", retained: "保留", moved: "移动", replaced: "替换", deleted: "删除" };
const statusLabels: Record<string, string> = { ok: "已生成三种不同方案", limited_alternatives: "可用方案不足三种", no_feasible_solution: "所提供数据的硬约束下无可行方案", search_limit: "搜索达到限制，未找到方案（不代表绝对无解）", insufficient_data: "缺少必要数据，无法生成方案" };

function dateText(date: Date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}
function localText(date: Date) {
  return `${dateText(date)}T${String(date.getHours()).padStart(2, "0")}:${String(date.getMinutes()).padStart(2, "0")}`;
}
function key(place: any) { return `${place.name}|${place.lat}|${place.lon}`; }
const pool = computed(() => {
  const unique = new Map<string, any>();
  [...(props.plan?.places || []), ...days.value.flatMap((d: any) => d.activities || [])].forEach((p: any) => {
    if (!unique.has(key(p))) unique.set(key(p), p);
  });
  return Array.from(unique.values()).map((p, index) => ({ ...p, placeId: `poi-${index}` }));
});

function resetDay() {
  const day = days.value[dayIndex.value];
  if (!day) return;
  const base = props.searchInfo?.startDate || (/^\d{4}-\d{2}-\d{2}$/.test(day.date) ? day.date : dateText(new Date()));
  const date = new Date(`${base}T12:00`);
  if (props.searchInfo?.startDate) date.setDate(date.getDate() + dayIndex.value);
  selectedDate.value = dateText(date);
  resetSchedule();
}
function resetSchedule() {
  const day = days.value[dayIndex.value];
  if (!day || !selectedDate.value) return;
  let cursor = new Date(`${selectedDate.value}T09:00`);
  rows.value = (day.activities || []).map((place: any, index: number) => {
    const minutes = Math.max(1, Math.round((place.duration || 2) * 60));
    const start = localText(cursor);
    cursor = new Date(cursor.getTime() + minutes * 60_000);
    const end = localText(cursor);
    cursor = new Date(cursor.getTime() + 15 * 60_000);
    const tags = place.tags || [];
    return { id: `day-${day.day}-activity-${index}`, placeId: pool.value.find(p => key(p) === key(place))?.placeId,
      name: place.name, start, end, minutes, durationVerified: false, cost: place.estimated_cost ?? "", costVerified: false,
      outdoor: tags.includes("outdoor") && !tags.includes("indoor") ? "outdoor" : tags.includes("indoor") && !tags.includes("outdoor") ? "indoor" : "unknown",
      outdoorVerified: false, openingStart: "", openingEnd: "", closed: false, mustVisit: false, fixed: false, completed: false, cancellationCost: "" };
  });
  currentTime.value = `${selectedDate.value}T09:00`;
  plannedDeparture.value = currentTime.value;
  horizonEnd.value = `${selectedDate.value}T20:00`;
  rainStart.value = `${selectedDate.value}T10:00`;
  rainEnd.value = `${selectedDate.value}T14:00`;
  const first = day.activities?.[0];
  latitude.value = first?.lat ?? "";
  longitude.value = first?.lon ?? "";
  budget.value = props.plan?.budget ?? 0;
  // Other days are outside this editable horizon, but must still count in the total budget.
  committedCost.value = days.value.reduce((total: number, d: any, index: number) => index === dayIndex.value ? total : total + (d.activities || []).reduce((sum: number, p: any) => sum + (p.estimated_cost || 0), 0), 0);
  committedVerified.value = false;
  confirmed.value = false;
  response.value = null;
  error.value = "";
}
watch(() => props.plan, resetDay, { immediate: true });
watch(dayIndex, resetDay);

function numeric(value: any): number | null {
  if (value === "" || value === null || value === undefined) return null;
  const num = Number(value);
  if (!Number.isFinite(num)) throw new Error("请输入有效数字。");
  return num;
}
function iso(value: string) {
  const date = new Date(value);
  if (!value || Number.isNaN(date.getTime())) throw new Error("请填写完整日期和时间。");
  return date.toISOString();
}
function normalizedPlace(p: any) {
  const row = rows.value.find(r => r.placeId === p.placeId);
  const tags = p.tags || [];
  const outdoor = row?.outdoor || (tags.includes("outdoor") && !tags.includes("indoor") ? "outdoor" : tags.includes("indoor") && !tags.includes("outdoor") ? "indoor" : "unknown");
  let opening = null;
  if (row?.closed) opening = [];
  else if (row?.openingStart || row?.openingEnd) opening = [{ start: iso(row.openingStart), end: iso(row.openingEnd) }];
  const lat = numeric(p.lat), lon = numeric(p.lon);
  return { id: p.placeId, name: p.name, location: lat === null || lon === null ? null : { lat, lon },
    outdoor: outdoor === "unknown" ? null : outdoor === "outdoor", outdoor_verified: row?.outdoorVerified || false, duration_minutes: row ? numeric(row.minutes) : p.duration ? Math.round(p.duration * 60) : null,
    duration_verified: row?.durationVerified || false, cost: row ? numeric(row.cost) : numeric(p.estimated_cost), cost_verified: row?.costVerified || false,
    opening_windows: opening };
}
async function submit() {
  error.value = "";
  response.value = null;
  if (!confirmed.value) { error.value = "请先核对原时间表和当前位置，并勾选确认。"; return; }
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 45_000);
  loading.value = true;
  const started = performance.now();
  try {
    const places = pool.value.map(normalizedPlace);
    const lat = numeric(latitude.value), lon = numeric(longitude.value);
    if (lat === null || lon === null) throw new Error("当前位置不能为空。");
    const activities = rows.value.map(row => ({ id: row.id, place: places.find(p => p.id === row.placeId),
      start: iso(row.start), end: iso(row.end), must_visit: row.mustVisit, fixed_time: row.fixed,
      cancellation_cost: numeric(row.cancellationCost) }));
    const originalIds = new Set(activities.map(a => a.place?.id));
    const payload = { activities, candidates: places.filter(p => !originalIds.has(p.id)).slice(0, 20),
      current_time: iso(currentTime.value), current_location: { lat, lon }, horizon_end: iso(horizonEnd.value),
      completed_activity_ids: rows.value.filter(r => r.completed).map(r => r.id), locked_activity_ids: rows.value.filter(r => r.fixed).map(r => r.id),
      event: eventType.value === "late_departure" ? { type: "late_departure", planned_departure: iso(plannedDeparture.value), delay_minutes: Number(delay.value) } : { type: "rain", start: iso(rainStart.value), end: iso(rainEnd.value) },
      total_budget: Number(budget.value), committed_cost: numeric(committedCost.value) ?? 0, committed_cost_verified: committedVerified.value,
      transport_cost: numeric(transportCost.value), original_schedule_verified: confirmed.value };
    const res = await fetch("/plan/replan", { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(payload), signal: controller.signal });
    const data = await res.json();
    if (!res.ok) throw new Error(Array.isArray(data.detail) ? data.detail.map((d: any) => `${d.loc.join(".")}: ${d.msg}`).join("；") : data.detail || `请求失败：${res.status}`);
    response.value = data;
    selectedAlternative.value = 0;
  } catch (err: any) {
    error.value = err.name === "AbortError" ? "请求超时，可稍后重试。" : err.message;
  } finally {
    clearTimeout(timer);
    browserElapsed.value = Math.round(performance.now() - started);
    loading.value = false;
  }
}
function time(value: string) { return new Date(value).toLocaleString([], { month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" }); }
function money(value: number | null) { return value == null ? "未验证／缺失" : `$${value.toFixed(2)}`; }
const preview = computed(() => (response.value?.alternatives[selectedAlternative.value]?.activities || []).filter((a: any) => a.place.location).map((a: any) => ({ name: a.place.name, lat: a.place.location.lat, lon: a.place.location.lon, estimated_cost: a.place.cost })));
</script>

<template>
  <section class="replan-panel">
    <h2>突发事件：最小扰动重规划</h2>
    <p>选择一天调整；其他日期保持不变，其费用计入总预算。每次最多 8 项原活动、20 个替换候选。</p>
    <p class="notice">现有行程没有起止时间。下方从 09:00 开始、活动间隔 15 分钟的时间表仅是编辑草稿，并非已验证路线。时间按浏览器所在时区输入。请核对后提交。</p>
    <form @submit.prevent="submit">
      <fieldset :disabled="loading">
        <div class="fields">
          <label>调整日期<select v-model.number="dayIndex"><option v-for="(day, index) in days" :key="day.day" :value="index">Day {{ day.day }}</option></select></label>
          <label>实际日期<input v-model="selectedDate" type="date" required @change="resetSchedule" /></label>
          <label>当前时间<input v-model="currentTime" type="datetime-local" required /></label>
          <label>行程截止时间<input v-model="horizonEnd" type="datetime-local" required /></label>
          <label>当前位置纬度<input v-model="latitude" type="number" step="any" min="-90" max="90" required /></label>
          <label>当前位置经度<input v-model="longitude" type="number" step="any" min="-180" max="180" required /></label>
          <label>事件<select v-model="eventType"><option value="late_departure">晚出发</option><option value="rain">户外时段降雨</option></select></label>
          <template v-if="eventType === 'late_departure'">
            <label>原计划出发时间<input v-model="plannedDeparture" type="datetime-local" required /></label>
            <label>延迟分钟<input v-model.number="delay" type="number" min="1" max="720" required /></label>
          </template>
          <template v-else>
            <label>降雨开始<input v-model="rainStart" type="datetime-local" required /></label>
            <label>降雨结束<input v-model="rainEnd" type="datetime-local" required /></label>
          </template>
        </div>
        <p>当前位置初始值来自第一个景点，请改为实际位置。晚出发从“原计划出发时间＋延迟”计算，与当前时间取较晚者，不重复累计。</p>
        <div class="table-wrap">
          <table>
            <caption>原行程与不可变约束</caption>
            <thead><tr><th>活动</th><th>原时间与停留</th><th>限制</th><th>开放时段与费用</th></tr></thead>
            <tbody><tr v-for="row in rows" :key="row.id">
              <td>{{ row.name }}<select v-model="row.outdoor" :aria-label="`${row.name}室内外`"><option value="unknown">室内外未知</option><option value="indoor">室内</option><option value="outdoor">户外</option></select><label class="check"><input v-model="row.outdoorVerified" type="checkbox" />室内外已核实</label></td>
              <td><label>开始<input v-model="row.start" type="datetime-local" required /></label><label>结束<input v-model="row.end" type="datetime-local" required /></label><label>停留分钟<input v-model.number="row.minutes" type="number" min="1" max="1440" required /></label><label class="check"><input v-model="row.durationVerified" type="checkbox" />停留时间已核实</label></td>
              <td><label class="check"><input v-model="row.completed" type="checkbox" />已完成</label><label class="check"><input v-model="row.mustVisit" type="checkbox" />必去，不可替换</label><label class="check"><input v-model="row.fixed" type="checkbox" />固定预约，不可移动</label></td>
              <td><label>开放起<input v-model="row.openingStart" type="datetime-local" :disabled="row.closed" /></label><label>开放止<input v-model="row.openingEnd" type="datetime-local" :disabled="row.closed" /></label><label class="check"><input v-model="row.closed" type="checkbox" />当天关闭</label><label>活动费用<input v-model="row.cost" type="number" min="0" step="0.01" placeholder="未知留空" /></label><label class="check"><input v-model="row.costVerified" type="checkbox" />费用已核实</label><label>取消费用<input v-model="row.cancellationCost" type="number" min="0" step="0.01" placeholder="未知留空，无费用填0" /></label></td>
            </tr></tbody>
          </table>
        </div>
        <p>开放时段留空表示未验证；填写表示你提供了已确认的开放窗口。已完成活动的费用仍计入总预算。</p>
        <div class="fields">
          <label>全程总预算<input v-model.number="budget" type="number" min="0" step="0.01" required /></label>
          <label>其他日期／住宿／餐饮／已承诺费用<input v-model="committedCost" type="number" min="0" step="0.01" required /></label>
          <label>覆盖所有方案的固定交通费用（如日票）<input v-model="transportCost" type="number" min="0" step="0.01" placeholder="未知／按里程计费则留空" /></label>
        </div>
        <label class="check"><input v-model="committedVerified" type="checkbox" />已核对其他费用完整，且没有重复计算上表活动费用（此值将视为各方案共同的固定支出）</label>
        <label class="check"><input v-model="confirmed" type="checkbox" required />我已核对原始时间表与当前位置</label>
        <button type="submit" :disabled="!rows.length || rows.length > 8">{{ loading ? '正在校验并比较方案…' : '生成重规划方案' }}</button>
      </fieldset>
    </form>
    <p v-if="error" role="alert" class="error">{{ error }}</p>
    <div v-if="response" aria-live="polite">
      <h3>{{ statusLabels[response.status] }}</h3>
      <p>数据获取 {{ response.timings.data_fetch_ms }} ms · 重规划 {{ response.timings.replanning_compute_ms }} ms · 服务端端到端 {{ response.timings.end_to_end_ms }} ms · 浏览器往返 {{ browserElapsed }} ms</p>
      <p>交通来源：{{ response.data_sources.travel }} · 缓存写入：{{ response.data_sources.cache_write }} · 搜索状态数：{{ response.evaluated_states }}</p>
      <ul><li v-for="notice in response.notices" :key="notice">{{ notice }}</li></ul>
      <h4>原行程剩余部分的冲突</h4>
      <p v-if="!response.original_conflicts.length">未发现已知冲突；未验证项仍需核实。</p>
      <ul><li v-for="(conflict, index) in response.original_conflicts" :key="index">{{ conflict.message }} {{ conflict.activity_ids.join(', ') }}</li></ul>
      <ul class="error"><li v-for="(conflict, index) in response.blocking_constraints" :key="index">{{ conflict.message }} {{ conflict.activity_ids.join(', ') }}</li></ul>
      <details v-if="response.unverified_constraints.length"><summary>原行程输入中未验证的约束（{{ response.unverified_constraints.length }}）</summary><ul><li v-for="(warning, index) in response.unverified_constraints" :key="index">{{ warning.message }} {{ warning.activity_ids.join(', ') }}</li></ul></details>
      <div class="alternatives">
        <article v-for="(alt, index) in response.alternatives" :key="alt.objective">
          <h3>{{ alt.label }}</h3>
          <p :class="{ notice: alt.feasibility === 'conditional' }">{{ alt.feasibility === 'conditional' ? '条件可行：包含未验证约束' : '满足所提供的已验证约束' }}</p>
          <p>预计结束：{{ time(alt.end_time) }}<br />从可出发时刻起：{{ alt.elapsed_minutes }} 分钟（含等待）<br />交通：{{ alt.travel_minutes }} 分钟 / {{ alt.travel_distance_km ?? '未知' }} km</p>
          <p>可用费用小计（含估计）：{{ money(alt.known_cost) }}<br />完整预计费用：{{ money(alt.estimated_total_cost) }}<br />相比原行程费用差：{{ money(alt.extra_cost) }}</p>
          <ol><li v-for="activity in alt.activities" :key="activity.id">{{ activity.place.name }}<br />{{ time(activity.start) }} → {{ time(activity.end) }}</li></ol>
          <details open><summary>调整前后差异</summary><div v-for="change in alt.changes" :key="change.activity_id" class="change"><strong>{{ actionLabels[change.action] }}：{{ change.before.place.name }}</strong><p>原：{{ time(change.before.start) }} → {{ time(change.before.end) }}</p><p v-if="change.after">新：{{ change.after.place.name }} {{ time(change.after.start) }} → {{ time(change.after.end) }}</p><ul><li v-for="reason in change.reasons" :key="reason">{{ reason }}</li></ul></div></details>
          <details v-if="alt.unverified.length"><summary>未验证约束（{{ alt.unverified.length }}）</summary><ul><li v-for="(warning, wi) in alt.unverified" :key="wi">{{ warning.message }} {{ warning.activity_ids.join(', ') }}</li></ul></details>
          <button type="button" @click="selectedAlternative = Number(index)">在地图预览</button>
        </article>
      </div>
      <div v-if="response.alternatives.length"><h4>{{ response.alternatives[selectedAlternative].label }}：调整后景点（连线仅示意，不是导航路线）</h4><TripMap :key="selectedAlternative" :places="preview" /></div>
    </div>
  </section>
</template>

<style scoped>
.replan-panel { background: white; border-radius: 20px; padding: 24px; margin: 30px 0; color: #17342e; }
fieldset { border: 0; padding: 0; min-width: 0; }
.fields { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 14px; margin: 16px 0; }
label { display: flex; flex-direction: column; gap: 6px; margin: 7px 0; font-size: 14px; }
input, select { padding: 9px; border: 1px solid #aebfb8; border-radius: 6px; min-width: 0; }
.check { flex-direction: row; align-items: center; }
button { background: #14735f; color: white; border: 0; border-radius: 8px; padding: 12px 20px; cursor: pointer; margin: 12px 0; }
button:disabled { opacity: .5; cursor: wait; }
.notice { padding: 12px; background: #fff4d4; border-left: 4px solid #b88300; }
.error { color: #a72323; white-space: pre-wrap; }
.table-wrap { overflow-x: auto; }
table { border-collapse: collapse; width: 100%; min-width: 780px; }
caption { text-align: left; font-weight: bold; padding: 12px 0; }
th, td { text-align: left; vertical-align: top; padding: 12px; border: 1px solid #dce6e1; }
.alternatives { display: grid; grid-template-columns: repeat(auto-fit, minmax(290px, 1fr)); gap: 16px; }
article { padding: 16px; background: #f6faf8; border: 1px solid #dae5df; border-radius: 12px; overflow-wrap: anywhere; }
li { margin: 7px 0; }
.change { border-top: 1px solid #ceded5; padding: 12px 0; font-size: 14px; }
summary { cursor: pointer; font-weight: bold; padding: 12px 0; }
</style>

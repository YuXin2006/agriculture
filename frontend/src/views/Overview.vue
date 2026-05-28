<template>
  <div class="overview-page">
    <header class="page-header">
      <div class="page-header__left">
        <h1>基地总览</h1>
        <p class="breadcrumb">{{ meta.location }}</p>
        <p class="updated">最后更新：{{ meta.last_updated }}</p>
      </div>
      <div class="page-header__right">
        <button type="button" class="weather-pill" @click="weatherOpen = true">
          {{ liveWeather.icon || "☁" }}
          {{ liveWeather.text || "—" }}
          {{ weatherTemp }}
        </button>
        <button type="button" class="icon-btn" aria-label="通知">🔔</button>
        <div class="user-pill">
          <span class="user-avatar">管</span>
          <span>管理员</span>
        </div>
      </div>
    </header>

    <section class="hero-banner dash-card">
      <div class="hero-banner__overlay" />
      <div class="hero-stats">
        <div v-for="item in summaryStats" :key="item.label" class="hero-stat">
          <span class="hero-stat__icon">{{ item.icon }}</span>
          <div>
            <strong>{{ item.value }}</strong>
            <span>{{ item.label }}</span>
          </div>
        </div>
      </div>
    </section>
      <!-- 传感器数据部分 -->
    <section class="sensor-section">
      <div class="sensor-grid">
        <article
          v-for="card in sensorCards"
          :key="card.key"
          class="sensor-card dash-card"
        >
          <div class="sensor-card__head">
            <span class="sensor-card__icon">{{ card.icon }}</span>
            <span class="sensor-card__label">{{ card.label }}</span>
          </div>
          <div class="sensor-card__value">
            {{ card.display }}
            <small v-if="card.unit">{{ card.unit }}</small>
          </div>
          <svg
            v-if="card.trend?.length"
            class="sparkline"
            viewBox="0 0 120 28"
            preserveAspectRatio="none"
          >
            <polyline
              :points="sparklinePoints(card.trend)"
              fill="none"
              :stroke="card.color"
              stroke-width="1.5"
              stroke-linecap="round"
              stroke-linejoin="round"
            />
          </svg>
          <footer class="sensor-card__foot">
            <span>正常范围 {{ card.range }}</span>
            <span>{{ card.time }}</span>
          </footer>
        </article>
      </div>
      
      <aside class="alarm-panel dash-card">
        <h2>最新告警</h2>
        <ul v-if="alarms.length" class="alarm-list">
          <li v-for="alarm in alarms" :key="alarm.id" class="alarm-item">
            <span class="alarm-severity" :class="alarm.level">
              {{ alarm.level === "warn" || alarm.level === "critical" ? "!" : "i" }}
            </span>
            <div class="alarm-body">
              <p>{{ alarm.text }}</p>
              <span>{{ alarm.detail }}</span>
            </div>
            <time>{{ alarm.time }}</time>
          </li>
        </ul>
        <p v-else class="empty-hint">暂无告警</p>
      </aside>
    </section>

    <section class="charts-row">
      <div class="chart-card dash-card">
        <h2>环境温湿度（24h）</h2>
        <div ref="envChartRef" class="chart-box" />
      </div>
      <div class="chart-card dash-card">
        <h2>土壤湿度变化（24h）</h2>
        <div ref="soilChartRef" class="chart-box" />
      </div>
      <div class="chart-card dash-card chart-card--donut">
        <h2>空气质量分布</h2>
        <div ref="airChartRef" class="chart-box chart-box--donut" />
      </div>
    </section>

    <section class="bottom-row">
      <div class="device-panel dash-card">
        <h2>设备列表</h2>
        <div class="table-wrap">
          <table class="device-table">
            <thead>
              <tr>
                <th>节点名称</th>
                <th>节点编号</th>
                <th>设备类型</th>
                <th>区域</th>
                <th>状态</th>
                <th>最后更新</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="row in deviceRows" :key="row.id">
                <td>{{ row.name }}</td>
                <td class="mono">{{ row.node_id }}</td>
                <td>{{ row.device_type }}</td>
                <td>{{ row.region || "-" }}</td>
                <td>
                  <span
                    class="tag"
                    :class="row.status === 'online' ? 'tag--online' : 'tag--offline'"
                  >
                    {{ row.status === "online" ? "在线" : "离线" }}
                  </span>
                </td>
                <td>{{ row.updated }}</td>
              </tr>
              <tr v-if="loading">
                <td colspan="6">数据加载中...</td>
              </tr>
              <tr v-if="!loading && deviceRows.length === 0">
                <td colspan="6">暂无设备数据</td>
              </tr>
            </tbody>
          </table>
        </div>
        <div class="pagination">
          <button class="btn-secondary" @click="prevNodePage" :disabled="nodePage <= 1 || loading">
            上一页
          </button>
          <span>第 {{ nodePage }} / {{ nodeTotalPages || 1 }} 页</span>
          <button
            class="btn-secondary"
            @click="nextNodePage"
            :disabled="loading || nodePage >= nodeTotalPages || nodeTotalPages === 0"
          >
            下一页
          </button>
        </div>
      </div>

      <div class="kpi-panel dash-card">
        <h2>数据概览（近 24h）</h2>
        <div class="kpi-grid">
          <div v-for="kpi in kpiStats" :key="kpi.label" class="kpi-item">
            <strong>{{ kpi.value }}</strong>
            <span>{{ kpi.label }}</span>
          </div>
        </div>
      </div>
    </section>

    <WeatherModal
      v-model:visible="weatherOpen"
      v-model:city-id="weatherCityId"
      @summary="onWeatherSummary"
    />
  </div>
</template>

<script setup>
import { computed, nextTick, onMounted, onUnmounted, ref } from "vue";
import * as echarts from "echarts";
import { getOverview } from "../api/dashboard";
import WeatherModal from "../components/WeatherModal.vue";

const loading = ref(false);
const nodePage = ref(1);
const nodePageSize = 8;
const nodeTotalPages = ref(0);

const weatherOpen = ref(false);
const weatherCityId = ref(localStorage.getItem("weather_city_id") || "beijing");
const liveWeather = ref({ text: "—", temperature: null, icon: "☁" });

const meta = ref({
  location: "示范种植基地 · 温室 A 区",
  last_updated: "—",
  weather: { text: "多云", temperature: null, icon: "☁" },
});

const onWeatherSummary = (summary) => {
  liveWeather.value = summary;
};
const summaryStats = ref([]);
const sensorCards = ref([]);
const alarms = ref([]);
const kpiStats = ref([]);
const devices = ref([]);
const chart24h = ref({ labels: [], temperature: [], humidity: [], soil_moisture: [] });
const airQuality = ref({ items: [] });

const envChartRef = ref(null);
const soilChartRef = ref(null);
const airChartRef = ref(null);
let envChart;
let soilChart;
let airChart;

const weatherTemp = computed(() => {
  const t = liveWeather.value.temperature;
  return t != null && t !== "" ? `${t}°C` : "";
});

const formatTime = (value) => {
  if (!value) return "-";
  return String(value).replace("T", " ").slice(0, 19);
};

const deviceRows = computed(() =>
  devices.value.map((item) => ({
    id: item.id,
    name: item.name,
    node_id: item.node_id,
    device_type: item.device_type || "-",
    region: item.region,
    status: item.status,
    updated: formatTime(item.updated_at),
  }))
);

const sparklinePoints = (trend) => {
  if (!trend?.length) return "";
  const max = Math.max(...trend);
  const min = Math.min(...trend);
  const span = max - min || 1;
  const len = trend.length;
  return trend
    .map((v, i) => {
      const x = len > 1 ? (i / (len - 1)) * 120 : 60;
      const y = 26 - ((v - min) / span) * 22;
      return `${x},${y}`;
    })
    .join(" ");
};

const chartLabelFilter = (labels) => labels.filter((_, i) => i % 3 === 0);

const renderEnvChart = () => {
  if (!envChartRef.value) return;
  if (!envChart) envChart = echarts.init(envChartRef.value, "dark");
  const c = chart24h.value;
  const labels = c.labels?.length ? chartLabelFilter(c.labels) : [];
  envChart.setOption({
    backgroundColor: "transparent",
    grid: { left: 48, right: 48, top: 28, bottom: 28 },
    tooltip: { trigger: "axis" },
    legend: { data: ["温度", "湿度"], textStyle: { color: "#8b9bb5" }, top: 0 },
    xAxis: {
      type: "category",
      data: labels,
      axisLine: { lineStyle: { color: "#334155" } },
      axisLabel: { color: "#8b9bb5" },
    },
    yAxis: [
      {
        type: "value",
        name: "℃",
        axisLabel: { color: "#8b9bb5" },
        splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)" } },
      },
      {
        type: "value",
        name: "%",
        axisLabel: { color: "#8b9bb5" },
        splitLine: { show: false },
      },
    ],
    series: [
      {
        name: "温度",
        type: "line",
        smooth: true,
        symbol: "none",
        lineStyle: { color: "#3ddc84", width: 2 },
        data: c.temperature || [],
      },
      {
        name: "湿度",
        type: "line",
        smooth: true,
        symbol: "none",
        yAxisIndex: 1,
        lineStyle: { color: "#4da3ff", width: 2 },
        data: c.humidity || [],
      },
    ],
  });
};

const renderSoilChart = () => {
  if (!soilChartRef.value) return;
  if (!soilChart) soilChart = echarts.init(soilChartRef.value, "dark");
  const c = chart24h.value;
  const labels = c.labels?.length ? chartLabelFilter(c.labels) : [];
  soilChart.setOption({
    backgroundColor: "transparent",
    grid: { left: 48, right: 24, top: 28, bottom: 28 },
    tooltip: { trigger: "axis" },
    xAxis: {
      type: "category",
      data: labels,
      axisLine: { lineStyle: { color: "#334155" } },
      axisLabel: { color: "#8b9bb5" },
    },
    yAxis: {
      type: "value",
      name: "%",
      axisLabel: { color: "#8b9bb5" },
      splitLine: { lineStyle: { color: "rgba(255,255,255,0.06)" } },
    },
    series: [
      {
        type: "line",
        smooth: true,
        symbol: "none",
        lineStyle: { color: "#3ddc84", width: 2 },
        areaStyle: {
          color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
            { offset: 0, color: "rgba(61, 220, 132, 0.35)" },
            { offset: 1, color: "rgba(61, 220, 132, 0.02)" },
          ]),
        },
        data: c.soil_moisture || [],
      },
    ],
  });
};

const renderAirChart = () => {
  if (!airChartRef.value) return;
  if (!airChart) airChart = echarts.init(airChartRef.value, "dark");
  const items = airQuality.value.items || [];
  airChart.setOption({
    backgroundColor: "transparent",
    tooltip: { trigger: "item" },
    legend: {
      orient: "vertical",
      right: 8,
      top: "center",
      textStyle: { color: "#8b9bb5", fontSize: 11 },
    },
    series: [
      {
        type: "pie",
        radius: ["48%", "72%"],
        center: ["38%", "50%"],
        label: { show: false },
        data: items.map((item) => ({
          value: item.value,
          name: item.name,
          itemStyle: { color: item.color },
        })),
      },
    ],
  });
};

const renderCharts = async () => {
  await nextTick();
  renderEnvChart();
  renderSoilChart();
  renderAirChart();
};

const applyOverviewData = (data) => {
  if (data?.meta) meta.value = data.meta;
  summaryStats.value = Array.isArray(data?.summary_stats) ? data.summary_stats : [];
  sensorCards.value = Array.isArray(data?.sensor_cards) ? data.sensor_cards : [];
  alarms.value = Array.isArray(data?.alarms) ? data.alarms : [];
  kpiStats.value = Array.isArray(data?.kpi_stats) ? data.kpi_stats : [];
  chart24h.value = data?.chart_24h || chart24h.value;
  airQuality.value = data?.air_quality_distribution || { items: [] };

  const dev = data?.devices;
  devices.value = Array.isArray(dev?.results) ? dev.results : [];
  nodeTotalPages.value = Number(dev?.pagination?.total_pages || 0);
};

const loadOverview = async () => {
  loading.value = true;
  try {
    const data = await getOverview({ page: nodePage.value, page_size: nodePageSize });
    applyOverviewData(data);
    if (nodeTotalPages.value > 0 && nodePage.value > nodeTotalPages.value) {
      nodePage.value = nodeTotalPages.value;
      await loadOverview();
      return;
    }
    await renderCharts();
  } catch (error) {
    console.error("加载总览数据失败:", error);
    summaryStats.value = [];
    sensorCards.value = [];
    alarms.value = [];
    kpiStats.value = [];
    devices.value = [];
  } finally {
    loading.value = false;
  }
};

const prevNodePage = async () => {
  if (nodePage.value <= 1 || loading.value) return;
  nodePage.value -= 1;
  await loadOverview();
};

const nextNodePage = async () => {
  if (nodePage.value >= nodeTotalPages.value || loading.value) return;
  nodePage.value += 1;
  await loadOverview();
};

const resizeCharts = () => {
  envChart?.resize();
  soilChart?.resize();
  airChart?.resize();
};

onMounted(async () => {
  await loadOverview();
  window.addEventListener("resize", resizeCharts);
});

onUnmounted(() => {
  window.removeEventListener("resize", resizeCharts);
  envChart?.dispose();
  soilChart?.dispose();
  airChart?.dispose();
});
</script>

<style scoped>
.overview-page {
  padding: 20px 24px 28px;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.page-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.page-header h1 {
  margin: 0;
  font-size: 22px;
  font-weight: 700;
}

.breadcrumb {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: 13px;
}

.updated {
  margin: 4px 0 0;
  color: var(--text-secondary);
  font-size: 12px;
}

.page-header__right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.weather-pill,
.user-pill {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 8px;
  background: var(--bg-card);
  border: 1px solid var(--border);
  font-size: 13px;
  color: var(--text-secondary);
}

.weather-pill {
  cursor: pointer;
  font-family: inherit;
}

.weather-pill:hover {
  background: var(--bg-card-hover);
}

.icon-btn {
  width: 38px;
  height: 38px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg-card);
  cursor: pointer;
  font-size: 16px;
}

.user-avatar {
  width: 26px;
  height: 26px;
  border-radius: 50%;
  background: linear-gradient(135deg, #4da3ff, #2b6cb0);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.hero-banner {
  position: relative;
  min-height: 120px;
  overflow: hidden;
  background: linear-gradient(90deg, rgba(8, 20, 14, 0.95) 0%, rgba(8, 20, 14, 0.4) 55%, rgba(8, 20, 14, 0.85) 100%),
    url("https://images.unsplash.com/photo-1500382017468-9049fed747ef?w=1200&q=80") center / cover;
}

.hero-banner__overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(90deg, rgba(11, 18, 32, 0.75), transparent 40%, rgba(11, 18, 32, 0.5));
}

.hero-stats {
  position: relative;
  display: flex;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 28px;
  padding: 28px 32px;
}

.hero-stat {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 120px;
}

.hero-stat__icon {
  font-size: 28px;
  opacity: 0.9;
}

.hero-stat strong {
  display: block;
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.1;
}

.hero-stat span {
  font-size: 12px;
  color: var(--text-secondary);
}

.sensor-section {
  display: grid;
  grid-template-columns: 1fr 280px;
  gap: 16px;
  align-items: stretch;
}

.sensor-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.sensor-card {
  padding: 14px;
  display: flex;
  flex-direction: column;
  gap: 6px;
  min-height: 130px;
}

.sensor-card__head {
  display: flex;
  align-items: center;
  gap: 8px;
  color: var(--text-secondary);
  font-size: 13px;
}

.sensor-card__icon {
  font-size: 16px;
}

.sensor-card__value {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
  line-height: 1.1;
}

.sensor-card__value small {
  margin-left: 4px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-secondary);
}

.sparkline {
  width: 100%;
  height: 28px;
  margin-top: 4px;
}

.sensor-card__foot {
  display: flex;
  justify-content: space-between;
  gap: 8px;
  margin-top: auto;
  padding-top: 8px;
  border-top: 1px solid var(--border);
  font-size: 11px;
  color: var(--text-secondary);
}

.alarm-panel {
  padding: 16px;
  display: flex;
  flex-direction: column;
}

.alarm-panel h2 {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 600;
}

.empty-hint {
  margin: 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.alarm-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 12px;
  flex: 1;
}

.alarm-item {
  display: grid;
  grid-template-columns: 28px 1fr auto;
  gap: 10px;
  align-items: start;
  padding-bottom: 12px;
  border-bottom: 1px solid var(--border);
}

.alarm-item:last-child {
  border-bottom: none;
  padding-bottom: 0;
}

.alarm-severity {
  width: 24px;
  height: 24px;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 700;
}

.alarm-severity.warn,
.alarm-severity.critical {
  background: rgba(245, 185, 66, 0.2);
  color: var(--accent-amber);
}

.alarm-severity.info {
  background: rgba(77, 163, 255, 0.15);
  color: var(--accent-blue);
}

.alarm-body p {
  margin: 0;
  font-size: 13px;
  font-weight: 600;
}

.alarm-body span {
  font-size: 11px;
  color: var(--text-secondary);
}

.alarm-item time {
  font-size: 11px;
  color: var(--text-secondary);
  white-space: nowrap;
}

.charts-row {
  display: grid;
  grid-template-columns: 1fr 1fr 320px;
  gap: 16px;
}

.chart-card {
  padding: 14px 14px 8px;
}

.chart-card h2 {
  margin: 0 0 8px;
  font-size: 14px;
  font-weight: 600;
}

.chart-box {
  height: 220px;
}

.bottom-row {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 16px;
}

.device-panel,
.kpi-panel {
  padding: 16px;
}

.device-panel h2,
.kpi-panel h2 {
  margin: 0 0 12px;
  font-size: 15px;
  font-weight: 600;
}

.table-wrap {
  overflow-x: auto;
}

.device-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.device-table th,
.device-table td {
  text-align: left;
  padding: 10px 8px;
  border-bottom: 1px solid var(--border);
  color: var(--text-secondary);
}

.device-table th {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 12px;
}

.device-table tbody td:first-child {
  color: var(--text-primary);
  font-weight: 500;
}

.tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
}

.tag--online {
  background: rgba(61, 220, 132, 0.15);
  color: var(--accent-green);
}

.tag--offline {
  background: rgba(139, 155, 181, 0.15);
  color: var(--text-secondary);
}

.mono {
  font-family: ui-monospace, monospace;
  font-size: 12px;
}

.kpi-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 16px;
  margin-top: 8px;
}

.kpi-item {
  padding: 20px 16px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  border: 1px solid var(--border);
  text-align: center;
}

.kpi-item strong {
  display: block;
  font-size: 28px;
  font-weight: 700;
  color: var(--accent-green);
  margin-bottom: 6px;
}

.kpi-item span {
  font-size: 13px;
  color: var(--text-secondary);
}

.pagination {
  margin-top: 12px;
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--text-secondary);
}

.btn-secondary {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 6px 12px;
  background: rgba(255, 255, 255, 0.05);
  color: var(--text-primary);
  cursor: pointer;
}

.btn-secondary:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

@media (max-width: 1400px) {
  .sensor-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .charts-row {
    grid-template-columns: 1fr;
  }

  .sensor-section {
    grid-template-columns: 1fr;
  }
}
</style>

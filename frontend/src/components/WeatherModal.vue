<script setup>
import { computed, ref, watch } from "vue";

const STORAGE_KEY = "weather_city_id";/**本地存储的键名，用于保存用户选择的城市 ID，实现持久化记忆。*/


const CITIES = [
  { id: "beijing", name: "北京", lat: 39.9042, lon: 116.4074 },
  { id: "shanghai", name: "上海", lat: 31.2304, lon: 121.4737 },
  { id: "tianjin", name: "天津", lat: 39.3434, lon: 117.3616 },
  { id: "chongqing", name: "重庆", lat: 29.563, lon: 106.5516 },
  { id: "shijiazhuang", name: "石家庄", lat: 38.0428, lon: 114.5149 },
  { id: "taiyuan", name: "太原", lat: 37.8706, lon: 112.5489 },
  { id: "shenyang", name: "沈阳", lat: 41.8057, lon: 123.4315 },
  { id: "changchun", name: "长春", lat: 43.8171, lon: 125.3235 },
  { id: "harbin", name: "哈尔滨", lat: 45.8038, lon: 126.535 },
  { id: "nanjing", name: "南京", lat: 32.0603, lon: 118.7969 },
  { id: "hangzhou", name: "杭州", lat: 30.2741, lon: 120.1551 },
  { id: "hefei", name: "合肥", lat: 31.8206, lon: 117.2272 },
  { id: "fuzhou", name: "福州", lat: 26.0745, lon: 119.2965 },
  { id: "nanchang", name: "南昌", lat: 28.682, lon: 115.8579 },
  { id: "jinan", name: "济南", lat: 36.6512, lon: 117.1201 },
  { id: "zhengzhou", name: "郑州", lat: 34.7466, lon: 113.6254 },
  { id: "wuhan", name: "武汉", lat: 30.5928, lon: 114.3055 },
  { id: "changsha", name: "长沙", lat: 28.2282, lon: 112.9388 },
  { id: "guangzhou", name: "广州", lat: 23.1291, lon: 113.2644 },
  { id: "shenzhen", name: "深圳", lat: 22.5431, lon: 114.0579 },
  { id: "haikou", name: "海口", lat: 20.044, lon: 110.1999 },
  { id: "chengdu", name: "成都", lat: 30.5728, lon: 104.0668 },
  { id: "guiyang", name: "贵阳", lat: 26.647, lon: 106.6302 },
  { id: "kunming", name: "昆明", lat: 25.0406, lon: 102.7123 },
  { id: "xian", name: "西安", lat: 34.3416, lon: 108.9398 },
  { id: "lanzhou", name: "兰州", lat: 36.0611, lon: 103.8343 },
  { id: "xining", name: "西宁", lat: 36.6171, lon: 101.7782 },
  { id: "hohhot", name: "呼和浩特", lat: 40.8414, lon: 111.7519 },
  { id: "nanning", name: "南宁", lat: 22.817, lon: 108.3665 },
  { id: "lhasa", name: "拉萨", lat: 29.652, lon: 91.1721 },
  { id: "yinchuan", name: "银川", lat: 38.4872, lon: 106.2309 },
  { id: "urumqi", name: "乌鲁木齐", lat: 43.8256, lon: 87.6168 },
];

const WEEKDAYS = ["周日", "周一", "周二", "周三", "周四", "周五", "周六"];

const props = defineProps({
  visible: { type: Boolean, default: false },
  cityId: { type: String, default: "beijing" },
});

const emit = defineEmits(["update:visible", "update:cityId", "summary"]);

const loading = ref(false);
const error = ref("");
const daily = ref([]);
const cityName = ref("北京");

/** 将 WMO（世界气象组织）标准天气码转换为中文描述和对应的 emoji 图标。 */
function wmoLabel(code) {
  const c = Number(code);
  if (c === 0) return { text: "晴", icon: "☀" };
  if (c === 1) return { text: "晴间多云", icon: "🌤" };
  if (c === 2) return { text: "多云", icon: "⛅" };
  if (c === 3) return { text: "阴", icon: "🌥" };
  if (c === 45 || c === 48) return { text: "雾", icon: "🌫" };
  if (c === 51 || c === 53 || c === 55) return { text: "毛毛雨", icon: "🌦" };
  if (c === 56 || c === 57) return { text: "冻毛毛雨", icon: "🌧" };
  if (c === 61) return { text: "小雨", icon: "🌧" };
  if (c === 63) return { text: "中雨", icon: "🌧" };
  if (c === 65) return { text: "大雨", icon: "🌧" };
  if (c === 66 || c === 67) return { text: "冻雨", icon: "🌧" };
  if (c === 71) return { text: "小雪", icon: "❄" };
  if (c === 73) return { text: "中雪", icon: "❄" };
  if (c === 75) return { text: "大雪", icon: "❄" };
  if (c === 77) return { text: "雪粒", icon: "❄" };
  if (c === 80 || c === 81 || c === 82) return { text: "阵雨", icon: "🌦" };
  if (c === 85 || c === 86) return { text: "阵雪", icon: "❄" };
  if (c === 95) return { text: "雷雨", icon: "⛈" };
  if (c === 96 || c === 99) return { text: "冰雹", icon: "🌨" };
  return { text: "多云", icon: "☁" };
}
/* 从 ISO 8601 格式的时间字符串（如 2024-01-01T06:30:00）中提取时分（如 06:30）。 */
function clipTime(iso) {
  if (!iso) return "—";
  const part = String(iso).split("T")[1];
  return part ? part.slice(0, 5) : "—";
}
/** 格式化日期字符串为 "MM-DD 星期X" 格式。 */
function formatDayLabel(dateStr) {
  const d = new Date(`${dateStr}T12:00:00`);
  const md = dateStr.slice(5);
  return `${md} ${WEEKDAYS[d.getDay()]}`;
}

async function fetchForecast(cityId) {
  const city = CITIES.find((c) => c.id === cityId) || CITIES[0];
  cityName.value = city.name;

  const params = new URLSearchParams({
    latitude: city.lat,
    longitude: city.lon,
    current: "temperature_2m,weather_code",
    daily: "weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset",
    timezone: "Asia/Shanghai",
    forecast_days: "7",
  });

  const res = await fetch(`https://api.open-meteo.com/v1/forecast?${params}`);
  if (!res.ok) throw new Error("天气服务暂不可用");
  const data = await res.json();

  const cur = data.current || {};
  const label = wmoLabel(cur.weather_code);
  const temp = cur.temperature_2m;

  const d = data.daily || {};
  const rows = (d.time || []).map((date, i) => {
    const cond = wmoLabel(d.weather_code?.[i]);
    return {
      date,
      label: formatDayLabel(date),
      text: cond.text,
      icon: cond.icon,
      temp_min: d.temperature_2m_min?.[i],
      temp_max: d.temperature_2m_max?.[i],
      sunrise: clipTime(d.sunrise?.[i]),
      sunset: clipTime(d.sunset?.[i]),
    };
  });

  daily.value = rows;
  emit("summary", {
    city: city.name,
    text: label.text,
    icon: label.icon,
    temperature: temp != null ? Math.round(temp * 10) / 10 : null,
  });
}

async function load(cityId) {
  loading.value = true;
  error.value = "";
  try {
    await fetchForecast(cityId);
  } catch (e) {
    error.value = e?.message || "加载失败";
    daily.value = [];
  } finally {
    loading.value = false;
  }
}

const localCityId = computed({
  get: () => props.cityId,
  set: (id) => {
    localStorage.setItem(STORAGE_KEY, id);
    emit("update:cityId", id);
  },
});

watch(
  () => props.cityId,
  (id) => {
    if (id) load(id);
  },
  { immediate: true }
);

function close() {
  emit("update:visible", false);
}

function onCityChange(ev) {
  localCityId.value = ev.target.value;
}
</script>

<template>
  <Teleport to="body">
    <div v-if="visible" class="weather-overlay" @click.self="close">
      <div class="weather-dialog dash-card" role="dialog" aria-label="天气预报">
        <header class="weather-dialog__head">
          <h2>{{ cityName }} · 近 7 日</h2>
          <button type="button" class="weather-dialog__close" aria-label="关闭" @click="close">
            ×
          </button>
        </header>

        <div class="weather-dialog__toolbar">
          <label>
            城市
            <select :value="localCityId" @change="onCityChange">
              <option v-for="c in CITIES" :key="c.id" :value="c.id">{{ c.name }}</option>
            </select>
          </label>
        </div>

        <p v-if="loading" class="weather-hint">加载中…</p>
        <p v-else-if="error" class="weather-hint weather-hint--error">{{ error }}</p>

        <table v-else class="weather-table">
          <thead>
            <tr>
              <th>日期</th>
              <th>天气</th>
              <th>最低</th>
              <th>最高</th>
              <th>日出</th>
              <th>日落</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="row in daily" :key="row.date">
              <td>{{ row.label }}</td>
              <td>
                <span class="weather-cell">
                  <span class="weather-cell__icon" aria-hidden="true">{{ row.icon }}</span>
                  <span>{{ row.text }}</span>
                </span>
              </td>
              <td>{{ row.temp_min != null ? `${row.temp_min}°C` : "—" }}</td>
              <td>{{ row.temp_max != null ? `${row.temp_max}°C` : "—" }}</td>
              <td>{{ row.sunrise }}</td>
              <td>{{ row.sunset }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </Teleport>
</template>

<style scoped>
.weather-overlay {
  position: fixed;
  inset: 0;
  z-index: 1000;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  background: rgba(4, 10, 22, 0.72);
}

.weather-dialog {
  width: min(600px, 100%);
  padding: 20px 22px 22px;
  border-radius: 12px;
  border: 1px solid var(--border);
  box-shadow: var(--shadow);
}

.weather-dialog__head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 14px;
}

.weather-dialog__head h2 {
  margin: 0;
  font-size: 17px;
  font-weight: 600;
}

.weather-dialog__close {
  width: 32px;
  height: 32px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: transparent;
  color: var(--text-secondary);
  font-size: 20px;
  line-height: 1;
  cursor: pointer;
}

.weather-dialog__toolbar label {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 13px;
  color: var(--text-secondary);
}

.weather-dialog__toolbar select {
  flex: 1;
  min-width: 140px;
  padding: 8px 10px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: var(--bg-app);
  color: var(--text-primary);
  font-size: 13px;
}

.weather-hint {
  margin: 16px 0 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.weather-hint--error {
  color: var(--accent-red);
}

.weather-table {
  width: 100%;
  margin-top: 14px;
  border-collapse: collapse;
  font-size: 13px;
}

.weather-table th,
.weather-table td {
  padding: 10px 8px;
  text-align: left;
  border-bottom: 1px solid var(--border);
}

.weather-table th {
  color: var(--text-secondary);
  font-weight: 500;
}

.weather-table td {
  color: var(--text-primary);
}

.weather-cell {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
}

.weather-cell__icon {
  font-size: 18px;
  line-height: 1;
}
</style>

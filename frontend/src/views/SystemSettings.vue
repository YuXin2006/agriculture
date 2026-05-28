<script setup>
import { computed, onMounted, onUnmounted, ref } from "vue";
import { useRouter } from "vue-router";
import { getSystemStatus } from "../api/dashboard";

const router = useRouter();
const loading = ref(false);
const status = ref(null);
const notice = ref({ show: false, type: "error", text: "" });
let noticeTimer = null;
let refreshTimer = null;

const summary = computed(() => status.value?.summary || {});
const services = computed(() => status.value?.services || {});
const mqtt = computed(() => services.value?.mqtt || {});
const dataFreshness = computed(() => status.value?.data_freshness || {});
const mqttCache = computed(() => status.value?.mqtt_cache || {});
const dbStats = computed(() => status.value?.database_stats || {});

const onlineRate = computed(() => {
  const total = Number(summary.value.total_devices || 0);
  const online = Number(summary.value.online_devices || 0);
  if (!total) return 0;
  return Math.round((online / total) * 100);
});

const showNotice = (type, text) => {
  notice.value = { show: true, type, text };
  if (noticeTimer) clearTimeout(noticeTimer);
  noticeTimer = setTimeout(() => {
    notice.value.show = false;
  }, 2200);
};

const loadStatus = async () => {
  loading.value = true;
  try {
    status.value = await getSystemStatus();
  } catch (error) {
    showNotice("error", `加载失败: ${error}`);
    status.value = null;
  } finally {
    loading.value = false;
  }
};

const serviceStatusClass = (item) => {
  const s = item?.status;
  if (s === "ok" || s === "running") return "ok";
  if (s === "disabled" || s === "unconfigured" || s === "idle" || s === "cache_only") return "warn";
  return "error";
};

const serviceStatusLabel = (item) => {
  const map = {
    ok: "正常",
    running: "运行中",
    disabled: "未启用",
    unconfigured: "未配置",
    idle: "待机",
    cache_only: "仅缓存",
    error: "异常",
  };
  return map[item?.status] || item?.status || "-";
};

const mqttStatusClass = computed(() => serviceStatusClass(mqtt.value));
const mqttStatusLabel = computed(() => serviceStatusLabel(mqtt.value));

const formatTime = (value) => value || "暂无数据";

const pickLatest = (channel) => {
  const cacheAt = channel?.cache_at;
  const dbAt = channel?.database?.at;
  if (cacheAt && dbAt) return cacheAt >= dbAt ? { source: "MQTT 缓存", at: cacheAt, node_id: channel.cache_node_id } : { source: "数据库", at: dbAt, node_id: channel.database?.node_id };
  if (cacheAt) return { source: "MQTT 缓存", at: cacheAt, node_id: channel.cache_node_id };
  if (dbAt) return { source: "数据库", at: dbAt, node_id: channel.database?.node_id };
  return { source: "-", at: null, node_id: null };
};

const envLatest = computed(() => pickLatest(dataFreshness.value.env));
const soilLatest = computed(() => pickLatest(dataFreshness.value.soil));
const sensorLatest = computed(() => pickLatest(dataFreshness.value.sensor));

const quickLinks = [
  { label: "数据总览", path: "/overview", desc: "查看基地指标与图表" },
  { label: "设备管理", path: "/device-manage", desc: "维护监测节点" },
  { label: "告警记录", path: "/alarm-center", desc: "处理未关闭告警" },
  { label: "问问 AI", path: "/chat", desc: "智能分析监测数据" },
];

const goTo = (path) => router.push(path);

onMounted(() => {
  loadStatus();
  refreshTimer = setInterval(loadStatus, 30000);
});

onUnmounted(() => {
  if (refreshTimer) clearInterval(refreshTimer);
  if (noticeTimer) clearTimeout(noticeTimer);
});
</script>

<template>
  <div class="ops-page">
    <transition name="toast">
      <div v-if="notice.show" class="notice" :class="notice.type">{{ notice.text }}</div>
    </transition>

    <header class="page-header">
      <div>
        <h1>运维管理中心</h1>
        <p class="subtitle">
          系统服务与数据采集运行状态
          <span v-if="status?.generated_at"> · 更新于 {{ status.generated_at }}</span>
        </p>
      </div>
      <button type="button" class="btn-ghost" :disabled="loading" @click="loadStatus">
        {{ loading ? "刷新中..." : "刷新状态" }}
      </button>
    </header>

    <section class="stat-row">
      <article class="stat-card dash-card">
        <span class="stat-label">在线设备</span>
        <strong>
          {{ summary.online_devices ?? "-" }}
          <small>/ {{ summary.total_devices ?? 0 }}</small>
        </strong>
        <p class="stat-foot">在线率 {{ onlineRate }}%</p>
      </article>
      <article class="stat-card dash-card">
        <span class="stat-label">未处理告警</span>
        <strong class="text-amber">{{ summary.active_alarms ?? "-" }}</strong>
        <p class="stat-foot">需人工跟进</p>
      </article>
      <article class="stat-card dash-card">
        <span class="stat-label">MQTT 服务</span>
        <strong :class="mqttStatusClass === 'ok' ? 'text-green' : mqttStatusClass === 'error' ? 'text-red' : 'text-amber'">
          {{ mqttStatusLabel }}
        </strong>
        <p class="stat-foot">{{ mqtt.detail || "-" }}</p>
      </article>
      <article class="stat-card dash-card">
        <span class="stat-label">采集频率</span>
        <strong>{{ summary.sampling_interval || "-" }}</strong>
        <p class="stat-foot">总览页展示间隔</p>
      </article>
    </section>

    <p v-if="loading && !status" class="loading-text">正在加载系统状态...</p>

    <template v-else-if="status">
      <div class="panel-grid">
        <section class="dash-card panel">
          <h2>服务状态</h2>
          <ul class="service-list">
            <li>
              <div class="service-head">
                <span class="service-name">Django API</span>
                <span class="tag" :class="`tag--${serviceStatusClass(services.api)}`">
                  {{ serviceStatusLabel(services.api) }}
                </span>
              </div>
              <p>{{ services.api?.detail }}</p>
            </li>
            <li>
              <div class="service-head">
                <span class="service-name">数据库</span>
                <span class="tag" :class="`tag--${serviceStatusClass(services.database)}`">
                  {{ serviceStatusLabel(services.database) }}
                </span>
              </div>
              <p>{{ services.database?.detail }}</p>
            </li>
            <li>
              <div class="service-head">
                <span class="service-name">MQTT 订阅</span>
                <span class="tag" :class="`tag--${mqttStatusClass}`">{{ mqttStatusLabel }}</span>
              </div>
              <p>{{ mqtt.detail }}</p>
              <dl class="kv-list">
                <div><dt>Broker</dt><dd>{{ mqtt.broker_host }}:{{ mqtt.broker_port }}</dd></div>
                <div><dt>认证</dt><dd>{{ mqtt.auth_configured ? "已配置" : "未配置" }}</dd></div>
                <div><dt>依赖</dt><dd>{{ mqtt.paho_installed ? "paho-mqtt 已安装" : "缺少 paho-mqtt" }}</dd></div>
                <div><dt>线程</dt><dd>{{ mqtt.thread_alive ? "运行中" : "未运行" }}</dd></div>
              </dl>
            </li>
            <li>
              <div class="service-head">
                <span class="service-name">大模型 (AI)</span>
                <span class="tag" :class="`tag--${serviceStatusClass(services.llm)}`">
                  {{ serviceStatusLabel(services.llm) }}
                </span>
              </div>
              <p>{{ services.llm?.detail }}</p>
              <dl v-if="services.llm?.model" class="kv-list">
                <div><dt>模型</dt><dd>{{ services.llm.model }}</dd></div>
                <div><dt>API Base</dt><dd>{{ services.llm.api_base_set ? "已设置" : "默认" }}</dd></div>
              </dl>
            </li>
          </ul>
        </section>

        <section class="dash-card panel">
          <h2>数据采集</h2>
          <table class="fresh-table">
            <thead>
              <tr>
                <th>通道</th>
                <th>最近来源</th>
                <th>最近时间</th>
                <th>节点</th>
              </tr>
            </thead>
            <tbody>
              <tr>
                <td>环境 (env)</td>
                <td>{{ envLatest.source }}</td>
                <td>{{ formatTime(envLatest.at) }}</td>
                <td class="mono">{{ envLatest.node_id || "-" }}</td>
              </tr>
              <tr>
                <td>土壤 (soil)</td>
                <td>{{ soilLatest.source }}</td>
                <td>{{ formatTime(soilLatest.at) }}</td>
                <td class="mono">{{ soilLatest.node_id || "-" }}</td>
              </tr>
              <tr>
                <td>传感器 (sensor)</td>
                <td>{{ sensorLatest.source }}</td>
                <td>{{ formatTime(sensorLatest.at) }}</td>
                <td class="mono">-</td>
              </tr>
            </tbody>
          </table>

          <h3 class="sub-title">MQTT 缓存概况</h3>
          <div class="cache-grid">
            <div class="cache-item">
              <span>环境缓存</span>
              <strong :class="mqttCache.env ? 'text-green' : ''">{{ mqttCache.env ? "有" : "无" }}</strong>
            </div>
            <div class="cache-item">
              <span>土壤缓存</span>
              <strong :class="mqttCache.soil ? 'text-green' : ''">{{ mqttCache.soil ? "有" : "无" }}</strong>
            </div>
            <div class="cache-item">
              <span>传感器缓存</span>
              <strong :class="mqttCache.sensor ? 'text-green' : ''">{{ mqttCache.sensor ? "有" : "无" }}</strong>
            </div>
            <div class="cache-item">
              <span>设备条目</span>
              <strong>{{ mqttCache.device_count ?? 0 }}</strong>
            </div>
            <div class="cache-item">
              <span>告警缓存</span>
              <strong>{{ mqttCache.alarm_count ?? 0 }}</strong>
            </div>
            <div class="cache-item">
              <span>24h 历史点</span>
              <strong>{{ (mqttCache.env_history_size || 0) + (mqttCache.soil_history_size || 0) }}</strong>
            </div>
          </div>
        </section>
      </div>

      <div class="panel-grid">
        <section class="dash-card panel">
          <h2>订阅主题</h2>
          <ul v-if="mqtt.topics?.length" class="topic-list">
            <li v-for="topic in mqtt.topics" :key="topic">{{ topic }}</li>
          </ul>
          <p v-else class="muted">未配置 MQTT_TOPICS</p>
        </section>

        <section class="dash-card panel">
          <h2>数据库统计</h2>
          <dl class="stats-grid">
            <div><dt>监测节点</dt><dd>{{ dbStats.device_nodes ?? 0 }}</dd></div>
            <div><dt>环境记录</dt><dd>{{ dbStats.env_records ?? 0 }}</dd></div>
            <div><dt>土壤记录</dt><dd>{{ dbStats.soil_records ?? 0 }}</dd></div>
            <div><dt>传感器记录</dt><dd>{{ dbStats.sensor_records ?? 0 }}</dd></div>
            <div><dt>告警总数</dt><dd>{{ dbStats.alarm_records ?? 0 }}</dd></div>
            <div><dt>未处理告警</dt><dd>{{ dbStats.active_alarm_records ?? 0 }}</dd></div>
            <div><dt>AI 会话</dt><dd>{{ dbStats.chat_sessions ?? 0 }}</dd></div>
          </dl>
        </section>
      </div>

      <section class="dash-card panel">
        <h2>快捷入口</h2>
        <div class="link-grid">
          <button
            v-for="link in quickLinks"
            :key="link.path"
            type="button"
            class="link-card"
            @click="goTo(link.path)"
          >
            <strong>{{ link.label }}</strong>
            <span>{{ link.desc }}</span>
          </button>
        </div>
      </section>
    </template>
  </div>
</template>

<style scoped>
.ops-page {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 20px 24px 28px;
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
  color: var(--text-primary);
}

.subtitle {
  margin: 6px 0 0;
  font-size: 13px;
  color: var(--text-secondary);
}

.stat-row {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.stat-card {
  padding: 16px 18px;
}

.stat-label {
  display: block;
  font-size: 13px;
  color: var(--text-secondary);
  margin-bottom: 8px;
}

.stat-card strong {
  font-size: 26px;
  font-weight: 700;
  color: var(--text-primary);
}

.stat-card strong small {
  font-size: 16px;
  font-weight: 500;
  color: var(--text-secondary);
}

.stat-foot {
  margin: 8px 0 0;
  font-size: 12px;
  color: var(--text-secondary);
}

.text-green {
  color: var(--accent-green);
}

.text-amber {
  color: var(--accent-amber);
}

.text-red {
  color: var(--accent-red);
}

.loading-text {
  color: var(--text-secondary);
  font-size: 14px;
}

.panel-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
}

.panel {
  padding: 18px;
}

.panel h2 {
  margin: 0 0 14px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.sub-title {
  margin: 18px 0 10px;
  font-size: 13px;
  font-weight: 600;
  color: var(--text-secondary);
}

.service-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.service-list li {
  padding-bottom: 16px;
  border-bottom: 1px solid var(--border);
}

.service-list li:last-child {
  padding-bottom: 0;
  border-bottom: none;
}

.service-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 6px;
}

.service-name {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-primary);
}

.service-list p {
  margin: 0 0 8px;
  font-size: 13px;
  color: var(--text-secondary);
  line-height: 1.5;
}

.kv-list {
  margin: 0;
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px 12px;
}

.kv-list div {
  display: flex;
  gap: 8px;
  font-size: 12px;
}

.kv-list dt {
  color: var(--text-secondary);
  min-width: 48px;
}

.kv-list dd {
  margin: 0;
  color: var(--text-primary);
  font-family: ui-monospace, monospace;
}

.tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  white-space: nowrap;
}

.tag--ok,
.tag--running {
  background: rgba(61, 220, 132, 0.15);
  color: var(--accent-green);
}

.tag--warn,
.tag--disabled,
.tag--unconfigured,
.tag--idle,
.tag--cache_only {
  background: rgba(245, 185, 66, 0.15);
  color: var(--accent-amber);
}

.tag--error {
  background: rgba(255, 107, 107, 0.15);
  color: var(--accent-red);
}

.fresh-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.fresh-table th,
.fresh-table td {
  text-align: left;
  padding: 10px 8px;
  border-bottom: 1px solid var(--border);
  color: var(--text-secondary);
}

.fresh-table th {
  color: var(--text-primary);
  font-size: 12px;
  font-weight: 600;
}

.mono {
  font-family: ui-monospace, monospace;
  font-size: 12px;
}

.cache-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 10px;
}

.cache-item {
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.2);
}

.cache-item span {
  display: block;
  font-size: 12px;
  color: var(--text-secondary);
  margin-bottom: 4px;
}

.cache-item strong {
  font-size: 18px;
  color: var(--text-primary);
}

.topic-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.topic-list li {
  padding: 8px 12px;
  border-radius: 8px;
  background: rgba(0, 0, 0, 0.25);
  border: 1px solid var(--border);
  font-family: ui-monospace, monospace;
  font-size: 13px;
  color: var(--accent-green);
}

.stats-grid {
  margin: 0;
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 12px;
}

.stats-grid div {
  display: flex;
  justify-content: space-between;
  padding: 10px 12px;
  border-radius: 8px;
  border: 1px solid var(--border);
  background: rgba(0, 0, 0, 0.2);
}

.stats-grid dt {
  font-size: 13px;
  color: var(--text-secondary);
}

.stats-grid dd {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.muted {
  font-size: 13px;
  color: var(--text-secondary);
}

.link-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
}

.link-card {
  text-align: left;
  padding: 14px 16px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.03);
  cursor: pointer;
  transition: border-color 0.15s, background 0.15s;
}

.link-card:hover {
  border-color: rgba(61, 220, 132, 0.4);
  background: rgba(61, 220, 132, 0.06);
}

.link-card strong {
  display: block;
  font-size: 14px;
  color: var(--text-primary);
  margin-bottom: 4px;
}

.link-card span {
  font-size: 12px;
  color: var(--text-secondary);
}

.btn-ghost {
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 9px 14px;
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
  font-size: 14px;
  cursor: pointer;
}

.btn-ghost:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.notice {
  position: fixed;
  top: 18px;
  left: 50%;
  transform: translateX(-50%);
  z-index: 9999;
  min-width: 220px;
  max-width: 420px;
  padding: 12px 16px;
  border-radius: 10px;
  font-size: 14px;
  text-align: center;
  box-shadow: var(--shadow);
}

.notice.error {
  background: rgba(255, 107, 107, 0.12);
  color: var(--accent-red);
  border: 1px solid rgba(255, 107, 107, 0.35);
}

.toast-enter-active,
.toast-leave-active {
  transition: all 0.25s ease;
}

.toast-enter-from,
.toast-leave-to {
  opacity: 0;
  transform: translate(-50%, -10px);
}

@media (max-width: 1100px) {
  .stat-row {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .panel-grid {
    grid-template-columns: 1fr;
  }

  .link-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}

@media (max-width: 640px) {
  .stat-row,
  .link-grid,
  .cache-grid {
    grid-template-columns: 1fr;
  }
}
</style>

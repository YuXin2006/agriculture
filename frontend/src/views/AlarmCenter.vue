<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import {
  createAlarm,
  deleteAlarm,
  getAlarmList,
  getDeviceList,
  updateAlarm,
} from "../api/dashboard";

const loading = ref(false);
const saving = ref(false);
const alarms = ref([]);
const deviceOptions = ref([]);
const editingId = ref(null);
const page = ref(1);
const pageSize = 10;
const totalPages = ref(0);
const total = ref(0);
const jumpPage = ref("");
const notice = ref({ show: false, type: "success", text: "" });
let noticeTimer = null;

const form = reactive({
  node: "",
  level: "warn",
  title: "",
  message: "",
  detail: "",
  metric_value: "",
  threshold: "",
  status: "active",
});

const activeCount = computed(
  () => alarms.value.filter((a) => a.status === "active").length
);

const criticalCount = computed(
  () => alarms.value.filter((a) => a.level === "critical").length
);

const showNotice = (type, text) => {
  notice.value = { show: true, type, text };
  if (noticeTimer) clearTimeout(noticeTimer);
  noticeTimer = setTimeout(() => {
    notice.value.show = false;
  }, 2200);
};

const resetForm = () => {
  form.node = "";
  form.level = "warn";
  form.title = "";
  form.message = "";
  form.detail = "";
  form.metric_value = "";
  form.threshold = "";
  form.status = "active";
  editingId.value = null;
};

const loadDevices = async () => {
  try {
    const data = await getDeviceList({ page: 1, page_size: 200 });
    deviceOptions.value = Array.isArray(data?.results) ? data.results : [];
  } catch {
    deviceOptions.value = [];
  }
};

const loadList = async () => {
  loading.value = true;
  try {
    const data = await getAlarmList({ page: page.value, page_size: pageSize });
    alarms.value = Array.isArray(data?.results) ? data.results : [];
    total.value = Number(data?.pagination?.total || 0);
    totalPages.value = Number(data?.pagination?.total_pages || 0);
    if (totalPages.value > 0 && page.value > totalPages.value) {
      page.value = totalPages.value;
      await loadList();
    }
  } catch (error) {
    showNotice("error", `加载失败: ${error}`);
    alarms.value = [];
  } finally {
    loading.value = false;
  }
};

const toPayload = () => ({
  node: form.node === "" ? null : Number(form.node),
  level: form.level,
  title: form.title.trim(),
  message: form.message.trim(),
  detail: form.detail.trim(),
  metric_value: form.metric_value === "" ? null : Number(form.metric_value),
  threshold: form.threshold === "" ? null : Number(form.threshold),
  status: form.status,
});

const submitForm = async () => {
  if (!form.title.trim()) {
    showNotice("error", "请填写告警标题");
    return;
  }

  saving.value = true;
  try {
    const payload = toPayload();
    if (editingId.value) {
      await updateAlarm(editingId.value, payload);
      showNotice("success", "告警修改成功");
    } else {
      await createAlarm(payload);
      showNotice("success", "告警新增成功");
    }
    resetForm();
    await loadList();
  } catch (error) {
    showNotice("error", `提交失败: ${error}`);
  } finally {
    saving.value = false;
  }
};

const startEdit = (item) => {
  editingId.value = item.id;
  form.node = item.node ?? "";
  form.level = item.level || "warn";
  form.title = item.title || "";
  form.message = item.message || "";
  form.detail = item.detail || "";
  form.metric_value = item.metric_value ?? "";
  form.threshold = item.threshold ?? "";
  form.status = item.status || "active";
};

const resolveItem = async (item) => {
  if (item.status === "resolved") return;
  try {
    await updateAlarm(item.id, {
      node: item.node,
      level: item.level,
      title: item.title,
      message: item.message || "",
      detail: item.detail || "",
      metric_value: item.metric_value,
      threshold: item.threshold,
      status: "resolved",
    });
    showNotice("success", "已标记为已处理");
    await loadList();
  } catch (error) {
    showNotice("error", `处理失败: ${error}`);
  }
};

const removeItem = async (id) => {
  if (!window.confirm("确定删除该告警记录吗？")) return;
  try {
    await deleteAlarm(id);
    showNotice("success", "删除成功");
    if (alarms.value.length === 1 && page.value > 1) page.value -= 1;
    await loadList();
  } catch (error) {
    showNotice("error", `删除失败: ${error}`);
  }
};

const prevPage = async () => {
  if (page.value <= 1 || loading.value) return;
  page.value -= 1;
  await loadList();
};

const nextPage = async () => {
  if (page.value >= totalPages.value || loading.value) return;
  page.value += 1;
  await loadList();
};

const goToPage = async () => {
  if (loading.value || totalPages.value === 0) return;
  const target = Number(jumpPage.value);
  if (!Number.isInteger(target) || target < 1 || target > totalPages.value) {
    showNotice("error", `页码范围为 1 到 ${totalPages.value}`);
    return;
  }
  page.value = target;
  await loadList();
};

const formatTime = (value) => {
  if (!value) return "-";
  return String(value).replace("T", " ").slice(0, 19);
};

const levelLabel = (level) => {
  const map = { info: "提示", warn: "警告", critical: "严重" };
  return map[level] || level;
};

const statusLabel = (status) => (status === "resolved" ? "已处理" : "未处理");

const formatMetric = (value, threshold) => {
  const parts = [];
  if (value != null) parts.push(`当前 ${value}`);
  if (threshold != null) parts.push(`阈值 ${threshold}`);
  return parts.length ? parts.join(" · ") : "-";
};

onMounted(async () => {
  await Promise.all([loadDevices(), loadList()]);
});
</script>

<template>
  <div class="alarm-page">
    <transition name="toast">
      <div v-if="notice.show" class="notice" :class="notice.type">{{ notice.text }}</div>
    </transition>

    <header class="page-header">
      <div>
        <h1>告警记录</h1>
        <p class="subtitle">监测告警的查看、登记与处理状态维护</p>
      </div>
      <button type="button" class="btn-ghost" :disabled="loading" @click="loadList">刷新列表</button>
    </header>

    <section class="stat-row">
      <article class="stat-card dash-card">
        <span class="stat-label">告警总数</span>
        <strong>{{ total }}</strong>
      </article>
      <article class="stat-card dash-card">
        <span class="stat-label">当前页未处理</span>
        <strong class="text-amber">{{ activeCount }}</strong>
      </article>
      <article class="stat-card dash-card">
        <span class="stat-label">当前页严重</span>
        <strong class="text-red">{{ criticalCount }}</strong>
      </article>
    </section>

    <section class="dash-card form-panel">
      <h2>{{ editingId ? "编辑告警" : "登记告警" }}</h2>
      <div class="form-grid">
        <label>
          <span>关联节点</span>
          <select v-model="form.node">
            <option value="">不关联节点</option>
            <option v-for="d in deviceOptions" :key="d.id" :value="d.id">
              {{ d.node_id }} · {{ d.name }}
            </option>
          </select>
        </label>
        <label>
          <span>告警级别</span>
          <select v-model="form.level">
            <option value="info">提示</option>
            <option value="warn">警告</option>
            <option value="critical">严重</option>
          </select>
        </label>
        <label>
          <span>处理状态</span>
          <select v-model="form.status">
            <option value="active">未处理</option>
            <option value="resolved">已处理</option>
          </select>
        </label>
        <label class="span-2">
          <span>告警标题 *</span>
          <input v-model="form.title" type="text" placeholder="如 土壤湿度过低" />
        </label>
        <label class="span-2">
          <span>告警描述</span>
          <textarea v-model="form.message" rows="2" placeholder="详细说明" />
        </label>
        <label class="span-2">
          <span>详情摘要</span>
          <input v-model="form.detail" type="text" placeholder="如 当前 41% · 阈值 45%" />
        </label>
        <label>
          <span>当前值</span>
          <input v-model="form.metric_value" type="number" step="0.01" placeholder="41" />
        </label>
        <label>
          <span>阈值</span>
          <input v-model="form.threshold" type="number" step="0.01" placeholder="45" />
        </label>
      </div>
      <div class="actions">
        <button type="button" class="btn-primary" :disabled="saving" @click="submitForm">
          {{ saving ? "提交中..." : editingId ? "保存修改" : "登记告警" }}
        </button>
        <button type="button" class="btn-ghost" @click="resetForm">清空</button>
      </div>
    </section>

    <section class="dash-card list-panel">
      <h2>告警列表</h2>
      <p v-if="loading" class="loading-text">加载中...</p>
      <div v-else class="table-wrap">
        <table class="alarm-table">
          <thead>
            <tr>
              <th>级别</th>
              <th>标题</th>
              <th>节点</th>
              <th>详情</th>
              <th>数值/阈值</th>
              <th>状态</th>
              <th>告警时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in alarms" :key="item.id">
              <td>
                <span class="tag" :class="`tag--${item.level}`">
                  {{ levelLabel(item.level) }}
                </span>
              </td>
              <td class="title-cell">
                <strong>{{ item.title }}</strong>
                <p v-if="item.message" class="msg-hint">{{ item.message }}</p>
              </td>
              <td class="mono">{{ item.node_id || "-" }}</td>
              <td>{{ item.detail || "-" }}</td>
              <td class="metric-cell">{{ formatMetric(item.metric_value, item.threshold) }}</td>
              <td>
                <span class="tag" :class="item.status === 'resolved' ? 'tag--resolved' : 'tag--active'">
                  {{ statusLabel(item.status) }}
                </span>
              </td>
              <td>{{ formatTime(item.created_at) }}</td>
              <td class="row-actions">
                <button
                  v-if="item.status === 'active'"
                  type="button"
                  class="btn-resolve btn-sm"
                  @click="resolveItem(item)"
                >
                  处理
                </button>
                <button type="button" class="btn-ghost btn-sm" @click="startEdit(item)">编辑</button>
                <button type="button" class="btn-danger btn-sm" @click="removeItem(item.id)">删除</button>
              </td>
            </tr>
            <tr v-if="alarms.length === 0">
              <td colspan="8" class="empty-cell">暂无告警记录</td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="pagination">
        <button type="button" class="btn-ghost" :disabled="page <= 1 || loading" @click="prevPage">
          上一页
        </button>
        <span>第 {{ page }} / {{ totalPages || 1 }} 页（共 {{ total }} 条）</span>
        <button
          type="button"
          class="btn-ghost"
          :disabled="loading || page >= totalPages || totalPages === 0"
          @click="nextPage"
        >
          下一页
        </button>
        <input
          v-model="jumpPage"
          class="jump-input"
          type="number"
          min="1"
          :max="totalPages || 1"
          placeholder="页码"
        />
        <button type="button" class="btn-ghost" :disabled="loading || totalPages === 0" @click="goToPage">
          跳转
        </button>
      </div>
    </section>
  </div>
</template>

<style scoped>
.alarm-page {
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
  grid-template-columns: repeat(3, minmax(0, 1fr));
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
  font-size: 28px;
  font-weight: 700;
  color: var(--text-primary);
}

.text-amber {
  color: var(--accent-amber);
}

.text-red {
  color: var(--accent-red);
}

.form-panel,
.list-panel {
  padding: 18px;
}

.form-panel h2,
.list-panel h2 {
  margin: 0 0 14px;
  font-size: 15px;
  font-weight: 600;
  color: var(--text-primary);
}

.form-grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
}

.form-grid .span-2 {
  grid-column: span 2;
}

label span {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

input,
select,
textarea {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 9px 11px;
  background: rgba(0, 0, 0, 0.25);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s;
  font-family: inherit;
  resize: vertical;
}

input:focus,
select:focus,
textarea:focus {
  border-color: rgba(61, 220, 132, 0.5);
}

select option {
  background: #121c30;
  color: var(--text-primary);
}

.actions {
  margin-top: 16px;
  display: flex;
  gap: 10px;
}

.btn-primary {
  border: none;
  border-radius: 8px;
  padding: 9px 18px;
  background: linear-gradient(135deg, #2ecc71, #1a9b52);
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
}

.btn-primary:disabled {
  opacity: 0.6;
  cursor: not-allowed;
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

.btn-sm {
  padding: 5px 10px;
  font-size: 12px;
}

.btn-resolve {
  border: 1px solid rgba(61, 220, 132, 0.35);
  border-radius: 8px;
  padding: 5px 10px;
  background: rgba(61, 220, 132, 0.12);
  color: var(--accent-green);
  font-size: 12px;
  cursor: pointer;
}

.btn-danger {
  border: 1px solid rgba(255, 107, 107, 0.35);
  border-radius: 8px;
  padding: 5px 10px;
  background: rgba(255, 107, 107, 0.12);
  color: var(--accent-red);
  font-size: 12px;
  cursor: pointer;
}

.loading-text {
  color: var(--text-secondary);
  font-size: 14px;
}

.table-wrap {
  overflow-x: auto;
}

.alarm-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.alarm-table th,
.alarm-table td {
  text-align: left;
  padding: 11px 10px;
  border-bottom: 1px solid var(--border);
  color: var(--text-secondary);
  vertical-align: top;
}

.alarm-table th {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 12px;
  white-space: nowrap;
}

.title-cell strong {
  display: block;
  color: var(--text-primary);
  font-weight: 600;
}

.msg-hint {
  margin: 4px 0 0;
  font-size: 11px;
  color: var(--text-secondary);
  line-height: 1.4;
}

.mono {
  font-family: ui-monospace, monospace;
  font-size: 12px;
}

.metric-cell {
  font-size: 12px;
  white-space: nowrap;
}

.tag {
  display: inline-block;
  padding: 2px 10px;
  border-radius: 999px;
  font-size: 12px;
  white-space: nowrap;
}

.tag--info {
  background: rgba(77, 163, 255, 0.15);
  color: var(--accent-blue);
}

.tag--warn {
  background: rgba(245, 185, 66, 0.2);
  color: var(--accent-amber);
}

.tag--critical {
  background: rgba(255, 107, 107, 0.15);
  color: var(--accent-red);
}

.tag--active {
  background: rgba(245, 185, 66, 0.15);
  color: var(--accent-amber);
}

.tag--resolved {
  background: rgba(61, 220, 132, 0.15);
  color: var(--accent-green);
}

.empty-cell {
  text-align: center;
  padding: 24px !important;
}

.row-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 6px;
}

.pagination {
  margin-top: 14px;
  display: flex;
  align-items: center;
  justify-content: flex-end;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 13px;
  color: var(--text-secondary);
}

.jump-input {
  width: 72px;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 7px 8px;
  background: rgba(0, 0, 0, 0.25);
  color: var(--text-primary);
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

.notice.success {
  background: rgba(61, 220, 132, 0.15);
  color: var(--accent-green);
  border: 1px solid rgba(61, 220, 132, 0.35);
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
  .form-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .form-grid .span-2 {
    grid-column: span 2;
  }

  .stat-row {
    grid-template-columns: 1fr;
  }
}
</style>

<script setup>
import { computed, onMounted, reactive, ref } from "vue";
import {
  createDevice,
  deleteDevice,
  getDeviceList,
  updateDevice,
} from "../api/dashboard";

const loading = ref(false);
const saving = ref(false);
const devices = ref([]);
const editingId = ref(null);
const page = ref(1);
const pageSize = 10;
const totalPages = ref(0);
const total = ref(0);
const jumpPage = ref("");
const notice = ref({ show: false, type: "success", text: "" });
let noticeTimer = null;

const form = reactive({
  node_id: "",
  name: "",
  device_type: "多合一传感器",
  region: "",
  install_location: "",
  status: "online",
  latitude: "",
  longitude: "",
});

const onlineCount = computed(
  () => devices.value.filter((d) => d.status === "online").length
);

const showNotice = (type, text) => {
  notice.value = { show: true, type, text };
  if (noticeTimer) clearTimeout(noticeTimer);
  noticeTimer = setTimeout(() => {
    notice.value.show = false;
  }, 2200);
};

const resetForm = () => {
  form.node_id = "";
  form.name = "";
  form.device_type = "多合一传感器";
  form.region = "";
  form.install_location = "";
  form.status = "online";
  form.latitude = "";
  form.longitude = "";
  editingId.value = null;
};

const loadList = async () => {
  loading.value = true;
  try {
    const data = await getDeviceList({ page: page.value, page_size: pageSize });
    devices.value = Array.isArray(data?.results) ? data.results : [];
    total.value = Number(data?.pagination?.total || 0);
    totalPages.value = Number(data?.pagination?.total_pages || 0);
    if (totalPages.value > 0 && page.value > totalPages.value) {
      page.value = totalPages.value;
      await loadList();
    }
  } catch (error) {
    showNotice("error", `加载失败: ${error}`);
    devices.value = [];
  } finally {
    loading.value = false;
  }
};

const toPayload = () => ({
  node_id: form.node_id.trim(),
  name: form.name.trim(),
  device_type: form.device_type.trim(),
  region: form.region.trim(),
  install_location: form.install_location.trim(),
  status: form.status,
  latitude: form.latitude === "" ? null : Number(form.latitude),
  longitude: form.longitude === "" ? null : Number(form.longitude),
});

const submitForm = async () => {
  if (!form.node_id.trim() || !form.name.trim()) {
    showNotice("error", "请填写节点编号和节点名称");
    return;
  }

  saving.value = true;
  try {
    const payload = toPayload();
    if (editingId.value) {
      await updateDevice(editingId.value, payload);
      showNotice("success", "节点修改成功");
    } else {
      await createDevice(payload);
      showNotice("success", "节点新增成功");
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
  form.node_id = item.node_id;
  form.name = item.name;
  form.device_type = item.device_type || "多合一传感器";
  form.region = item.region || "";
  form.install_location = item.install_location || "";
  form.status = item.status || "online";
  form.latitude = item.latitude ?? "";
  form.longitude = item.longitude ?? "";
};

const removeItem = async (id) => {
  if (!window.confirm("确定删除该监测节点吗？")) return;
  try {
    await deleteDevice(id);
    showNotice("success", "删除成功");
    if (devices.value.length === 1 && page.value > 1) page.value -= 1;
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

const statusLabel = (status) => (status === "online" ? "在线" : "离线");

onMounted(loadList);
</script>

<template>
  <div class="device-page">
    <transition name="toast">
      <div v-if="notice.show" class="notice" :class="notice.type">{{ notice.text }}</div>
    </transition>

    <header class="page-header">
      <div>
        <h1>设备管理</h1>
        <p class="subtitle">监测节点增删改查与 GPS 位置维护</p>
      </div>
      <button type="button" class="btn-ghost" :disabled="loading" @click="loadList">刷新列表</button>
    </header>

    <section class="stat-row">
      <article class="stat-card dash-card">
        <span class="stat-label">节点总数</span>
        <strong>{{ total }}</strong>
      </article>
      <article class="stat-card dash-card">
        <span class="stat-label">当前页在线</span>
        <strong class="text-green">{{ onlineCount }}</strong>
      </article>
      <article class="stat-card dash-card">
        <span class="stat-label">当前页离线</span>
        <strong class="text-amber">{{ devices.length - onlineCount }}</strong>
      </article>
    </section>

    <section class="dash-card form-panel">
      <h2>{{ editingId ? "编辑监测节点" : "新增监测节点" }}</h2>
      <div class="form-grid">
        <label>
          <span>节点编号 *</span>
          <input v-model="form.node_id" type="text" placeholder="如 GH-A-01" :disabled="!!editingId" />
        </label>
        <label>
          <span>节点名称 *</span>
          <input v-model="form.name" type="text" placeholder="如 温室A-01" />
        </label>
        <label>
          <span>设备类型</span>
          <input v-model="form.device_type" type="text" placeholder="多合一传感器" />
        </label>
        <label>
          <span>所属区域</span>
          <input v-model="form.region" type="text" placeholder="温室 A 区" />
        </label>
        <label>
          <span>安装位置</span>
          <input v-model="form.install_location" type="text" placeholder="A区第1垄" />
        </label>
        <label>
          <span>状态</span>
          <select v-model="form.status">
            <option value="online">在线</option>
            <option value="offline">离线</option>
          </select>
        </label>
        <label>
          <span>纬度</span>
          <input v-model="form.latitude" type="number" step="0.0001" placeholder="31.2304" />
        </label>
        <label>
          <span>经度</span>
          <input v-model="form.longitude" type="number" step="0.0001" placeholder="121.4737" />
        </label>
      </div>
      <div class="actions">
        <button type="button" class="btn-primary" :disabled="saving" @click="submitForm">
          {{ saving ? "提交中..." : editingId ? "保存修改" : "新增节点" }}
        </button>
        <button type="button" class="btn-ghost" @click="resetForm">清空</button>
      </div>
    </section>

    <section class="dash-card list-panel">
      <h2>节点列表</h2>
      <p v-if="loading" class="loading-text">加载中...</p>
      <div v-else class="table-wrap">
        <table class="device-table">
          <thead>
            <tr>
              <th>节点编号</th>
              <th>名称</th>
              <th>设备类型</th>
              <th>区域</th>
              <th>状态</th>
              <th>GPS</th>
              <th>更新时间</th>
              <th>操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="item in devices" :key="item.id">
              <td class="mono">{{ item.node_id }}</td>
              <td>{{ item.name }}</td>
              <td>{{ item.device_type }}</td>
              <td>{{ item.region || "-" }}</td>
              <td>
                <span class="tag" :class="item.status === 'online' ? 'tag--online' : 'tag--offline'">
                  {{ statusLabel(item.status) }}
                </span>
              </td>
              <td class="gps-cell">
                <template v-if="item.latitude != null && item.longitude != null">
                  {{ Number(item.latitude).toFixed(4) }}, {{ Number(item.longitude).toFixed(4) }}
                </template>
                <span v-else class="muted">未设置</span>
              </td>
              <td>{{ formatTime(item.updated_at) }}</td>
              <td class="row-actions">
                <button type="button" class="btn-ghost btn-sm" @click="startEdit(item)">编辑</button>
                <button type="button" class="btn-danger btn-sm" @click="removeItem(item.id)">删除</button>
              </td>
            </tr>
            <tr v-if="devices.length === 0">
              <td colspan="8" class="empty-cell">暂无节点数据</td>
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
.device-page {
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

.text-green {
  color: var(--accent-green);
}

.text-amber {
  color: var(--accent-amber);
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

label span {
  display: block;
  margin-bottom: 6px;
  font-size: 12px;
  color: var(--text-secondary);
}

input,
select {
  width: 100%;
  border: 1px solid var(--border);
  border-radius: 8px;
  padding: 9px 11px;
  background: rgba(0, 0, 0, 0.25);
  color: var(--text-primary);
  font-size: 14px;
  outline: none;
  transition: border-color 0.15s;
}

input:focus,
select:focus {
  border-color: rgba(61, 220, 132, 0.5);
}

input:disabled {
  opacity: 0.55;
  cursor: not-allowed;
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

.device-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
}

.device-table th,
.device-table td {
  text-align: left;
  padding: 11px 10px;
  border-bottom: 1px solid var(--border);
  color: var(--text-secondary);
}

.device-table th {
  color: var(--text-primary);
  font-weight: 600;
  font-size: 12px;
  white-space: nowrap;
}

.device-table tbody td:nth-child(1),
.device-table tbody td:nth-child(2) {
  color: var(--text-primary);
}

.mono {
  font-family: ui-monospace, monospace;
  font-size: 12px;
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

.gps-cell {
  font-size: 12px;
  font-family: ui-monospace, monospace;
}

.muted {
  color: var(--text-secondary);
}

.empty-cell {
  text-align: center;
  padding: 24px !important;
}

.row-actions {
  display: flex;
  gap: 8px;
  white-space: nowrap;
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

  .stat-row {
    grid-template-columns: 1fr;
  }
}
</style>

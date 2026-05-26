<script setup>
import { computed } from "vue";
import { useRoute } from "vue-router";

const route = useRoute();

const menuItems = [
  { label: "数据总览", path: "/overview", icon: "overview" },
  { label: "设备管理", path: "/device-manage", icon: "device" },
  { label: "告警记录", path: "/alarm-center", icon: "alarm" },
  { label: "系统设置", path: "/system-settings", icon: "settings" },
  { label: "问问AI", path: "/chat", icon: "ai" },
];

const currentTitle = computed(() => route.meta.title || "智慧农业作物监测系统");
const isFlushPage = computed(() => ["/overview", "/device-manage"].includes(route.path));
</script>

<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="brand">
        <div class="brand-logo">AIMC</div>
        <div class="brand-info">
          <div class="brand-title">智慧农业作物监测系统</div>
          <div class="brand-sub">Agricultural IoT Platform</div>
        </div>
      </div>

      <nav class="menu">
        <RouterLink
          v-for="item in menuItems"
          :key="`${item.path}-${item.label}`"
          :to="item.path"
          class="menu-item"
          :class="{ active: route.path === item.path }"
        >
          <span class="menu-icon" :data-icon="item.icon" aria-hidden="true" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </nav>

      <div class="mesh-card">
        <div class="mesh-card__title">Mesh 网络状态</div>
        <div class="mesh-card__row">
          <span class="status-dot" />
          <span>正常</span>
        </div>
        <div class="mesh-card__meta">
          <div><span>在线节点</span><strong>23 / 25</strong></div>
          <div><span>网络质量</span><strong>优秀 92%</strong></div>
        </div>
        <div class="mesh-card__time">更新于 2026-05-23 14:32:08</div>
      </div>
    </aside>

    <main class="main-content">
      <header v-if="!isFlushPage" class="simple-topbar">
        <h1>{{ currentTitle }}</h1>
      </header>
      <div class="content-container" :class="{ 'content-container--flush': isFlushPage }">
        <RouterView />
      </div>
    </main>
  </div>
</template>

<style scoped>
.menu-item.active {
  background: rgba(46, 204, 113, 0.18);
  color: #3ddc84;
  border-color: rgba(61, 220, 132, 0.35);
}
</style>

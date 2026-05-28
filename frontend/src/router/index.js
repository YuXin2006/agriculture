import { createRouter, createWebHistory } from "vue-router";
import MainLayout from "../layouts/MainLayout.vue";
import Overview from "../views/Overview.vue";
import DeviceManage from "../views/DeviceManage.vue";
import AlarmCenter from "../views/AlarmCenter.vue";
import SystemSettings from "../views/SystemSettings.vue";
import HelpCenter from "../views/HelpCenter.vue";
import ChatBot from "../views/ChatBot.vue";

const routes = [
  {
    path: "/",
    component: MainLayout,
    children: [
      {
        path: "",
        redirect: "/overview",
      },
      {
        path: "overview",
        name: "overview",
        component: Overview,
        meta: { title: "基地总览" },
      },
      {
        path: "device-manage",
        name: "device-manage",
        component: DeviceManage,
        meta: { title: "设备管理" },
      },
      {
        path: "alarm-center",
        name: "alarm-center",
        component: AlarmCenter,
        meta: { title: "告警中心" },
      },
      {
        path: "system-settings",
        name: "system-settings",
        component: SystemSettings,
        meta: { title: "运维中心" },
      },
      {
        path: "help-center",
        name: "help-center",
        component: HelpCenter,
        meta: { title: "帮助中心" },
      },
      {
        path: "chat",
        name: "chat",
        component: ChatBot,
        meta: { title: "问问AI" },
      },
    ],
  },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

export default router;

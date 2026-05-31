import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";

export default defineConfig({
  plugins: [vue()],
  server: {
    port: 5173,
  },
  build: {
    chunkSizeWarningLimit: 2000 // 将阈值改为 2000KB
  }
});

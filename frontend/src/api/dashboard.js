import http from "./Http";
import WebSocketClient from "../utils/WebSocketClient";

export const getOverview = (params = {}) => {
  return http.get("/api/overview/", params);
};
// 获取传感器列表
export const getSensorList = (params = {}) => {
  return http.get("/api/sensors/", params);
};
// 新增传感器
export const createSensor = (data) => {
  return http.post("/api/sensors/", data);
};
// 更新传感器
export const updateSensor = (id, data) => {
  return http.put(`/api/sensors/${id}/`, data);
};
// 删除传感器
export const deleteSensor = (id) => {
  return http.delete(`/api/sensors/${id}/`);
};
// 获取设备列表
export const getDeviceList = (params = {}) => {
  return http.get("/api/devices/", params);
};
// 创建设备
export const createDevice = (data) => {
  return http.post("/api/devices/", data);
};
// 更新设备
export const updateDevice = (id, data) => {
  return http.put(`/api/devices/${id}/`, data);
};
// 删除设备
export const deleteDevice = (id) => {
  return http.delete(`/api/devices/${id}/`);
};
// 获取设备 GPS 定位数据
export const getDeviceGps = (id) => {
  return http.get(`/api/devices/${id}/gps/`);
};

// 告警记录列表
export const getAlarmList = (params = {}) => {
  return http.get("/api/alarm/", params);
};
// 新增告警
export const createAlarm = (data) => {
  return http.post("/api/alarm/", data);
};
// 更新告警
export const updateAlarm = (id, data) => {
  return http.put(`/api/alarm/${id}/`, data);
};
// 删除告警
export const deleteAlarm = (id) => {
  return http.delete(`/api/alarm/${id}/`);
};

// 系统运行状态（运维看板）
export const getSystemStatus = () => {
  return http.get("/api/system/status/");
};

// 发送 AI 聊天消息（非流式，备用）
export const sendChatMessage = (data) => {
  return http.post("/api/chat/", data, { timeout: 120000 });
};

// 流式发送 AI 聊天消息（SSE）
export const streamChatMessage = (data, callbacks = {}) => {
  const baseURL = import.meta.env.VITE_BASE_URL || "http://127.0.0.1:8000";
  const { onSession, onToken, onDone, onError } = callbacks;

  return new Promise((resolve, reject) => {
    fetch(`${baseURL}/api/chat/stream/`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data),
    })
      .then(async (response) => {
        if (!response.ok) {
          const errBody = await response.json().catch(() => ({}));
          const detail = errBody?.detail || `请求失败 (${response.status})`;
          onError?.(detail);
          reject(detail);
          return;
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder();
        let buffer = "";

        const pump = () =>
          reader.read().then(({ done, value }) => {
            if (done) {
              resolve();
              return;
            }

            buffer += decoder.decode(value, { stream: true });
            const lines = buffer.split("\n");
            buffer = lines.pop() || "";

            for (const line of lines) {
              if (!line.startsWith("data: ")) continue;
              try {
                const event = JSON.parse(line.slice(6));
                if (event.type === "session") {
                  onSession?.(event.session_id);
                } else if (event.type === "token") {
                  onToken?.(event.content);
                } else if (event.type === "done") {
                  onDone?.(event.reply);
                } else if (event.type === "error") {
                  onError?.(event.detail);
                  reject(event.detail);
                  return;
                }
              } catch {
                /* 忽略解析失败的行 */
              }
            }
            return pump();
          });

        return pump();
      })
      .catch((err) => {
        const detail = err?.message || "网络请求失败";
        onError?.(detail);
        reject(detail);
      });
  });
};

// 获取聊天历史
export const getChatHistory = (params = {}) => {
  return http.get("/api/chat/history/", params);
};

// 清空当前会话
export const clearChatSession = (data = {}) => {
  return http.post("/api/chat/clear/", data);
};

export { WebSocketClient };
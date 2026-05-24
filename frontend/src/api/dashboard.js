import http from "./Http";

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

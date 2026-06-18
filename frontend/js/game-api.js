/**
 * API 调用封装模块
 * 负责：所有 fetch 调用、错误处理、响应解析
 * 依赖：game-core.js
 */

window.GameAPI = (function() {
  const { API_BASE, getToken, setToken, clearToken } = window.GameCore;

  // ========== 通用请求封装 ==========
  async function request(path, options = {}) {
    const headers = { "Content-Type": "application/json", ...(options.headers || {}) };
    const token = getToken();
    if (token) headers.Authorization = `Bearer ${token}`;
    const response = await fetch(`${API_BASE}${path}`, { ...options, headers });
    const data = await response.json();
    if (!response.ok) throw new Error(data.detail || "请求失败");
    return data;
  }

  // ========== 认证相关 API ==========
  async function register(username, password) {
    const data = await request("/register", { 
      method: "POST", 
      body: JSON.stringify({ username, password }) 
    });
    setToken(data.token);
    return data;
  }

  async function login(username, password) {
    const data = await request("/login", { 
      method: "POST", 
      body: JSON.stringify({ username, password }) 
    });
    setToken(data.token);
    return data;
  }

  function logout() {
    clearToken();
    window.GameCore.setCurrentUser(null);
  }

  // ========== 角色相关 API ==========
  async function getCharacterMe() {
    return await request("/character/me");
  }

  async function changeTitle(title) {
    return await request("/character/title", { 
      method: "POST", 
      body: JSON.stringify({ title }) 
    });
  }

  // ========== 行动相关 API ==========
  async function executeAction(actionType, params = {}) {
    return await request("/action/execute", {
      method: "POST",
      body: JSON.stringify({ action_type: actionType, params })
    });
  }

  // ========== 功法/法宝 API ==========
  async function getMethods() {
    return await request("/methods");
  }

  async function getArtifacts() {
    return await request("/artifacts");
  }

  // ========== 日志 API ==========
  async function getLogs(limit = 30) {
    return await request(`/logs?limit=${limit}`);
  }

  // ========== 宗门 API ==========
  async function getSects() {
    return await request("/sects");
  }

  async function getMySect() {
    return await request("/sects/me");
  }

  async function getSectTasks() {
    return await request("/sects/tasks");
  }

  async function getMySectTasks() {
    return await request("/sects/tasks/me");
  }

  async function getSectShop() {
    return await request("/sects/shop");
  }

  // ========== 生活技能 API ==========
  async function getRecipes() {
    return await request("/life-skills/recipes");
  }

  // ========== 自动修行 API ==========
  async function getAutoCultivationStatus() {
    return await request("/auto-cultivation/status");
  }

  async function executeTick() {
    return await request("/action/execute-tick", {
      method: "POST",
      body: JSON.stringify({ action_type: "auto_cultivation_tick", params: {} })
    });
  }

  // ========== 目标建议 API ==========
  async function getGoals() {
    return await request("/goals/current");
  }

  // ========== 公共接口 ==========
  return {
    request,
    register,
    login,
    logout,
    getCharacterMe,
    changeTitle,
    executeAction,
    getMethods,
    getArtifacts,
    getLogs,
    getSects,
    getMySect,
    getSectTasks,
    getMySectTasks,
    getSectShop,
    getRecipes,
    getAutoCultivationStatus,
    executeTick,
    getGoals,
  };
})();

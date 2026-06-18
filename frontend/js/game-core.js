/**
 * 游戏核心逻辑模块
 * 负责：角色状态管理、资源计算、全局状态
 */

window.GameCore = (function() {
  // ========== 常量定义 ==========
  const API_BASE = (function() {
    const apiParams = new URLSearchParams(window.location.search);
    const configuredApiBase = apiParams.get("apiBase")
      || localStorage.getItem("xiuxian_api_base")
      || "http://localhost:8000";
    if (apiParams.get("apiBase")) localStorage.setItem("xiuxian_api_base", apiParams.get("apiBase"));
    const legacyPort = localStorage.getItem("xiuxian_api_port");
    return legacyPort
      ? `${window.location.protocol}//${window.location.hostname}:${legacyPort}`
      : configuredApiBase;
  })();
  
  const tokenKey = "xiuxian_mmo_token";

  // ========== 全局状态 ==========
  let currentUser = null;
  let currentMethods = [];
  let currentArtifacts = [];
  let currentSect = null;
  let sectCatalog = [];
  let availableSectTasks = [];
  let mySectTasks = [];
  let currentSectShop = [];
  let currentActiveEffects = [];
  let currentSkillTab = "alchemy";
  let fetchedRecipes = null;
  let currentAutoStatus = null;

  // ========== 物品和效果名称映射 ==========
  const ITEM_NAMES = {
    low_spirit_stone: "下品灵石", low_material: "下品材料", healing_herb: "疗伤草", formula_scroll: "空白配方卷",
    beast_core: "妖兽内丹", mana_pill: "回灵丹", qi_powder: "聚气散",
    yangqi_pill: "养气丹", guyu_pill: "固元丹", huichun_pill: "回春丹",
    foundation_pill: "筑基丹", scout_talisman: "探查符", guard_talisman: "护身符",
    swift_talisman: "速行符", calm_talisman: "清心符", crafted_low_sword: "低阶剑",
    explore_luck_talisman: "寻机符", avoid_harm_talisman: "避害符", spirit_gather_talisman: "聚灵符",
    qingmu_pendant: "青木坠", juqi_jade: "聚气玉", hushen_bell: "护身铃",
    gathering_artifact: "聚灵器", explore_puppet: "探索傀儡",
    foundation_pill_formula: "筑基丹配方", swift_talisman_formula: "速行符配方",
    explore_puppet_formula: "探索傀儡配方",
    formation_gather_spirit: "聚灵阵", formation_guard: "护身阵", formation_draw_spirit: "引灵阵",
  };

  const EFFECT_TYPE_NAMES = {
    explore_luck_bonus: "探查运气加成", explore_damage_reduction: "探索减伤",
    explore_mana_discount: "探索法力折扣", train_cultivation_bonus: "修炼加成",
    train_next_bonus: "下次修炼收益提升", breakthrough_next_bonus: "下次突破概率提升",
    explore_reward_bonus: "探索奖励加成",
  };

  // ========== 工具函数 ==========
  function getItemName(code) {
    return ITEM_NAMES[code] || "未知物品";
  }

  function getEffectTypeName(type) {
    return EFFECT_TYPE_NAMES[type] || "未知效果";
  }

  function _formatEffectValue(value) {
    if (typeof value !== "number") return String(value);
    if (value < 1 && value > 0) return (value * 100).toFixed(0) + "%";
    if (Number.isInteger(value)) return String(value);
    return value.toFixed(2);
  }

  function _hasItem(code) {
    return currentUser?.inventory.some(i => i.code === code && i.quantity > 0) || false;
  }

  // ========== Token 管理 ==========
  function getToken() {
    return localStorage.getItem(tokenKey);
  }

  function setToken(token) {
    localStorage.setItem(tokenKey, token);
  }

  function clearToken() {
    localStorage.removeItem(tokenKey);
  }

  // ========== 公共接口 ==========
  return {
    // 常量
    API_BASE,
    tokenKey,
    ITEM_NAMES,
    EFFECT_TYPE_NAMES,

    // 状态获取/设置
    getCurrentUser: () => currentUser,
    setCurrentUser: (data) => { currentUser = data; },
    
    getCurrentMethods: () => currentMethods,
    setCurrentMethods: (methods) => { currentMethods = methods; },
    
    getCurrentArtifacts: () => currentArtifacts,
    setCurrentArtifacts: (artifacts) => { currentArtifacts = artifacts; },
    
    getCurrentSect: () => currentSect,
    setCurrentSect: (sect) => { currentSect = sect; },
    
    getSectCatalog: () => sectCatalog,
    setSectCatalog: (catalog) => { sectCatalog = catalog; },
    
    getAvailableSectTasks: () => availableSectTasks,
    setAvailableSectTasks: (tasks) => { availableSectTasks = tasks; },
    
    getMySectTasks: () => mySectTasks,
    setMySectTasks: (tasks) => { mySectTasks = tasks; },
    
    getCurrentSectShop: () => currentSectShop,
    setCurrentSectShop: (shop) => { currentSectShop = shop; },
    
    getCurrentActiveEffects: () => currentActiveEffects,
    setCurrentActiveEffects: (effects) => { currentActiveEffects = effects; },
    
    getCurrentSkillTab: () => currentSkillTab,
    setCurrentSkillTab: (tab) => { currentSkillTab = tab; },
    
    getFetchedRecipes: () => fetchedRecipes,
    setFetchedRecipes: (recipes) => { fetchedRecipes = recipes; },
    
    getCurrentAutoStatus: () => currentAutoStatus,
    setCurrentAutoStatus: (status) => { currentAutoStatus = status; },

    // 工具函数
    getItemName,
    getEffectTypeName,
    _formatEffectValue,
    _hasItem,

    // Token 管理
    getToken,
    setToken,
    clearToken,
  };
})();

/**
 * 游戏主入口模块
 * 负责：初始化、事件绑定、定时器启动
 * 依赖：game-core.js, game-api.js, game-ui.js, game-actions.js
 */

window.GameMain = (function() {
  const { getToken, clearToken, getCurrentUser, setTab: setCurrentTab } = window.GameCore;
  const { register, login, logout } = window.GameAPI;
  const { showGame, initTooltips, closeNarrativePanel, skipTypewriter, showNarrativePanel } = window.GameUI;
  const { loadMe, renderRecipes, startRealtimeLogPolling } = window.GameActions;

  // ========== 标签切换 ==========
  function setTab(tab) {
    document.querySelectorAll(".tab-panel").forEach((p) => p.classList.add("hidden"));
    document.getElementById(`tab-${tab}`).classList.remove("hidden");
    document.querySelectorAll(".tabs button").forEach((b) => b.classList.toggle("active", b.dataset.tab === tab));
    if (tab === "life-skills") renderRecipes("alchemy");
  }

  // ========== 事件绑定 ==========
  function bindEvents() {
    // 认证相关
    document.getElementById("register-btn").addEventListener("click", () => {
      const username = document.getElementById("username").value.trim();
      const password = document.getElementById("password").value;
      register(username, password).then(() => loadMe()).catch(e => window.GameUI.showToast(e.message));
    });

    document.getElementById("login-btn").addEventListener("click", () => {
      const username = document.getElementById("username").value.trim();
      const password = document.getElementById("password").value;
      login(username, password).then(() => loadMe()).catch(e => window.GameUI.showToast(e.message));
    });

    document.getElementById("logout-btn").addEventListener("click", () => {
      logout();
      window.GameUI.showToast("");
      showGame(false);
      document.getElementById("hero-name").textContent = "云游散修";
      document.getElementById("hero-realm").textContent = "太虚历 6513年";
      document.getElementById("hero-subtitle").textContent = "沧澜修仙志";
      document.getElementById("hero-pill").textContent = "灵网连通";
    });

    // 基础行动
    document.getElementById("train-btn").addEventListener("click", () => {
      window.GameActions.doTrain().catch(e => window.GameUI.showToast(e.message));
    });

    document.getElementById("explore-btn").addEventListener("click", () => {
      window.GameActions.doExplore().catch(e => window.GameUI.showToast(e.message));
    });

    document.getElementById("breakthrough-btn").addEventListener("click", () => {
      window.GameActions.doBreakthrough().catch(e => window.GameUI.showToast(e.message));
    });

    document.getElementById("meditate-btn").addEventListener("click", () => {
      window.GameActions.doMeditate().catch(e => window.GameUI.showToast(e.message));
    });

    document.getElementById("spirit-stone-btn").addEventListener("click", () => {
      window.GameActions.doSpiritStone().catch(e => window.GameUI.showToast(e.message));
    });

    document.getElementById("pill-btn").addEventListener("click", () => {
      window.GameActions.doPill().catch(e => window.GameUI.showToast(e.message));
    });

    // 刷新按钮
    document.getElementById("refresh-btn").addEventListener("click", () => {
      loadMe().catch(e => window.GameUI.showToast(e.message));
    });

    document.getElementById("refresh-sect-btn").addEventListener("click", () => {
      window.GameActions.loadSect().catch(e => window.GameUI.showToast(e.message));
    });

    // 称号选择
    document.getElementById("title-select").addEventListener("change", () => {
      const title = document.getElementById("title-select").value;
      window.GameAPI.changeTitle(title).then(() => loadMe()).catch(e => window.GameUI.showToast(e.message));
    });

    // 灵根帮助
    const rootHelp = document.getElementById("root-help");
    document.getElementById("close-root-help").addEventListener("click", () => {
      rootHelp.classList.add("hidden");
    });
    rootHelp.addEventListener("click", e => {
      if (e.target === rootHelp) rootHelp.classList.add("hidden");
    });

    // 叙事面板事件
    document.getElementById("narrative-continue")?.addEventListener("click", () => {
      if (!window.GameUI._typewriterDone) {
        window.GameUI.skipTypewriter();
      } else {
        closeNarrativePanel();
      }
    });

    document.getElementById("narrative-fullscreen-continue")?.addEventListener("click", () => {
      if (!window.GameUI._typewriterDone) {
        window.GameUI.skipTypewriter();
      } else {
        closeNarrativePanel();
      }
    });

    // 空格键跳过叙事
    document.addEventListener("keydown", (e) => {
      if (e.code === "Space" || e.code === "Enter") {
        const overlay = document.getElementById("narrative-overlay");
        const fullscreen = document.getElementById("narrative-fullscreen");
        if (!overlay.classList.contains("hidden") || !fullscreen.classList.contains("hidden")) {
          e.preventDefault();
          if (!overlay.classList.contains("hidden")) {
            document.getElementById("narrative-continue")?.click();
          } else {
            document.getElementById("narrative-fullscreen-continue")?.click();
          }
        }
      }
    });

    // 行囊点击
    document.getElementById("inventory").addEventListener("click", event => {
      const button = event.target.closest("button[data-slot-action]");
      if (!button) return;
      const slotIndex = Number(button.dataset.slotIndex);
      const actionType = button.dataset.slotAction;
      window.GameActions.doAction(actionType, { slot_index: slotIndex }).catch(e => window.GameUI.showToast(e.message));
    });

    // 功法
    document.getElementById("methods-list").addEventListener("click", event => {
      const equip = event.target.closest("button[data-method-equip]");
      const practice = event.target.closest("button[data-method-practice]");
      if (equip) window.GameActions.doAction("equip_method", { method_id: Number(equip.dataset.methodEquip) }).catch(e => window.GameUI.showToast(e.message));
      if (practice) window.GameActions.doAction("practice_method", { method_id: Number(practice.dataset.methodPractice) }).catch(e => window.GameUI.showToast(e.message));
    });

    // 法宝
    document.getElementById("artifacts-list").addEventListener("click", event => {
      const upgrade = event.target.closest("button[data-artifact-upgrade]");
      const unequip = event.target.closest("button[data-artifact-unequip]");
      if (upgrade) window.GameActions.doAction("upgrade_artifact", { artifact_id: Number(upgrade.dataset.artifactUpgrade) }).catch(e => window.GameUI.showToast(e.message));
      if (unequip) window.GameActions.doAction("unequip_artifact", { artifact_id: Number(unequip.dataset.artifactUnequip) }).catch(e => window.GameUI.showToast(e.message));
    });

    // 生活技能子标签
    document.querySelectorAll(".life-skills-subtabs button").forEach(btn => {
      btn.addEventListener("click", () => {
        document.querySelectorAll(".life-skills-subtabs button").forEach(b => b.classList.remove("active"));
        btn.classList.add("active");
        renderRecipes(btn.dataset.skill);
      });
    });

    // 生活技能配方点击
    document.getElementById("recipes-list").addEventListener("click", event => {
      const button = event.target.closest("button[data-recipe-id]");
      if (!button || button.disabled) return;
      const recipeId = button.dataset.recipeId;
      const skillType = button.dataset.skillType;
      window.GameActions.doAction(skillType, { recipe_id: recipeId }).catch(e => window.GameUI.showToast(e.message));
    });

    // 宗门
    document.getElementById("sect-list").addEventListener("click", event => {
      const join = event.target.closest("button[data-join-sect]");
      if (join) window.GameActions.doAction("join_sect", { sect_code: join.dataset.joinSect }).catch(e => window.GameUI.showToast(e.message));
    });

    document.getElementById("sect-tasks").addEventListener("click", event => {
      const accept = event.target.closest("button[data-accept-sect-task]");
      const complete = event.target.closest("button[data-complete-sect-task]");
      const abandon = event.target.closest("button[data-abandon-sect-task]");
      if (accept) window.GameActions.doAction("accept_sect_task", { task_code: accept.dataset.acceptSectTask }).catch(e => window.GameUI.showToast(e.message));
      if (complete) window.GameActions.doAction("complete_sect_task", { task_id: Number(complete.dataset.completeSectTask) }).catch(e => window.GameUI.showToast(e.message));
      if (abandon) window.GameActions.doAction("sect_task_abandon").catch(e => window.GameUI.showToast(e.message));
    });

    document.getElementById("sect-shop").addEventListener("click", event => {
      const exchange = event.target.closest("button[data-exchange-sect-reward]");
      if (exchange) window.GameActions.doAction("exchange_sect_reward", { reward_code: exchange.dataset.exchangeSectReward }).catch(e => window.GameUI.showToast(e.message));
    });

    document.getElementById("sect-summary").addEventListener("click", event => {
      const action = event.target.closest("button[data-sect-action]");
      if (!action) return;
      if (action.dataset.sectAction === "promote") window.GameActions.doAction("promote_sect_position").catch(e => window.GameUI.showToast(e.message));
      if (action.dataset.sectAction === "leave") window.GameActions.doAction("leave_sect").catch(e => window.GameUI.showToast(e.message));
    });

    // 标签切换
    document.querySelectorAll(".tabs button").forEach(button => {
      button.addEventListener("click", () => setTab(button.dataset.tab));
    });

    // 自动修行事件
    document.getElementById("auto-start-btn")?.addEventListener("click", () => {
      const strategy = window.GameCore.getCurrentAutoStatus()?.strategy || "balanced";
      window.GameActions.doAutoConfig(strategy, true);
    });

    document.getElementById("auto-settle-btn")?.addEventListener("click", () => {
      window.GameActions.doAutoSettle();
    });

    document.getElementById("auto-pause-btn")?.addEventListener("click", () => {
      window.GameActions.doAutoPause();
    });

    document.getElementById("auto-resume-btn")?.addEventListener("click", () => {
      window.GameActions.doAutoResume();
    });

    document.querySelectorAll(".strategy-btn").forEach(btn => {
      btn.addEventListener("click", () => {
        window.GameActions.doAutoConfig(btn.dataset.strategy, window.GameCore.getCurrentAutoStatus()?.enabled || false);
      });
    });

    // Goals Panel 事件
    const toggleGoalsBtn = document.getElementById("toggle-goals-btn");
    const showGoalsBtn = document.getElementById("show-goals-btn");

    toggleGoalsBtn?.addEventListener("click", () => {
      localStorage.setItem("xiuxian_goals_hidden", "true");
      document.getElementById("goals-panel").classList.add("hidden");
      document.getElementById("goals-hidden-entry").classList.remove("hidden");
    });

    showGoalsBtn?.addEventListener("click", () => {
      localStorage.setItem("xiuxian_goals_hidden", "false");
      document.getElementById("goals-panel").classList.remove("hidden");
      document.getElementById("goals-hidden-entry").classList.add("hidden");
      window.GameActions.loadGoals();
    });

    // 临时操作折叠
    const toggleTempOpsBtn = document.getElementById("toggle-temp-ops-btn");
    const tempOpsContent = document.getElementById("temp-ops-content");
    const tempOpsRecovery = document.getElementById("temp-ops-recovery");

    toggleTempOpsBtn?.addEventListener("click", () => {
      const isHidden = tempOpsContent.style.display === "none";
      if (isHidden) {
        tempOpsContent.style.display = "grid";
        tempOpsRecovery.style.display = "grid";
        toggleTempOpsBtn.textContent = "折叠";
        localStorage.setItem("xiuxian_temp_ops_hidden", "false");
      } else {
        tempOpsContent.style.display = "none";
        tempOpsRecovery.style.display = "none";
        toggleTempOpsBtn.textContent = "展开";
        localStorage.setItem("xiuxian_temp_ops_hidden", "true");
      }
    });

    // 默认折叠临时操作
    if (localStorage.getItem("xiuxian_temp_ops_hidden") === "true") {
      if (tempOpsContent) tempOpsContent.style.display = "none";
      if (tempOpsRecovery) tempOpsRecovery.style.display = "none";
      if (toggleTempOpsBtn) toggleTempOpsBtn.textContent = "展开";
    }
  }

  // ========== 初始化 ==========
  function init() {
    // P2-1: 初始化 Tooltip
    initTooltips();

    // 绑定所有事件
    bindEvents();

    // 检查是否已登录
    if (getToken()) {
      loadMe().catch(() => {
        clearToken();
        showGame(false);
      });
    } else {
      showGame(false);
    }
  }

  // ========== 公共接口 ==========
  return {
    init,
    setTab,
    bindEvents,
  };
})();

// ========== DOM 加载完成后初始化 ==========
document.addEventListener("DOMContentLoaded", () => {
  window.GameMain.init();
});

/**
 * 行动逻辑模块
 * 负责：吐纳/游历/叩关/服丹等行动函数
 * 依赖：game-core.js, game-api.js, game-ui.js
 */

window.GameActions = (function() {
  const { getCurrentUser, setCurrentUser, getCurrentSkillTab, setCurrentSkillTab, getFetchedRecipes, setFetchedRecipes } = window.GameCore;
  const { executeAction, getCharacterMe, getMethods, getArtifacts, getLogs, getSects, getMySect, getSectTasks, getMySectTasks, getSectShop, getRecipes } = window.GameAPI;
  const { showToast, showNarrativePanel, renderCharacter, renderAutoCultivation, renderGoals } = window.GameUI;

  // ========== 基础行动 ==========
  async function doAction(actionType, params = {}) {
    try {
      const data = await executeAction(actionType, params);

      // 检查是否有叙事文本
      if (data.narrative) {
        await new Promise(resolve => {
          showNarrativePanel(data.narrative, "popup", () => {
            resolve();
          });
        });
      }

      showToast(data.message, data.success);
      await loadMe();
    } catch (error) {
      showToast(error.message);
    }
  }

  async function doTrain() {
    await doAction("train");
  }

  async function doExplore() {
    await doAction("explore");
  }

  async function doBreakthrough() {
    await doAction("breakthrough");
  }

  async function doMeditate() {
    await doAction("recover_mana_meditate");
  }

  async function doSpiritStone() {
    await doAction("recover_mana_stone");
  }

  async function doPill() {
    const slot = getCurrentUser()?.inventory.find(item => item.code === "mana_pill" && item.quantity > 0);
    await doAction("use_item", { slot_index: slot ? slot.slot_index : 0 });
  }

  // ========== 自动修行相关 ==========
  async function doAutoConfig(strategy, enabled) {
    try {
      showToast("正在设置自动修行...");
      const result = await executeAction("auto_cultivation_config", { strategy, enabled });
      if (result.success) {
        showToast(result.message, true);
        renderAutoCultivation(result.character);
      } else {
        showToast(result.message);
      }
    } catch (e) {
      showToast("设置失败：" + e.message);
    }
  }

  async function doAutoSettle() {
    try {
      showToast("正在结算离线收益...");
      const result = await executeAction("auto_cultivation_settle", {});
      if (result.success) {
        showToast(result.message, true);
        renderAutoCultivation(result.character);
      } else {
        showToast(result.message);
      }
    } catch (e) {
      showToast("结算失败：" + e.message);
    }
  }

  async function doAutoPause() {
    try {
      showToast("正在暂停自动修行...");
      const result = await executeAction("auto_cultivation_pause", {});
      if (result.success) {
        showToast(result.message, true);
        renderAutoCultivation(result.character);
      } else {
        showToast(result.message);
      }
    } catch (e) {
      showToast("暂停失败：" + e.message);
    }
  }

  async function doAutoResume() {
    try {
      showToast("正在恢复自动修行...");
      const result = await executeAction("auto_cultivation_resume", {});
      if (result.success) {
        showToast(result.message, true);
        renderAutoCultivation(result.character);
      } else {
        showToast(result.message);
      }
    } catch (e) {
      showToast("恢复失败：" + e.message);
    }
  }

  // ========== 生活技能 ==========
  function renderRecipes(skillType) {
    setCurrentSkillTab(skillType);
    const recipes = (getFetchedRecipes() && getFetchedRecipes()[skillType]) || [];
    const container = document.getElementById("recipes-list");
    const char = getCurrentUser()?.character;

    if (!char) {
      container.innerHTML = `<div class="empty">请先登录</div>`;
      return;
    }

    if (recipes.length === 0) {
      container.innerHTML = `<div class="empty">暂无配方</div>`;
      return;
    }

    container.innerHTML = recipes.map((recipe) => {
      const isLocked = recipe.unlock_item && !_hasItem(recipe.unlock_item);
      const materials = recipe.materials || recipe.required_items || [];
      const materialsHtml = materials.map(i => `${i.name || getItemName(i.code || i.item_id)} x${i.quantity || i.count}`).join(" · ");
      const outputName = recipe.output_name || recipe.output_item_name || recipe.output_effect_name || (recipe.output_item_id ? getItemName(recipe.output_item_id) : getItemName(recipe.output_effect_id));
      const summary = recipe.effect_summary || recipe.output_item_description || recipe.output_effect_description || "";
      const requirement = recipe.realm_requirement || recipe.required_realm || "无";
      const canCraft = !isLocked && char.mana >= recipe.mana_cost;

      return `<div class="recipe-card">
        <div class="recipe-header">
          <strong>${recipe.name}</strong>
          <span style="font-size:11px;color:#e5c568">${recipe.mana_cost}法力</span>
        </div>
        <div class="recipe-info">
          <span>需求：${requirement}</span>
          <span>材料：${materialsHtml}</span>
          ${recipe.unlock_item ? `<span style="color:#d95f45">需配方：${recipe.unlock_item_name || getItemName(recipe.unlock_item)}</span>` : ""}
        </div>
        <div class="recipe-output">产出：${outputName}${recipe.output_count > 1 ? ` x${recipe.output_count}` : ""}</div>
        ${summary ? `<div class="recipe-info"><span>说明：${summary}</span></div>` : ""}
        <button data-recipe-id="${recipe.id}" data-skill-type="${skillType}" ${canCraft ? "" : "disabled"}>${isLocked ? "未解锁" : "制作"}</button>
      </div>`;
    }).join("");
  }

  // ========== 宗门相关 ==========
  function renderSect() {
    const sectCatalog = window.GameCore.getSectCatalog();
    const currentSect = window.GameCore.getCurrentSect();
    const availableSectTasks = window.GameCore.getAvailableSectTasks();
    const mySectTasks = window.GameCore.getMySectTasks();
    const currentSectShop = window.GameCore.getCurrentSectShop();
    
    const reputations = currentSect?.reputations || {};
    const sectSummary = document.getElementById("sect-summary");
    const sectTasks = document.getElementById("sect-tasks");
    const sectShop = document.getElementById("sect-shop");
    const sectList = document.getElementById("sect-list");

    if (!currentSect?.sect) {
      sectSummary.innerHTML = `<div class="empty">你目前是散修，可以选择一个宗门拜入。</div>`;
      sectTasks.innerHTML = `<div class="empty">加入宗门后可接取任务。</div>`;
      sectShop.innerHTML = `<div class="empty">加入宗门后可使用贡献兑换奖励。</div>`;
    } else {
      const sect = currentSect.sect;
      const member = currentSect.member;
      sectSummary.innerHTML = `<div class="row"><div><strong>${sect.name} · ${sect.faction_name}</strong><span>${member.position_name} · 贡献 ${member.contribution} · 声望 ${member.reputation}</span><span>正道 ${reputations.righteous || 0} / 魔道 ${reputations.demonic || 0} / 鬼道 ${reputations.ghost || 0} / 佛道 ${reputations.buddhist || 0}</span></div><button data-sect-action="promote">晋升</button><button data-sect-action="leave" class="danger">退出</button></div>`;
      
      const currentTasks = mySectTasks.filter(task => task.status === "active" || task.status === "claimable");
      const currentTasksHtml = currentTasks.length ? currentTasks.map(task => {
        const canComplete = task.status === "claimable" || task.is_donation;
        const progressBar = `<div style="margin-top:4px"><div class="bar"><span style="width:${Math.min(100, (task.progress / task.target) * 100)}%"></span></div></div>`;
        const abandonBtn = `<button data-abandon-sect-task="${task.id}" class="danger">放弃</button>`;
        const completeBtnText = task.is_donation ? "提交捐献" : (canComplete ? "领取奖励" : "进行中");
        const completeBtn = `<button data-complete-sect-task="${task.id}" ${canComplete ? "" : "disabled"}>${completeBtnText}</button>`;
        return `<div class="row task-card"><div><strong>当前：${task.name}</strong><span>${task.description}</span><span>${task.requirement_display || `进度：${task.progress} / ${task.target}`}</span>${task.cost_display ? `<span style="color:#e5c568">${task.cost_display}</span>` : ""}${progressBar}</div>${completeBtn}${abandonBtn}</div>`;
      }).join("") : `<div class="empty">暂无进行中的宗门任务</div>`;
      
      const availableTasksHtml = availableSectTasks.length ? availableSectTasks.map(task => `<div class="row"><div><strong>${task.name}</strong><span>${task.description}</span><span>奖励：贡献 ${task.reward_contribution || task.reward?.contribution || 0} · 灵石 ${task.reward_stones || task.reward?.spirit_stones || 0}</span></div><button data-accept-sect-task="${task.code}">接取</button></div>`).join("") : "";
      sectTasks.innerHTML = `${currentTasksHtml}${availableTasksHtml ? `<div style="margin-top:10px"><strong style="color:#c8d2c1;font-size:13px">可接任务：</strong>${availableTasksHtml}</div>` : ""}`;
      
      sectShop.innerHTML = currentSectShop.length ? currentSectShop.map(item => `<div class="row"><div><strong>${item.name || item.item_name || getItemName(item.item_code)}</strong><span>${item.exchange_summary || `消耗 ${item.cost} 贡献：获得 ${item.item_name || getItemName(item.item_code)} x${item.quantity}`}</span></div><button data-exchange-sect-reward="${item.code}">兑换</button></div>`).join("") : `<div class="empty">暂无可兑换奖励</div>`;
    }
    
    sectList.innerHTML = sectCatalog.map(sect => `<div class="row"><div><strong>${sect.name} · ${sect.faction_name}</strong><span>${sect.description}</span><span>要求：${sect.required_realm} · 灵石 ${sect.required_spirit_stones || 0} · 偏好灵根 ${sect.preferred_root.join("、") || "不限"}</span></div><button data-join-sect="${sect.code}" ${currentSect?.sect ? "disabled" : ""}>拜入</button></div>`).join("");
  }

  // ========== 数据加载 ==========
  async function loadMe() {
    const data = await getCharacterMe();
    renderCharacter(data);
    renderAutoCultivation(data.character);
    await loadProgression();
    await loadSect();
    await loadLogs();
    await loadRecipes();
    await loadGoals();
    window.GameUI.showGame(true);
    if (getCurrentSkillTab()) renderRecipes(getCurrentSkillTab());
    startRealtimeLogPolling();
  }

  async function loadProgression() {
    const methods = await getMethods();
    const artifacts = await getArtifacts();
    window.GameCore.setCurrentMethods(methods);
    window.GameCore.setCurrentArtifacts(artifacts);
    renderProgression();
  }

  async function loadLogs() {
    const data = await getLogs(30);
    const logs = document.getElementById("logs");
    const recentLogs = document.getElementById("recent-logs");
    const items = data.length ? data.map(log => `<p><small>${new Date(log.created_at).toLocaleString()}</small><br />${log.content}</p>`).join("") : `<div class="empty">暂无日志</div>`;
    logs.innerHTML = items;
    recentLogs.innerHTML = data.slice(0, 5).length ? data.slice(0, 5).map(log => `<p>${log.content}</p>`).join("") : `<div class="empty">暂无游历记录</div>`;
  }

  async function loadSect() {
    const catalog = await getSects();
    const mySect = await getMySect();
    const tasks = mySect.sect ? await getSectTasks() : [];
    const myTasks = mySect.sect ? await getMySectTasks() : [];
    const shop = mySect.sect ? await getSectShop() : [];
    
    window.GameCore.setSectCatalog(catalog);
    window.GameCore.setCurrentSect(mySect);
    window.GameCore.setAvailableSectTasks(tasks);
    window.GameCore.setMySectTasks(myTasks);
    window.GameCore.setCurrentSectShop(shop);
    
    renderSect();
  }

  async function loadRecipes() {
    try {
      const recipes = await getRecipes();
      setFetchedRecipes(recipes);
    } catch (e) {
      showToast("配方加载失败：" + e.message);
    }
  }

  async function loadGoals() {
    const goalsPanel = document.getElementById("goals-panel");
    const goalsHiddenEntry = document.getElementById("goals-hidden-entry");
    const goalsShortTerm = document.getElementById("goals-short-term");
    const goalsLongTerm = document.getElementById("goals-long-term");
    
    if (isGoalsHidden()) {
      goalsPanel.classList.add("hidden");
      goalsHiddenEntry.classList.remove("hidden");
    } else {
      goalsPanel.classList.remove("hidden");
      goalsHiddenEntry.classList.add("hidden");
      try {
        const data = await getGoals();
        renderGoals(data.goals || []);
      } catch (e) {
        goalsShortTerm.innerHTML = "";
        goalsLongTerm.innerHTML = "";
      }
    }
  }

  // ========== 辅助函数 ==========
  function renderProgression() {
    const methods = window.GameCore.getCurrentMethods();
    const artifacts = window.GameCore.getCurrentArtifacts();
    const methodsList = document.getElementById("methods-list");
    const artifactsList = document.getElementById("artifacts-list");
    
    methodsList.innerHTML = methods.length ? methods.map(method =>
      `<div class="row"><div><strong>${method.name} ${method.equipped ? "· 主修" : ""}</strong><span>${method.level}层 · 经验 ${method.exp}${method.next_exp ? ` / ${method.next_exp}` : ""}</span></div><button data-method-equip="${method.id}" ${method.equipped ? "disabled" : ""}>主修</button><button data-method-practice="${method.id}" class="secondary">修炼</button></div>`
    ).join("") : `<div class="empty">尚未学习功法</div>`;
    
    artifactsList.innerHTML = artifacts.length ? artifacts.map(artifact =>
      `<div class="row"><div><strong>${artifact.rarity}品 ${artifact.name}</strong><span>强化 +${artifact.level} · ${artifact.equipped ? "已装备" : "未装备"}</span></div><button data-artifact-upgrade="${artifact.id}">强化</button><button data-artifact-unequip="${artifact.id}" class="secondary">卸下</button></div>`
    ).join("") : `<div class="empty">尚未装备法宝</div>`;
  }

  function _hasItem(code) {
    return getCurrentUser()?.inventory.some(i => i.code === code && i.quantity > 0) || false;
  }

  function getItemName(code) {
    return window.GameCore.getItemName(code);
  }

  // ========== Goals Panel 控制 ==========
  function isGoalsHidden() {
    const stored = localStorage.getItem("xiuxian_goals_hidden");
    return stored === null || stored === "true";
  }

  // ========== 实时日志轮询 ==========
  let _logPollTimer = null;

  function startRealtimeLogPolling() {
    if (_logPollTimer) clearInterval(_logPollTimer);
    _logPollTimer = setInterval(async () => {
      if (!window.GameCore.getToken()) return;
      try {
        const autoStatus = window.GameCore.getCurrentAutoStatus() || {};
        const enabled = autoStatus.enabled;

        if (enabled) {
          await window.GameAPI.executeTick();
        }

        const data = await window.GameAPI.getAutoCultivationStatus();
        const auto = data.auto_cultivation || {};
        window.GameCore.setCurrentAutoStatus(auto);

        const logsEl = document.getElementById("recent-logs");
        if (logsEl) {
          const realtimeLogs = auto.realtime_logs || [];
          if (realtimeLogs.length > 0) {
            logsEl.innerHTML = realtimeLogs.slice(-8).reverse().map(log =>
              `<p class="log-entry">${log}</p>`
            ).join("");
          }
        }

        const mattersEl = document.getElementById("auto-pending-matters");
        if (mattersEl) {
          const pausedReason = auto.paused_reason;
          const pendingMatters = auto.last_report?.pending_matters || [];
          if (pausedReason) {
            mattersEl.innerHTML = `<div class="pending-alert">
              <strong>⚠ 待处理：</strong>${pausedReason}
              <button id="auto-resume-btn-from-matter" class="secondary" style="margin-left:8px;min-height:28px;padding:0 8px;font-size:11px">处理后继续</button>
            </div>`;
            document.getElementById("auto-resume-btn-from-matter")?.addEventListener("click", () => doAutoResume());
          } else if (pendingMatters.length > 0) {
            mattersEl.innerHTML = `<div class="pending-alert">
              <strong>📋 待处理：</strong>${pendingMatters.join("；")}
            </div>`;
          } else if (enabled) {
            mattersEl.innerHTML = `<div style="font-size:13px;color:#8faa8f;padding:4px 0">自动修行中，一切平稳 ✦</div>`;
          } else {
            mattersEl.innerHTML = "";
          }
        }

        const stateEl = document.getElementById("auto-state-name");
        if (stateEl) {
          const stateName = auto.state_name || "未开启";
          stateEl.textContent = `${stateName}${auto.enabled ? "（进行中）" : "（已暂停）"}`;
        }
      } catch (e) {
        // 忽略轮询错误
      }
    }, 10000);
  }

  // ========== 公共接口 ==========
  return {
    doAction,
    doTrain,
    doExplore,
    doBreakthrough,
    doMeditate,
    doSpiritStone,
    doPill,
    doAutoConfig,
    doAutoSettle,
    doAutoPause,
    doAutoResume,
    renderRecipes,
    renderSect,
    loadMe,
    loadProgression,
    loadLogs,
    loadSect,
    loadRecipes,
    loadGoals,
    renderProgression,
    startRealtimeLogPolling,
  };
})();

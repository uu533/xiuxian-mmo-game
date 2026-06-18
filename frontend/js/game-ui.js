/**
 * UI 渲染和交互模块
 * 负责：面板渲染、Toast、叙事面板、Tooltip 初始化
 * 依赖：game-core.js, game-api.js
 */

window.GameUI = (function() {
  const { getCurrentUser, setCurrentUser, getItemName, getEffectTypeName, _formatEffectValue, _hasItem } = window.GameCore;
  const { executeAction, getCharacterMe, getMethods, getArtifacts, getLogs, getSects, getMySect, getSectTasks, getMySectTasks, getSectShop, getRecipes, getGoals } = window.GameAPI;

  // ========== Toast 提示功能 ==========
  const message = document.getElementById("message");

  function showToast(text, isSuccess = false) {
    const narrativeText = formatNarrativeToast(text);
    message.textContent = narrativeText || "";
    message.classList.toggle("hidden", !narrativeText);
    message.classList.toggle("success", isSuccess);
  }

  // ========== Toast 叙事性文本优化 ==========
  function formatNarrativeToast(originalText, result = null) {
    if (!originalText) return originalText;

    let match = originalText.match(/修炼成功[，,]修为\+(\d+)/);
    if (match) {
      return `你静坐吐纳，修为有所精进。（+${match[1]}）`;
    }

    match = originalText.match(/探索成功[，,]获得灵石\s*x\s*(\d+)/);
    if (match) {
      const num = parseInt(match[1]);
      const chineseNum = ['零', '一', '二', '三', '四', '五', '六', '七', '八', '九', '十'][num] || num;
      return `你在山石间有所发现，获得灵石${chineseNum}枚。`;
    }

    match = originalText.match(/突破成功/);
    if (match) {
      return `灵气贯通，瓶颈已破。你感受到了境界的突破——大道向前！`;
    }

    match = originalText.match(/突破失败[，,]修为-(\d+)%/);
    if (match) {
      return `突破未成，灵气反噬，修为有所亏损。（-${match[1]}%）`;
    }

    match = originalText.match(/加入宗门成功/);
    if (match && result && result.sect_name) {
      return `你正式拜入【${result.sect_name}】，从此有了依归。`;
    }

    return originalText;
  }

  // ========== 叙事面板功能 ==========
  let _narrativeCallback = null;
  let _typewriterTimer = null;
  let _typewriterDone = false;
  let _currentTextContainer = null;
  let _currentNarrativeText = "";

  function showNarrativePanel(text, mode = "popup", onComplete = null) {
    _narrativeCallback = onComplete;
    _typewriterDone = false;
    _currentNarrativeText = text;

    const overlay = document.getElementById("narrative-overlay");
    const fullscreen = document.getElementById("narrative-fullscreen");

    overlay.classList.add("hidden");
    fullscreen.classList.add("hidden");

    if (mode === "fullscreen") {
      fullscreen.classList.remove("hidden");
      _currentTextContainer = document.getElementById("narrative-fullscreen-text");
    } else {
      overlay.classList.remove("hidden");
      _currentTextContainer = document.getElementById("narrative-text");
    }

    _currentTextContainer.innerHTML = "";
    typewriterEffect(_currentTextContainer, text, 50);
  }

  function typewriterEffect(container, text, speed = 50, onComplete = null) {
    if (_typewriterTimer) {
      clearTimeout(_typewriterTimer);
    }

    let index = 0;
    let outputHtml = "";
    container.dataset.fullText = text;

    function type() {
      if (index < text.length) {
        if (text[index] === "\n") {
          outputHtml += "<br>";
        } else {
          outputHtml += text[index];
        }
        container.innerHTML = outputHtml;
        index++;
        _typewriterTimer = setTimeout(type, speed);
      } else {
        _typewriterTimer = null;
        _typewriterDone = true;
        if (onComplete) onComplete();
      }
    }

    type();
  }

  function skipTypewriter() {
    if (_typewriterTimer) {
      clearTimeout(_typewriterTimer);
      _typewriterTimer = null;
    }
    const container = _currentTextContainer || document.getElementById("narrative-text") || document.getElementById("narrative-fullscreen-text");
    const fullText = container?.dataset.fullText || "";
    if (container && fullText) {
      container.innerHTML = fullText.replace(/\n/g, "<br>");
    }
    _typewriterDone = true;
  }

  function closeNarrativePanel() {
    document.getElementById("narrative-overlay").classList.add("hidden");
    document.getElementById("narrative-fullscreen").classList.add("hidden");

    document.querySelectorAll("button").forEach(btn => {
      btn.disabled = false;
    });

    if (_narrativeCallback) {
      const callback = _narrativeCallback;
      _narrativeCallback = null;
      callback();
    }
  }

  // ========== 技能界面文案优化 ==========
  const SKILL_TEXTS_OPTIMIZED = {
    alchemy: {
      tabName: "炼丹",
      panelTitle: "丹房",
      intro: "以灵草为引，以灵火为媒，\n将天地灵气炼入丹药之中。\n\n一颗好丹，可抵三年苦修。",
      materialLabel: "药材",
      outputLabel: "成丹",
    },
    talisman: {
      tabName: "符箓",
      panelTitle: "符阁",
      intro: "以灵力为墨，以符纸为媒，\n将一丝天地法则封入方寸之间。\n\n一张好符，可救燃眉之急。",
      materialLabel: "符材",
      outputLabel: "成符",
    },
    crafting: {
      tabName: "炼器",
      panelTitle: "炼器室",
      intro: "以天地矿物为骨，以灵火为魂，\n锻造出承载灵力的法器。\n\n一件好法宝，可伴你一生。",
      materialLabel: "矿材",
      outputLabel: "成器",
    },
    formation: {
      tabName: "阵法",
      panelTitle: "阵台",
      intro: "以灵石为眼，以天地为盘，\n布下借天地之力的阵法。\n\n一座好阵，可护一方平安。",
      materialLabel: "阵材",
      outputLabel: "成阵",
    },
  };

  // ========== 行动按钮提示优化 ==========
  const ACTION_TOOLTIPS = {
    train: {
      name: "吐纳",
      cost: "耗法力 12",
      desc: "盘膝静坐，导引灵气入体，\n积累修为，夯实根基。",
    },
    explore: {
      name: "游历",
      cost: "耗法力 18",
      desc: "踏入山野，探索机缘，\n也可能遭遇危险——\n修行路上，风险与机遇并存。",
    },
    breakthrough: {
      name: "叩关",
      cost: "耗法力 35",
      desc: "以全部修为冲击当前境界的瓶颈。\n\n成功则境界突破，大道向前；\n失败则修为亏损，需重新积累。\n\n——叩关需谨慎。",
    },
    meditate: {
      name: "调息",
      desc: "不修炼，不探索，\n只是安静地呼吸，\n让法力慢慢恢复。",
    },
    "spirit-stone": {
      name: "吸灵石",
      desc: "消耗灵石，换取法力恢复。\n\n这是用'钱'换'时间'——\n富人常用，穷人慎用。",
    },
    pill: {
      name: "服丹",
      desc: "服用丹药恢复法力。\n\n比吸灵石温和，\n但丹药有限，需节约使用。",
    },
  };

  // ========== P2-1: Hover 提示升级（MUI Tooltip）=新增功能 ==========
  // 由于当前是 Vanilla JS，创建一个轻量级的 Tooltip 实现
  let tooltipInitialized = false;

  function initTooltips() {
    if (tooltipInitialized) return;
    
    // 为所有带有 data-tooltip 属性的元素初始化 Tooltip
    document.querySelectorAll('[data-tooltip]').forEach(element => {
      const tooltipText = element.getAttribute('data-tooltip');
      if (tooltipText) {
        addTooltip(element, tooltipText);
      }
    });

    // 为资源条等特定元素添加 Tooltip
    initResourceTooltips();
    
    // 为行动按钮添加 Tooltip
    initActionButtonTooltips();

    tooltipInitialized = true;
  }

  function addTooltip(element, tooltipText, options = {}) {
    // 创建自定义 Tooltip（轻量级，不依赖 React）
    const tooltip = document.createElement('div');
    tooltip.className = 'custom-tooltip';
    tooltip.textContent = tooltipText;
    tooltip.style.cssText = `
      position: absolute;
      background: rgba(0, 0, 0, 0.87);
      color: #f6eed9;
      padding: 8px 12px;
      border-radius: 4px;
      font-size: 12px;
      max-width: 300px;
      z-index: 9999;
      pointer-events: none;
      opacity: 0;
      transition: opacity 0.3s;
      box-shadow: 0 2px 8px rgba(0,0,0,0.3);
    `;
    
    document.body.appendChild(tooltip);

    let enterDelay = options.enterDelay || 500;
    let showTimeout = null;

    element.addEventListener('mouseenter', (e) => {
      showTimeout = setTimeout(() => {
        const rect = element.getBoundingClientRect();
        tooltip.style.left = `${rect.left + rect.width / 2 - tooltip.offsetWidth / 2}px`;
        tooltip.style.top = `${rect.top - tooltip.offsetHeight - 8}px`;
        tooltip.style.opacity = '1';
      }, enterDelay);
    });

    element.addEventListener('mouseleave', () => {
      if (showTimeout) {
        clearTimeout(showTimeout);
        showTimeout = null;
      }
      tooltip.style.opacity = '0';
    });

    // 存储 tooltip 引用以便清理
    element._tooltip = tooltip;
  }

  function initResourceTooltips() {
    // 资源条 tooltip
    const manaStat = document.querySelector('#res-mana');
    if (manaStat) {
      const parentStat = manaStat.closest('.stat');
      if (parentStat) {
        parentStat.setAttribute('data-tooltip', '法力：行动所需，可调息、吸灵石或服丹药恢复');
      }
    }

    const hpStat = document.querySelector('#res-hp');
    if (hpStat) {
      const parentStat = hpStat.closest('.stat');
      if (parentStat) {
        parentStat.setAttribute('data-tooltip', '气血：生命之本，归零则道消');
      }
    }
  }

  function initActionButtonTooltips() {
    // 行动按钮 tooltip
    const actionButtons = {
      'train-btn': '吐纳：静坐修炼，提升修为（耗法力 12）',
      'explore-btn': '游历：踏入山野，探索机缘（耗法力 18）',
      'breakthrough-btn': '叩关：冲击瓶颈，大道向前（耗法力 35）',
      'meditate-btn': '调息：安静呼吸，恢复法力',
      'spirit-stone-btn': '吸灵石：消耗灵石，换取法力',
      'pill-btn': '服丹：服用丹药，恢复法力',
    };

    Object.entries(actionButtons).forEach(([btnId, tooltip]) => {
      const btn = document.getElementById(btnId);
      if (btn) {
        btn.setAttribute('data-tooltip', tooltip);
      }
    });
  }

  // ========== P2-2: 文案过长处理 =新增功能 ==========
  function addEllipsisWithTooltip(element, maxWidth, maxLines = 1) {
    // 检查文本是否过长
    const checkOverflow = () => {
      if (maxLines === 1) {
        // 单行省略
        if (element.scrollWidth > (maxWidth || element.clientWidth)) {
          element.classList.add('text-ellipsis');
          const fullText = element.textContent;
          if (!element.hasAttribute('data-tooltip')) {
            element.setAttribute('data-tooltip', fullText);
            addTooltip(element, fullText);
          }
        }
      } else {
        // 多行省略
        element.classList.add('text-ellipsis-multiline');
        element.style.setProperty('-webkit-line-clamp', maxLines);
        const fullText = element.textContent;
        if (!element.hasAttribute('data-tooltip')) {
          element.setAttribute('data-tooltip', fullText);
          addTooltip(element, fullText, { enterDelay: 300 });
        }
      }
    };

    // 延迟检查（等待渲染完成）
    setTimeout(checkOverflow, 100);
  }

  // ========== 游戏 UI 显示控制 ==========
  const authSection = document.getElementById("auth-section");
  const gameUi = document.getElementById("game-ui");
  const tabs = document.getElementById("tabs");

  function showGame(loggedIn) {
    authSection.classList.toggle("hidden", loggedIn);
    gameUi.classList.toggle("hidden", !loggedIn);
    tabs.classList.toggle("hidden", !loggedIn);
  }

  // ========== 角色信息渲染 ==========
  function renderCharacter(data) {
    setCurrentUser(data);
    const c = data.character;
    window.GameCore.setCurrentActiveEffects(c.active_effects || []);

    document.getElementById("hero-name").textContent = `${data.username} ${c.title}`;
    document.getElementById("hero-realm").textContent = `${c.realm}`;
    document.getElementById("hero-subtitle").textContent = `${c.spiritual_root} · ${c.age}岁 · ${c.identity_status}`;
    document.getElementById("hero-pill").textContent = `法力 ${c.mana}/${c.max_mana}`;
    document.getElementById("res-cultivation").textContent = `${c.cultivation} / ${c.cultivation_cap}`;
    document.getElementById("res-stones").textContent = c.spirit_stones;
    document.getElementById("res-mana").textContent = `${c.mana} / ${c.max_mana}`;
    document.getElementById("res-hp").textContent = `${c.hp} / ${c.max_hp} · ${c.life_status}`;
    
    const isDead = c.hp <= 0;
    document.getElementById("train-btn").disabled = isDead || c.mana < 12;
    document.getElementById("explore-btn").disabled = isDead || c.mana < 18;
    document.getElementById("breakthrough-btn").disabled = isDead || c.mana < 35;
    document.getElementById("meditate-btn").disabled = isDead || c.mana >= c.max_mana;
    document.getElementById("spirit-stone-btn").disabled = isDead || c.spirit_stones < 10 || c.mana >= c.max_mana;
    document.getElementById("pill-btn").disabled = isDead || !data.inventory.some(item => item.code === "mana_pill" && item.quantity > 0) || c.mana >= c.max_mana;

    // 应用 P2-2: 文案过长处理
    addEllipsisWithTooltip(document.getElementById("hero-name"), 200);
    addEllipsisWithTooltip(document.getElementById("hero-subtitle"), 250);

    // 继续渲染...
    renderCharacterDetails(data);
    renderInventory(data);
    renderActiveEffects();
  }

  function renderCharacterDetails(data) {
    const c = data.character;
    const grid = document.getElementById("character-grid");
    const playerTitle = document.getElementById("player-title");
    const fullTitleName = document.getElementById("full-title-name");
    const titleSelect = document.getElementById("title-select");

    playerTitle.textContent = `角色：${data.username} ${c.title}`;
    fullTitleName.textContent = `${data.username} ${c.title}`;
    titleSelect.innerHTML = c.unlocked_titles.map(t => `<option value="${t}">${t}</option>`).join("");
    titleSelect.value = c.title;

    // Debug info
    document.getElementById("dbg-realm").textContent = c.realm;
    const usedSlots = data.inventory.filter(i => i.name).length;
    const totalSlots = data.inventory.length || 36;
    document.getElementById("dbg-bag").textContent = `${usedSlots}/${totalSlots}`;
    document.getElementById("dbg-contribution").textContent = c.sect_position?.contribution || "无宗门";

    const stats = [
      ["境界", c.realm], ["修为", `${c.cultivation} / ${c.cultivation_cap}`],
      ["灵根", c.spiritual_root, true], ["年龄", c.age],
      ["身份", c.identity_status], ["宗门地位", c.sect_position || "散修"],
      ["寿元", c.lifespan], ["气血", `${c.hp} / ${c.max_hp}（0则死亡）`],
      ["生命状态", c.life_status], ["法力", `${c.mana} / ${c.max_mana}`],
      ["攻击", `${c.attack}（基础${c.base_attack}+加成${c.attack_bonus}）`],
      ["防御", `${c.defense}（基础${c.base_defense}+加成${c.defense_bonus}）`],
      ["突破率", `${Math.round(c.breakthrough_rate * 100)}%`],
      ["灵石", c.spirit_stones],
    ];

    grid.innerHTML = stats.map(([label, value, hasHelp]) => {
      const valueHtml = hasHelp ? `<div class="root-line"><strong>${value}</strong><button class="help-btn" id="root-help-btn" title="查看灵根说明">?</button></div>` : `<strong>${value}</strong>`;
      return `<div class="mini-stat"><span>${label}</span>${valueHtml}</div>`;
    }).join("");
  }

  function renderInventory(data) {
    const inventory = document.getElementById("inventory");
    inventory.innerHTML = `<div class="bag-grid">${data.inventory.map(item => {
      if (!item.name) return `<div class="bag-slot empty-slot"><span>${item.slot_index}</span></div>`;
      const actionBtn = (() => {
        if (item.type === "cultivation_method") return `<button data-slot-action="learn_method" data-slot-index="${item.slot_index}">学习</button>`;
        if (item.type === "magic_artifact") return `<button data-slot-action="equip_artifact" data-slot-index="${item.slot_index}">装备</button>`;
        if (item.type === "pill" || item.type === "talisman") return `<button data-slot-action="use_item" data-slot-index="${item.slot_index}">${item.type === "pill" ? "服用" : "使用"}</button>`;
        return "";
      })();
      return `<div class="bag-slot" title="${item.name} x${item.quantity}"><strong>${item.name}</strong><span>x${item.quantity}</span>${actionBtn}</div>`;
    }).join("")}</div>`;

    // P2-2: 对物品名称应用省略号
    inventory.querySelectorAll('.bag-slot strong').forEach(el => {
      addEllipsisWithTooltip(el, 80);
    });
  }

  function renderActiveEffects() {
    const effects = window.GameCore.getCurrentActiveEffects() || [];
    const validEffects = effects.filter(e => e.remaining_uses > 0);

    const charEffectList = document.getElementById("active-effects-list");
    const countEl = document.getElementById("effect-count");
    if (countEl) countEl.textContent = `${validEffects.length} 个有效`;

    if (validEffects.length === 0) {
      charEffectList.innerHTML = `<div class="empty">暂无临时效果</div>`;
    } else {
      charEffectList.innerHTML = validEffects.map(e => `
        <div class="effect-card">
          <div class="effect-name">${e.effect_name || getEffectTypeName(e.effect_type)}</div>
          <div class="effect-detail">来源：${e.source_name || getItemName(e.source_item_or_recipe)} · 剩余：${e.remaining_uses}次 · 数值：${_formatEffectValue(e.value)}</div>
        </div>
      `).join("");
    }
  }

  // ========== 自动修行渲染 ==========
  function renderAutoCultivation(c) {
    const auto = c.auto_cultivation || {};
    window.GameCore.setCurrentAutoStatus(auto);

    const stateName = auto.state_name || "未开启";
    const strategyName = auto.strategy_name || "未选择";
    const enabled = auto.enabled;

    document.getElementById("auto-state-name").textContent = `${stateName}${enabled ? "（进行中）" : "（已暂停）"}`;
    document.getElementById("auto-strategy-name").textContent = `策略：${strategyName}`;

    // 待处理事项
    const mattersEl = document.getElementById("auto-pending-matters");
    const pendingMatters = auto.last_report?.pending_matters || [];
    const realtimeLogs = auto.realtime_logs || [];
    
    if (auto.paused_reason) {
      mattersEl.innerHTML = `<div class="pending-alert">
        <strong>⚠ 待处理：</strong>${auto.paused_reason}
        <button id="auto-resume-btn-from-matter" class="secondary" style="margin-left:8px;min-height:28px;padding:0 8px;font-size:11px">处理后继续</button>
      </div>`;
      document.getElementById("auto-resume-btn-from-matter")?.addEventListener("click", () => window.GameActions.doAutoResume());
    } else if (pendingMatters.length > 0) {
      mattersEl.innerHTML = `<div class="pending-alert">
        <strong>📋 待处理：</strong>${pendingMatters.join("；")}
      </div>`;
    } else if (enabled) {
      mattersEl.innerHTML = `<div style="font-size:13px;color:#8faa8f;padding:4px 0">自动修行中，一切平稳 ✦</div>`;
    } else {
      mattersEl.innerHTML = "";
    }

    // 实时日志
    const logsEl = document.getElementById("recent-logs");
    if (realtimeLogs.length > 0) {
      logsEl.innerHTML = realtimeLogs.slice(-8).reverse().map(log =>
        `<p class="log-entry">${log}</p>`
      ).join("");
    } else if (enabled) {
      logsEl.innerHTML = `<p class="log-entry" style="color:#8faa8f">自动修行中，静候佳音...</p>`;
    }

    // 更新控制按钮状态
    const startBtn = document.getElementById("auto-start-btn");
    const settleBtn = document.getElementById("auto-settle-btn");
    const pauseBtn = document.getElementById("auto-pause-btn");
    const resumeBtn = document.getElementById("auto-resume-btn");

    startBtn.disabled = enabled;
    settleBtn.disabled = !auto.can_settle;
    pauseBtn.disabled = !enabled;
  }

  // ========== 目标建议渲染 ==========
  function renderGoals(goals) {
    const goalsShortTerm = document.getElementById("goals-short-term");
    const goalsLongTerm = document.getElementById("goals-long-term");
    
    const shortGoals = goals.filter(g => g.category === "short_term");
    const longGoals = goals.filter(g => g.category === "long_term");

    goalsShortTerm.innerHTML = shortGoals.length
      ? `<div class="goals-section-title">短期建议</div>` + shortGoals.map(g => goalCardHtml(g)).join("")
      : "";
    goalsLongTerm.innerHTML = longGoals.length
      ? `<div class="goals-section-title">长期建议</div>` + longGoals.map(g => goalCardHtml(g)).join("")
      : "";
  }

  function goalCardHtml(goal) {
    return `<div class="goal-card">
      <div class="goal-title">${goal.title}</div>
      <div class="goal-reason">${goal.reason}</div>
      ${goal.progress_text ? `<div class="goal-progress">${goal.progress_text}</div>` : ""}
      ${goal.requirements && goal.requirements.length ? `<div class="goal-requirements">${goal.requirements.join("；")}</div>` : ""}
      <div class="goal-action">${goal.recommended_action}</div>
      <div class="goal-benefits">${goal.benefits}</div>
    </div>`;
  }

  // ========== 公共接口 ==========
  return {
    showToast,
    formatNarrativeToast,
    showNarrativePanel,
    skipTypewriter,
    closeNarrativePanel,
    initTooltips,
    addTooltip,
    addEllipsisWithTooltip,
    showGame,
    renderCharacter,
    renderCharacterDetails,
    renderInventory,
    renderActiveEffects,
    renderAutoCultivation,
    renderGoals,
    SKILL_TEXTS_OPTIMIZED,
    ACTION_TOOLTIPS,
  };
})();

// Shared ElevenLabs widget loader for the tutor and orientation pages.
// Agent IDs are filled in by agents/create_agents.py (or by hand) after the agents exist.
window.TUTEUR_CONFIG = {
  agents: {
    histoire: "",
    maths: "",
    francais: "",
    orientation: "",
  },
  widgetSrc: "https://unpkg.com/@elevenlabs/convai-widget-embed@0.19.0/dist/index.js",
};

(function () {
  let loaded = false;
  function loadScript() {
    if (loaded) return;
    loaded = true;
    const s = document.createElement("script");
    s.src = window.TUTEUR_CONFIG.widgetSrc;
    s.async = true;
    document.head.appendChild(s);
  }

  // Mounts one widget in `slot`, replacing any previous one.
  // vars: dynamic variables (all strings). opts.voiceId: voice override. opts.clientTools: {name: fn}.
  window.monterVoix = function (slot, key, vars, opts = {}) {
    slot.innerHTML = "";
    const id = window.TUTEUR_CONFIG.agents[key];
    if (!id) {
      slot.innerHTML = '<p class="warn">Ce personnage n\'est pas encore branché à sa voix (identifiant d\'agent manquant dans assets/voix.js).</p>';
      return null;
    }
    loadScript();
    const w = document.createElement("elevenlabs-convai");
    w.setAttribute("agent-id", id);
    const clean = {};
    for (const [k, v] of Object.entries(vars || {})) clean[k] = String(v ?? "").slice(0, 400);
    w.setAttribute("dynamic-variables", JSON.stringify(clean));
    if (opts.voiceId) w.setAttribute("override-voice-id", opts.voiceId);
    w.setAttribute("variant", "full");
    w.setAttribute("placement", "bottom-right");
    if (opts.expanded) w.setAttribute("default-expanded", "true");
    if (opts.clientTools) {
      w.addEventListener("elevenlabs-convai:call", (e) => {
        e.detail.config.clientTools = Object.assign({}, e.detail.config.clientTools, opts.clientTools);
      });
    }
    slot.appendChild(w);
    return w;
  };

  window.paramsURL = function () {
    const p = new URLSearchParams(location.search);
    const o = {};
    for (const [k, v] of p.entries()) o[k] = v;
    return o;
  };
})();

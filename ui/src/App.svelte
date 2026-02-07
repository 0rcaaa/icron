<script>
  import { onMount } from 'svelte';

  let loading = true;
  let saving = false;
  let error = '';
  let status = 'idle';
  let config = null;
  let rawJson = '';
  let rawDirty = false;
  let lastSaved = '';
  let activeTab = 'models';

  // Test connection states
  let testStates = {
    default: { testing: false, result: null },
    openrouter: { testing: false, result: null },
    together: { testing: false, result: null },
    anthropic: { testing: false, result: null },
    openai: { testing: false, result: null },
    gemini: { testing: false, result: null },
    vllm: { testing: false, result: null },
    groq: { testing: false, result: null },
    discord: { testing: false, result: null },
    telegram: { testing: false, result: null },
    whatsapp: { testing: false, result: null }
  };

  // MCP runtime status (fetched from /api/mcp/status)
  let mcpStatus = { initialized: false, totalTools: 0, servers: [] };
  let mcpStatusLoading = false;

  const tabs = [
    { id: 'models', label: 'Models' },
    { id: 'channels', label: 'Channels' },
    { id: 'memory', label: 'Memory' },
    { id: 'tools', label: 'Tools' },
    { id: 'mcp', label: 'MCP' },
    { id: 'raw', label: 'Raw Config' }
  ];

  // New MCP server form
  let newMcpServer = {
    name: '',
    transport: 'stdio',
    command: '',
    args: '',
    url: '',
    headers: ''
  };

  let form = {
    model: '',
    // Provider enables
    openrouterEnabled: false,
    togetherEnabled: false,
    anthropicEnabled: false,
    openaiEnabled: false,
    geminiEnabled: false,
    vllmEnabled: false,
    groqEnabled: false,
    // OpenRouter
    openrouterApiKey: '',
    openrouterApiBase: '',
    openrouterModel: '',
    // Together
    togetherApiKey: '',
    togetherApiBase: '',
    togetherModel: '',
    // Anthropic
    anthropicApiKey: '',
    anthropicApiBase: '',
    anthropicModel: '',
    // OpenAI
    openaiApiKey: '',
    openaiApiBase: '',
    openaiModel: '',
    // Gemini
    geminiApiKey: '',
    geminiApiBase: '',
    geminiModel: '',
    // vLLM
    vllmApiKey: '',
    vllmApiBase: '',
    vllmModel: '',
    // Groq
    groqApiKey: '',
    groqApiBase: '',
    groqModel: '',
    // Tools
    websearchApiKey: '',
    restrictToWorkspace: false,
    maxContextTokens: 100000,
    // Channels
    telegramEnabled: false,
    telegramToken: '',
    telegramAllowFrom: '',
    whatsappEnabled: false,
    whatsappAllowFrom: '',
    whatsappBridgeUrl: '',
    discordEnabled: false,
    discordToken: '',
    discordAllowFrom: '',
    discordAllowedChannels: '',
    // MCP
    mcpEnabled: false
  };

  // Track MCP servers separately for editing
  let mcpServers = {};

  // MCP Presets - popular servers users can enable with one click
  const mcpPresets = [
    // === File & Data ===
    {
      id: 'filesystem',
      name: 'Filesystem',
      description: 'Read, write, and manage files on the local system',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-filesystem', '/'],
      requiresApiKey: false,
      category: 'files'
    },
    {
      id: 'sqlite',
      name: 'SQLite',
      description: 'Query and manage SQLite databases locally',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-sqlite'],
      requiresApiKey: false,
      category: 'data'
    },
    {
      id: 'postgres',
      name: 'PostgreSQL',
      description: 'Query and manage PostgreSQL databases',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-postgres'],
      requiresApiKey: true,
      apiKeyEnv: 'POSTGRES_CONNECTION_STRING',
      apiKeyPlaceholder: 'postgresql://user:pass@host:5432/db',
      category: 'data'
    },
    // === Web & Search ===
    {
      id: 'fetch',
      name: 'Web Fetch',
      description: 'Simple HTTP fetch for web content',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', 'mcp-fetch-server'],
      requiresApiKey: false,
      category: 'web'
    },
    {
      id: 'brave-search',
      name: 'Brave Search',
      description: 'Search the web using Brave Search API',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-brave-search'],
      requiresApiKey: true,
      apiKeyEnv: 'BRAVE_API_KEY',
      apiKeyPlaceholder: 'BSA...',
      category: 'web'
    },
    {
      id: 'exa',
      name: 'Exa Search',
      description: 'AI-powered semantic search engine',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@exa-labs/mcp-exa'],
      requiresApiKey: true,
      apiKeyEnv: 'EXA_API_KEY',
      apiKeyPlaceholder: 'exa-...',
      category: 'web'
    },
    {
      id: 'puppeteer',
      name: 'Puppeteer',
      description: 'Browser automation and web scraping',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-puppeteer'],
      requiresApiKey: false,
      category: 'web'
    },
    // === Developer Tools ===
    {
      id: 'github',
      name: 'GitHub',
      description: 'Interact with GitHub repositories, issues, and PRs',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-github'],
      requiresApiKey: true,
      apiKeyEnv: 'GITHUB_PERSONAL_ACCESS_TOKEN',
      apiKeyPlaceholder: 'ghp_...',
      category: 'dev'
    },
    {
      id: 'gitlab',
      name: 'GitLab',
      description: 'Manage GitLab projects, MRs, and issues',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-gitlab'],
      requiresApiKey: true,
      apiKeyEnv: 'GITLAB_PERSONAL_ACCESS_TOKEN',
      apiKeyPlaceholder: 'glpat-...',
      category: 'dev'
    },
    {
      id: 'sentry',
      name: 'Sentry',
      description: 'Monitor errors and performance issues',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-sentry'],
      requiresApiKey: true,
      apiKeyEnv: 'SENTRY_AUTH_TOKEN',
      apiKeyPlaceholder: 'sntrys_...',
      category: 'dev'
    },
    {
      id: 'linear',
      name: 'Linear',
      description: 'Issue tracking and project management',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-linear'],
      requiresApiKey: true,
      apiKeyEnv: 'LINEAR_API_KEY',
      apiKeyPlaceholder: 'lin_api_...',
      category: 'dev'
    },
    // === Productivity ===
    {
      id: 'slack',
      name: 'Slack',
      description: 'Send messages and interact with Slack',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-slack'],
      requiresApiKey: true,
      apiKeyEnv: 'SLACK_BOT_TOKEN',
      apiKeyPlaceholder: 'xoxb-...',
      category: 'productivity'
    },
    {
      id: 'notion',
      name: 'Notion',
      description: 'Access and manage Notion workspaces',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-notion'],
      requiresApiKey: true,
      apiKeyEnv: 'NOTION_API_KEY',
      apiKeyPlaceholder: 'ntn_...',
      category: 'productivity'
    },
    {
      id: 'google-drive',
      name: 'Google Drive',
      description: 'Access and search Google Drive files',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-gdrive'],
      requiresApiKey: true,
      apiKeyEnv: 'GDRIVE_CREDENTIALS',
      apiKeyPlaceholder: 'Path to credentials JSON',
      category: 'productivity'
    },
    {
      id: 'google-maps',
      name: 'Google Maps',
      description: 'Location search, directions, and places',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-google-maps'],
      requiresApiKey: true,
      apiKeyEnv: 'GOOGLE_MAPS_API_KEY',
      apiKeyPlaceholder: 'AIza...',
      category: 'productivity'
    },
    // === AI & Tools ===
    {
      id: 'everart',
      name: 'EverArt',
      description: 'AI image generation and editing',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-everart'],
      requiresApiKey: true,
      apiKeyEnv: 'EVERART_API_KEY',
      apiKeyPlaceholder: 'ea_...',
      category: 'ai'
    },
    {
      id: 'time',
      name: 'Time',
      description: 'Get current time with timezone support',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@guanxiong/mcp-server-time'],
      requiresApiKey: false,
      category: 'tools'
    },
    {
      id: 'sequential-thinking',
      name: 'Sequential Thinking',
      description: 'Step-by-step reasoning and problem solving',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-sequential-thinking'],
      requiresApiKey: false,
      category: 'ai'
    },
    // === Cloud & Infrastructure ===
    {
      id: 'cloudflare',
      name: 'Cloudflare',
      description: 'Manage Workers, KV, R2, and DNS',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@cloudflare/mcp-server-cloudflare'],
      requiresApiKey: true,
      apiKeyEnv: 'CLOUDFLARE_API_TOKEN',
      apiKeyPlaceholder: 'cf_...',
      category: 'cloud'
    },
    {
      id: 'aws-kb',
      name: 'AWS Bedrock KB',
      description: 'Query AWS Bedrock knowledge bases',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@modelcontextprotocol/server-aws-kb-retrieval'],
      requiresApiKey: true,
      apiKeyEnv: 'AWS_ACCESS_KEY_ID',
      apiKeyPlaceholder: 'AKIA...',
      category: 'cloud'
    },
    // === Communication ===
    {
      id: 'discord-mcp',
      name: 'Discord',
      description: 'Send messages and manage Discord servers',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', 'mcp-discord'],
      requiresApiKey: true,
      apiKeyEnv: 'DISCORD_BOT_TOKEN',
      apiKeyPlaceholder: 'MTI...',
      category: 'communication'
    },
    {
      id: 'email',
      name: 'Email (IMAP)',
      description: 'Read and search emails via IMAP',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@anthropics/mcp-server-email'],
      requiresApiKey: true,
      apiKeyEnv: 'EMAIL_PASSWORD',
      apiKeyPlaceholder: 'app password',
      category: 'communication'
    },
    // === Knowledge & Research ===
    {
      id: 'arxiv',
      name: 'arXiv',
      description: 'Search academic papers on arXiv',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@mzxrai/mcp-arxiv'],
      requiresApiKey: false,
      category: 'research'
    },
    {
      id: 'wikipedia',
      name: 'Wikipedia',
      description: 'Search and read Wikipedia articles',
      transport: 'stdio',
      command: 'npx',
      args: ['-y', '@anthropic/mcp-server-wikipedia'],
      requiresApiKey: false,
      category: 'research'
    }
  ];

  // Track preset enabled states and API keys
  let presetStates = {};
  mcpPresets.forEach(p => {
    presetStates[p.id] = { enabled: false, apiKey: '' };
  });

  // MCP preset search/filter
  let mcpSearch = '';
  $: filteredPresets = mcpSearch
    ? mcpPresets.filter(p => p.name.toLowerCase().includes(mcpSearch.toLowerCase()) || p.description.toLowerCase().includes(mcpSearch.toLowerCase()))
    : mcpPresets;

  const apiUrl = '/api/config';

  const clone = (obj) => {
    if (typeof structuredClone === 'function') return structuredClone(obj);
    return JSON.parse(JSON.stringify(obj));
  };

  const toCsv = (list) => (Array.isArray(list) ? list.join(', ') : '');
  const toList = (value) =>
    value
      .split(',')
      .map((item) => item.trim())
      .filter(Boolean);

  const safeGet = (obj, path, fallback) => {
    let cur = obj;
    for (const key of path) {
      if (!cur || typeof cur !== 'object' || !(key in cur)) return fallback;
      cur = cur[key];
    }
    return cur ?? fallback;
  };

  const hasApiKey = (cfg, provider) => {
    return !!safeGet(cfg, ['providers', provider, 'apiKey'], '');
  };

  const initForm = (cfg) => {
    // Determine if providers are enabled based on having an API key
    form = {
      model: safeGet(cfg, ['agents', 'defaults', 'model'], ''),
      // Provider enables - true if they have an API key set
      openrouterEnabled: hasApiKey(cfg, 'openrouter'),
      togetherEnabled: hasApiKey(cfg, 'together'),
      anthropicEnabled: hasApiKey(cfg, 'anthropic'),
      openaiEnabled: hasApiKey(cfg, 'openai'),
      geminiEnabled: hasApiKey(cfg, 'gemini'),
      vllmEnabled: hasApiKey(cfg, 'vllm'),
      groqEnabled: hasApiKey(cfg, 'groq'),
      // OpenRouter
      openrouterApiKey: safeGet(cfg, ['providers', 'openrouter', 'apiKey'], ''),
      openrouterApiBase: safeGet(cfg, ['providers', 'openrouter', 'apiBase'], ''),
      openrouterModel: safeGet(cfg, ['providers', 'openrouter', 'model'], ''),
      // Together
      togetherApiKey: safeGet(cfg, ['providers', 'together', 'apiKey'], ''),
      togetherApiBase: safeGet(cfg, ['providers', 'together', 'apiBase'], ''),
      togetherModel: safeGet(cfg, ['providers', 'together', 'model'], ''),
      // Anthropic
      anthropicApiKey: safeGet(cfg, ['providers', 'anthropic', 'apiKey'], ''),
      anthropicApiBase: safeGet(cfg, ['providers', 'anthropic', 'apiBase'], ''),
      anthropicModel: safeGet(cfg, ['providers', 'anthropic', 'model'], ''),
      // OpenAI
      openaiApiKey: safeGet(cfg, ['providers', 'openai', 'apiKey'], ''),
      openaiApiBase: safeGet(cfg, ['providers', 'openai', 'apiBase'], ''),
      openaiModel: safeGet(cfg, ['providers', 'openai', 'model'], ''),
      // Gemini
      geminiApiKey: safeGet(cfg, ['providers', 'gemini', 'apiKey'], ''),
      geminiApiBase: safeGet(cfg, ['providers', 'gemini', 'apiBase'], ''),
      geminiModel: safeGet(cfg, ['providers', 'gemini', 'model'], ''),
      // vLLM
      vllmApiKey: safeGet(cfg, ['providers', 'vllm', 'apiKey'], ''),
      vllmApiBase: safeGet(cfg, ['providers', 'vllm', 'apiBase'], ''),
      vllmModel: safeGet(cfg, ['providers', 'vllm', 'model'], ''),
      // Groq
      groqApiKey: safeGet(cfg, ['providers', 'groq', 'apiKey'], ''),
      groqApiBase: safeGet(cfg, ['providers', 'groq', 'apiBase'], ''),
      groqModel: safeGet(cfg, ['providers', 'groq', 'model'], ''),
      // Tools
      websearchApiKey: safeGet(cfg, ['tools', 'web', 'search', 'apiKey'], ''),
      restrictToWorkspace: !!safeGet(cfg, ['tools', 'exec', 'restrictToWorkspace'], false),
      maxContextTokens: safeGet(cfg, ['tools', 'exec', 'maxContextTokens'], 100000),
      // Channels
      telegramEnabled: !!safeGet(cfg, ['channels', 'telegram', 'enabled'], false),
      telegramToken: safeGet(cfg, ['channels', 'telegram', 'token'], ''),
      telegramAllowFrom: toCsv(safeGet(cfg, ['channels', 'telegram', 'allowFrom'], [])),
      whatsappEnabled: !!safeGet(cfg, ['channels', 'whatsapp', 'enabled'], false),
      whatsappAllowFrom: toCsv(safeGet(cfg, ['channels', 'whatsapp', 'allowFrom'], [])),
      whatsappBridgeUrl: safeGet(cfg, ['channels', 'whatsapp', 'bridgeUrl'], ''),
      discordEnabled: !!safeGet(cfg, ['channels', 'discord', 'enabled'], false),
      discordToken: safeGet(cfg, ['channels', 'discord', 'token'], ''),
      discordAllowFrom: toCsv(safeGet(cfg, ['channels', 'discord', 'allowFrom'], [])),
      discordAllowedChannels: toCsv(safeGet(cfg, ['channels', 'discord', 'allowedChannels'], [])),
      // MCP
      mcpEnabled: !!safeGet(cfg, ['tools', 'mcp', 'enabled'], false)
    };
    // Load MCP servers
    mcpServers = clone(safeGet(cfg, ['tools', 'mcp', 'servers'], {}));

    // Detect preset states from existing servers
    const servers = safeGet(cfg, ['tools', 'mcp', 'servers'], {});
    mcpPresets.forEach(preset => {
      const isEnabled = preset.id in servers;
      const serverEnv = servers[preset.id]?.env || {};
      const apiKey = preset.requiresApiKey && preset.apiKeyEnv ? (serverEnv[preset.apiKeyEnv] || '') : '';
      presetStates[preset.id] = { enabled: isEnabled, apiKey };
    });
  };

  const syncRawFromConfig = (cfg) => {
    rawJson = JSON.stringify(cfg, null, 2);
    rawDirty = false;
  };

  const loadConfig = async () => {
    loading = true;
    error = '';
    status = 'loading';
    try {
      const res = await fetch(apiUrl);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);
      const data = await res.json();
      config = data;
      initForm(data);
      syncRawFromConfig(data);
      status = 'connected';
    } catch (err) {
      status = 'error';
      error = err?.message || 'Unable to reach gateway.';
    } finally {
      loading = false;
    }
  };

  const saveConfigObject = async (payload) => {
    saving = true;
    error = '';
    try {
      const res = await fetch(apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload)
      });
      const body = await res.json();
      if (!res.ok || !body.ok) {
        throw new Error(body.error || `HTTP ${res.status}`);
      }
      config = payload;
      initForm(payload);
      syncRawFromConfig(payload);
      lastSaved = new Date().toLocaleTimeString();
    } catch (err) {
      error = err?.message || 'Save failed.';
    } finally {
      saving = false;
    }
  };

  const applyFormToConfig = (cfg) => {
    const next = clone(cfg || {});
    next.agents = next.agents || {};
    next.agents.defaults = next.agents.defaults || {};
    next.agents.defaults.model = form.model;

    next.providers = next.providers || {};

    // Only include providers that are enabled
    if (form.openrouterEnabled) {
      next.providers.openrouter = next.providers.openrouter || {};
      next.providers.openrouter.apiKey = form.openrouterApiKey;
      next.providers.openrouter.apiBase = form.openrouterApiBase || null;
      next.providers.openrouter.model = form.openrouterModel || null;
    } else {
      next.providers.openrouter = { apiKey: '', apiBase: null, model: null };
    }

    if (form.togetherEnabled) {
      next.providers.together = next.providers.together || {};
      next.providers.together.apiKey = form.togetherApiKey;
      next.providers.together.apiBase = form.togetherApiBase || null;
      next.providers.together.model = form.togetherModel || null;
    } else {
      next.providers.together = { apiKey: '', apiBase: null, model: null };
    }

    if (form.anthropicEnabled) {
      next.providers.anthropic = next.providers.anthropic || {};
      next.providers.anthropic.apiKey = form.anthropicApiKey;
      next.providers.anthropic.apiBase = form.anthropicApiBase || null;
      next.providers.anthropic.model = form.anthropicModel || null;
    } else {
      next.providers.anthropic = { apiKey: '', apiBase: null, model: null };
    }

    if (form.openaiEnabled) {
      next.providers.openai = next.providers.openai || {};
      next.providers.openai.apiKey = form.openaiApiKey;
      next.providers.openai.apiBase = form.openaiApiBase || null;
      next.providers.openai.model = form.openaiModel || null;
    } else {
      next.providers.openai = { apiKey: '', apiBase: null, model: null };
    }

    if (form.geminiEnabled) {
      next.providers.gemini = next.providers.gemini || {};
      next.providers.gemini.apiKey = form.geminiApiKey;
      next.providers.gemini.apiBase = form.geminiApiBase || null;
      next.providers.gemini.model = form.geminiModel || null;
    } else {
      next.providers.gemini = { apiKey: '', apiBase: null, model: null };
    }

    if (form.vllmEnabled) {
      next.providers.vllm = next.providers.vllm || {};
      next.providers.vllm.apiKey = form.vllmApiKey;
      next.providers.vllm.apiBase = form.vllmApiBase || null;
      next.providers.vllm.model = form.vllmModel || null;
    } else {
      next.providers.vllm = { apiKey: '', apiBase: null, model: null };
    }

    if (form.groqEnabled) {
      next.providers.groq = next.providers.groq || {};
      next.providers.groq.apiKey = form.groqApiKey;
      next.providers.groq.apiBase = form.groqApiBase || null;
      next.providers.groq.model = form.groqModel || null;
    } else {
      next.providers.groq = { apiKey: '', apiBase: null, model: null };
    }

    // Tools
    next.tools = next.tools || {};
    next.tools.web = next.tools.web || {};
    next.tools.web.search = next.tools.web.search || {};
    next.tools.web.search.apiKey = form.websearchApiKey;
    next.tools.exec = next.tools.exec || {};
    next.tools.exec.restrictToWorkspace = !!form.restrictToWorkspace;
    next.tools.exec.maxContextTokens = parseInt(form.maxContextTokens) || 100000;

    // MCP
    next.tools.mcp = next.tools.mcp || {};
    next.tools.mcp.enabled = !!form.mcpEnabled;

    // Merge preset servers and custom servers
    const allServers = { ...mcpServers };

    // Add/update preset servers based on enabled state
    mcpPresets.forEach(preset => {
      const state = presetStates[preset.id];
      if (state.enabled) {
        const server = {
          transport: preset.transport,
          command: preset.command,
          args: [...preset.args]
        };
        if (preset.requiresApiKey && preset.apiKeyEnv && state.apiKey) {
          server.env = { [preset.apiKeyEnv]: state.apiKey };
        }
        allServers[preset.id] = server;
      } else {
        // Remove preset if disabled
        delete allServers[preset.id];
      }
    });

    next.tools.mcp.servers = allServers;

    // Channels
    next.channels = next.channels || {};

    next.channels.telegram = next.channels.telegram || {};
    next.channels.telegram.enabled = !!form.telegramEnabled;
    next.channels.telegram.token = form.telegramToken;
    next.channels.telegram.allowFrom = toList(form.telegramAllowFrom);

    next.channels.whatsapp = next.channels.whatsapp || {};
    next.channels.whatsapp.enabled = !!form.whatsappEnabled;
    next.channels.whatsapp.allowFrom = toList(form.whatsappAllowFrom);
    next.channels.whatsapp.bridgeUrl = form.whatsappBridgeUrl;

    next.channels.discord = next.channels.discord || {};
    next.channels.discord.enabled = !!form.discordEnabled;
    next.channels.discord.token = form.discordToken;
    next.channels.discord.allowFrom = toList(form.discordAllowFrom);
    next.channels.discord.allowedChannels = toList(form.discordAllowedChannels);

    return next;
  };

  const saveForm = async () => {
    if (!config) return;
    await saveConfigObject(applyFormToConfig(config));
  };

  const saveRaw = async () => {
    try {
      const parsed = JSON.parse(rawJson);
      await saveConfigObject(parsed);
    } catch (err) {
      error = err?.message || 'Invalid JSON.';
    }
  };

  const applyRawToForm = () => {
    try {
      const parsed = JSON.parse(rawJson);
      config = parsed;
      initForm(parsed);
      rawDirty = false;
    } catch (err) {
      error = err?.message || 'Invalid JSON.';
    }
  };

  const resetRaw = () => {
    if (!config) return;
    syncRawFromConfig(config);
  };

  // MCP Server management
  const addMcpServer = () => {
    if (!newMcpServer.name.trim()) {
      error = 'Server name is required';
      return;
    }
    const name = newMcpServer.name.trim();
    if (mcpServers[name]) {
      error = `Server "${name}" already exists`;
      return;
    }

    const server = { transport: newMcpServer.transport };
    if (newMcpServer.transport === 'stdio') {
      server.command = newMcpServer.command;
      server.args = newMcpServer.args.split(' ').filter(Boolean);
    } else {
      server.url = newMcpServer.url;
      if (newMcpServer.headers.trim()) {
        try {
          server.headers = JSON.parse(newMcpServer.headers);
        } catch {
          error = 'Invalid JSON for headers';
          return;
        }
      }
    }

    mcpServers = { ...mcpServers, [name]: server };
    newMcpServer = { name: '', transport: 'stdio', command: '', args: '', url: '', headers: '' };
    error = '';
  };

  // Check if a server name is a preset
  const isPreset = (name) => mcpPresets.some(p => p.id === name);

  // Get custom servers (non-preset)
  const getCustomServers = () => {
    const presetIds = mcpPresets.map(p => p.id);
    return Object.entries(mcpServers).filter(([name]) => !presetIds.includes(name));
  };

  const deleteMcpServer = (name) => {
    // If it's a preset, just disable it via presetStates
    if (isPreset(name)) {
      presetStates[name] = { ...presetStates[name], enabled: false };
      presetStates = presetStates; // trigger reactivity
    }
    // Remove from mcpServers
    const { [name]: _, ...rest } = mcpServers;
    mcpServers = rest;
  };

  // Test provider connection
  const testProvider = async (provider, apiKey, apiBase) => {
    testStates[provider] = { testing: true, result: null };
    testStates = testStates;
    
    try {
      const res = await fetch('/api/test/provider', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider, api_key: apiKey, api_base: apiBase })
      });
      const data = await res.json();
      testStates[provider] = { testing: false, result: data };
    } catch (err) {
      testStates[provider] = { testing: false, result: { ok: false, error: err.message } };
    }
    testStates = testStates;
  };

  // Test default model - parses provider from model string
  const testDefaultModel = async () => {
    const model = form.model || '';
    const providerMap = {
      '@openrouter': { key: 'openrouter', apiKey: form.openrouterApiKey, apiBase: form.openrouterApiBase },
      '@together': { key: 'together', apiKey: form.togetherApiKey, apiBase: form.togetherApiBase },
      '@anthropic': { key: 'anthropic', apiKey: form.anthropicApiKey, apiBase: form.anthropicApiBase },
      'anthropic/': { key: 'anthropic', apiKey: form.anthropicApiKey, apiBase: form.anthropicApiBase },
      '@openai': { key: 'openai', apiKey: form.openaiApiKey, apiBase: form.openaiApiBase },
      'openai/': { key: 'openai', apiKey: form.openaiApiKey, apiBase: form.openaiApiBase },
      '@gemini': { key: 'gemini', apiKey: form.geminiApiKey, apiBase: form.geminiApiBase },
      'gemini/': { key: 'gemini', apiKey: form.geminiApiKey, apiBase: form.geminiApiBase },
      '@groq': { key: 'groq', apiKey: form.groqApiKey, apiBase: form.groqApiBase },
      'groq/': { key: 'groq', apiKey: form.groqApiKey, apiBase: form.groqApiBase }
    };
    
    let detected = null;
    for (const [prefix, config] of Object.entries(providerMap)) {
      if (model.startsWith(prefix) || model.includes(prefix)) {
        detected = config;
        break;
      }
    }
    
    if (!detected) {
      testStates.default = { testing: false, result: { ok: false, error: 'Cannot detect provider. Use format: @provider/model or provider/model' } };
      testStates = testStates;
      return;
    }
    
    if (!detected.apiKey) {
      testStates.default = { testing: false, result: { ok: false, error: `No API key set for ${detected.key}. Enable and configure it below.` } };
      testStates = testStates;
      return;
    }
    
    testStates.default = { testing: true, result: null };
    testStates = testStates;
    
    try {
      const res = await fetch('/api/test/provider', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ provider: detected.key, api_key: detected.apiKey, api_base: detected.apiBase })
      });
      const data = await res.json();
      testStates.default = { testing: false, result: data };
    } catch (err) {
      testStates.default = { testing: false, result: { ok: false, error: err.message } };
    }
    testStates = testStates;
  };

  // Test channel connection
  const testChannel = async (channel, token, bridgeUrl = '') => {
    testStates[channel] = { testing: true, result: null };
    testStates = testStates;
    
    try {
      const res = await fetch('/api/test/channel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ channel, token, bridge_url: bridgeUrl })
      });
      const data = await res.json();
      testStates[channel] = { testing: false, result: data };
    } catch (err) {
      testStates[channel] = { testing: false, result: { ok: false, error: err.message } };
    }
    testStates = testStates;
  };

  // Clear test result after timeout
  const clearTestResult = (key) => {
    setTimeout(() => {
      testStates[key] = { testing: false, result: null };
      testStates = testStates;
    }, 5000);
  };

  // Fetch MCP runtime status
  const fetchMcpStatus = async () => {
    mcpStatusLoading = true;
    try {
      const res = await fetch('/api/mcp/status');
      if (res.ok) {
        mcpStatus = await res.json();
      }
    } catch (err) {
      console.warn('Could not fetch MCP status:', err);
    } finally {
      mcpStatusLoading = false;
    }
  };

  onMount(() => {
    loadConfig();
    fetchMcpStatus();
  });
</script>

<div class="shell">
  <header class="hero">
    <div>
      <span class="eyebrow">Gateway UI</span>
      <h1>icron Control Room</h1>
      <p>Manage models, providers, and channels without touching the filesystem.</p>
    </div>
    <div class={`status-pill ${status === 'connected' ? 'ok' : status === 'error' ? 'err' : ''}`}>
      {#if loading}
        Connecting…
      {:else if status === 'connected'}
        Connected
      {:else}
        Disconnected
      {/if}
    </div>
  </header>

  {#if error}
    <div class="notice err">{error}</div>
  {/if}

  <nav class="tabs">
    {#each tabs as tab}
      <button
        class={`tab ${activeTab === tab.id ? 'active' : ''}`}
        on:click={() => (activeTab = tab.id)}
      >
        {tab.label}
      </button>
    {/each}
  </nav>

  <main class="tab-content">
    {#if activeTab === 'models'}
      <div class="card">
        <div class="card-header">
          <div>
            <h2>Model Configuration</h2>
            <p>Enable providers and configure API credentials. Only enabled providers are used.</p>
          </div>
          <div class="meta">{lastSaved ? `Saved at ${lastSaved}` : ''}</div>
        </div>

        <div class="fields">
          <label class="field full">
            <span>Default Model</span>
            <input type="text" bind:value={form.model} placeholder="e.g. @anthropic/claude-sonnet-4-20250514" />
            <small>Format: <code>@provider/model</code> or <code>provider/model</code>. The provider prefix determines which API key to use.</small>
          </label>
          <div class="test-row">
            <button class="test-btn" on:click={testDefaultModel} disabled={testStates.default.testing || !form.model}>
              {testStates.default.testing ? 'Testing...' : 'Test Default Model'}
            </button>
            {#if testStates.default.result}
              <span class={`test-result ${testStates.default.result.ok ? 'ok' : 'err'}`}>
                {testStates.default.result.ok ? '✓ ' + testStates.default.result.message : '✗ ' + testStates.default.result.error}
              </span>
            {/if}
          </div>

          <div class="providers-grid">
            <!-- OpenRouter -->
            <div class="provider-section">
            <div class="provider-header">
              <h3>OpenRouter</h3>
              <label class="toggle-small">
                <input type="checkbox" bind:checked={form.openrouterEnabled} />
                <span>{form.openrouterEnabled ? 'Enabled' : 'Disabled'}</span>
              </label>
            </div>
            {#if form.openrouterEnabled}
              <div class="provider-fields">
                <div class="split">
                  <label class="field">
                    <span>API Key</span>
                    <input type="password" bind:value={form.openrouterApiKey} placeholder="sk-or-..." />
                  </label>
                  <label class="field">
                    <span>API Base</span>
                    <input type="text" bind:value={form.openrouterApiBase} placeholder="https://openrouter.ai/api/v1" />
                  </label>
                </div>
                <label class="field">
                  <span>Model</span>
                  <input type="text" bind:value={form.openrouterModel} placeholder="e.g. deepseek/deepseek-r1-0528:free" />
                </label>
                <div class="test-row">
                  <button class="test-btn" on:click={() => testProvider('openrouter', form.openrouterApiKey, form.openrouterApiBase)} disabled={testStates.openrouter.testing || !form.openrouterApiKey}>
                    {testStates.openrouter.testing ? 'Testing...' : 'Test Connection'}
                  </button>
                  {#if testStates.openrouter.result}
                    <span class={`test-result ${testStates.openrouter.result.ok ? 'ok' : 'err'}`}>
                      {testStates.openrouter.result.ok ? '✓ ' + testStates.openrouter.result.message : '✗ ' + testStates.openrouter.result.error}
                    </span>
                  {/if}
                </div>
              </div>
            {/if}
          </div>

          <!-- Together -->
          <div class="provider-section">
            <div class="provider-header">
              <h3>Together AI</h3>
              <label class="toggle-small">
                <input type="checkbox" bind:checked={form.togetherEnabled} />
                <span>{form.togetherEnabled ? 'Enabled' : 'Disabled'}</span>
              </label>
            </div>
            {#if form.togetherEnabled}
              <div class="provider-fields">
                <div class="split">
                  <label class="field">
                    <span>API Key</span>
                    <input type="password" bind:value={form.togetherApiKey} placeholder="..." />
                  </label>
                  <label class="field">
                    <span>API Base</span>
                    <input type="text" bind:value={form.togetherApiBase} placeholder="https://api.together.xyz/v1" />
                  </label>
                </div>
                <label class="field">
                  <span>Model</span>
                  <input type="text" bind:value={form.togetherModel} placeholder="e.g. meta-llama/Llama-3.1-70B-Instruct" />
                </label>
                <div class="test-row">
                  <button class="test-btn" on:click={() => testProvider('together', form.togetherApiKey, form.togetherApiBase)} disabled={testStates.together.testing || !form.togetherApiKey}>
                    {testStates.together.testing ? 'Testing...' : 'Test Connection'}
                  </button>
                  {#if testStates.together.result}
                    <span class={`test-result ${testStates.together.result.ok ? 'ok' : 'err'}`}>
                      {testStates.together.result.ok ? '✓ ' + testStates.together.result.message : '✗ ' + testStates.together.result.error}
                    </span>
                  {/if}
                </div>
              </div>
            {/if}
          </div>

          <!-- Anthropic -->
          <div class="provider-section">
            <div class="provider-header">
              <h3>Anthropic</h3>
              <label class="toggle-small">
                <input type="checkbox" bind:checked={form.anthropicEnabled} />
                <span>{form.anthropicEnabled ? 'Enabled' : 'Disabled'}</span>
              </label>
            </div>
            {#if form.anthropicEnabled}
              <div class="provider-fields">
                <div class="split">
                  <label class="field">
                    <span>API Key</span>
                    <input type="password" bind:value={form.anthropicApiKey} placeholder="sk-ant-..." />
                  </label>
                  <label class="field">
                    <span>API Base</span>
                    <input type="text" bind:value={form.anthropicApiBase} placeholder="https://api.anthropic.com" />
                  </label>
                </div>
                <label class="field">
                  <span>Model</span>
                  <input type="text" bind:value={form.anthropicModel} placeholder="e.g. claude-sonnet-4-20250514" />
                </label>
                <div class="test-row">
                  <button class="test-btn" on:click={() => testProvider('anthropic', form.anthropicApiKey, form.anthropicApiBase)} disabled={testStates.anthropic.testing || !form.anthropicApiKey}>
                    {testStates.anthropic.testing ? 'Testing...' : 'Test Connection'}
                  </button>
                  {#if testStates.anthropic.result}
                    <span class={`test-result ${testStates.anthropic.result.ok ? 'ok' : 'err'}`}>
                      {testStates.anthropic.result.ok ? '✓ ' + testStates.anthropic.result.message : '✗ ' + testStates.anthropic.result.error}
                    </span>
                  {/if}
                </div>
              </div>
            {/if}
          </div>

          <!-- OpenAI -->
          <div class="provider-section">
            <div class="provider-header">
              <h3>OpenAI</h3>
              <label class="toggle-small">
                <input type="checkbox" bind:checked={form.openaiEnabled} />
                <span>{form.openaiEnabled ? 'Enabled' : 'Disabled'}</span>
              </label>
            </div>
            {#if form.openaiEnabled}
              <div class="provider-fields">
                <div class="split">
                  <label class="field">
                    <span>API Key</span>
                    <input type="password" bind:value={form.openaiApiKey} placeholder="sk-..." />
                  </label>
                  <label class="field">
                    <span>API Base</span>
                    <input type="text" bind:value={form.openaiApiBase} placeholder="https://api.openai.com/v1" />
                  </label>
                </div>
                <label class="field">
                  <span>Model</span>
                  <input type="text" bind:value={form.openaiModel} placeholder="e.g. gpt-4o" />
                </label>
                <div class="test-row">
                  <button class="test-btn" on:click={() => testProvider('openai', form.openaiApiKey, form.openaiApiBase)} disabled={testStates.openai.testing || !form.openaiApiKey}>
                    {testStates.openai.testing ? 'Testing...' : 'Test Connection'}
                  </button>
                  {#if testStates.openai.result}
                    <span class={`test-result ${testStates.openai.result.ok ? 'ok' : 'err'}`}>
                      {testStates.openai.result.ok ? '✓ ' + testStates.openai.result.message : '✗ ' + testStates.openai.result.error}
                    </span>
                  {/if}
                </div>
              </div>
            {/if}
          </div>

          <!-- Gemini -->
          <div class="provider-section">
            <div class="provider-header">
              <h3>Gemini</h3>
              <label class="toggle-small">
                <input type="checkbox" bind:checked={form.geminiEnabled} />
                <span>{form.geminiEnabled ? 'Enabled' : 'Disabled'}</span>
              </label>
            </div>
            {#if form.geminiEnabled}
              <div class="provider-fields">
                <div class="split">
                  <label class="field">
                    <span>API Key</span>
                    <input type="password" bind:value={form.geminiApiKey} placeholder="..." />
                  </label>
                  <label class="field">
                    <span>API Base</span>
                    <input type="text" bind:value={form.geminiApiBase} placeholder="https://generativelanguage.googleapis.com" />
                  </label>
                </div>
                <label class="field">
                  <span>Model</span>
                  <input type="text" bind:value={form.geminiModel} placeholder="e.g. gemini-2.0-flash" />
                </label>
                <div class="test-row">
                  <button class="test-btn" on:click={() => testProvider('gemini', form.geminiApiKey, form.geminiApiBase)} disabled={testStates.gemini.testing || !form.geminiApiKey}>
                    {testStates.gemini.testing ? 'Testing...' : 'Test Connection'}
                  </button>
                  {#if testStates.gemini.result}
                    <span class={`test-result ${testStates.gemini.result.ok ? 'ok' : 'err'}`}>
                      {testStates.gemini.result.ok ? '✓ ' + testStates.gemini.result.message : '✗ ' + testStates.gemini.result.error}
                    </span>
                  {/if}
                </div>
              </div>
            {/if}
          </div>

          <!-- vLLM -->
          <div class="provider-section">
            <div class="provider-header">
              <h3>vLLM (Local)</h3>
              <label class="toggle-small">
                <input type="checkbox" bind:checked={form.vllmEnabled} />
                <span>{form.vllmEnabled ? 'Enabled' : 'Disabled'}</span>
              </label>
            </div>
            {#if form.vllmEnabled}
              <div class="provider-fields">
                <div class="split">
                  <label class="field">
                    <span>API Key</span>
                    <input type="password" bind:value={form.vllmApiKey} placeholder="any-string" />
                  </label>
                  <label class="field">
                    <span>API Base</span>
                    <input type="text" bind:value={form.vllmApiBase} placeholder="http://localhost:8000/v1" />
                  </label>
                </div>
                <label class="field">
                  <span>Model</span>
                  <input type="text" bind:value={form.vllmModel} placeholder="e.g. meta-llama/Llama-3.1-8B-Instruct" />
                </label>
                <div class="test-row">
                  <button class="test-btn" on:click={() => testProvider('vllm', form.vllmApiKey, form.vllmApiBase)} disabled={testStates.vllm.testing || !form.vllmApiBase}>
                    {testStates.vllm.testing ? 'Testing...' : 'Test Connection'}
                  </button>
                  {#if testStates.vllm.result}
                    <span class={`test-result ${testStates.vllm.result.ok ? 'ok' : 'err'}`}>
                      {testStates.vllm.result.ok ? '✓ ' + testStates.vllm.result.message : '✗ ' + testStates.vllm.result.error}
                    </span>
                  {/if}
                </div>
              </div>
            {/if}
          </div>

          <!-- Groq -->
          <div class="provider-section">
            <div class="provider-header">
              <h3>Groq</h3>
              <label class="toggle-small">
                <input type="checkbox" bind:checked={form.groqEnabled} />
                <span>{form.groqEnabled ? 'Enabled' : 'Disabled'}</span>
              </label>
            </div>
            {#if form.groqEnabled}
              <div class="provider-fields">
                <div class="split">
                  <label class="field">
                    <span>API Key</span>
                    <input type="password" bind:value={form.groqApiKey} placeholder="gsk_..." />
                  </label>
                  <label class="field">
                    <span>API Base</span>
                    <input type="text" bind:value={form.groqApiBase} placeholder="https://api.groq.com" />
                  </label>
                </div>
                <label class="field">
                  <span>Model</span>
                  <input type="text" bind:value={form.groqModel} placeholder="e.g. llama-3.3-70b-versatile" />
                </label>
                <div class="test-row">
                  <button class="test-btn" on:click={() => testProvider('groq', form.groqApiKey, form.groqApiBase)} disabled={testStates.groq.testing || !form.groqApiKey}>
                    {testStates.groq.testing ? 'Testing...' : 'Test Connection'}
                  </button>
                  {#if testStates.groq.result}
                    <span class={`test-result ${testStates.groq.result.ok ? 'ok' : 'err'}`}>
                      {testStates.groq.result.ok ? '✓ ' + testStates.groq.result.message : '✗ ' + testStates.groq.result.error}
                    </span>
                  {/if}
                </div>
              </div>
            {/if}
            </div>
          </div>
        </div>

        <div class="actions">
          <button class="primary" on:click|preventDefault={saveForm} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
          <button class="ghost" on:click|preventDefault={loadConfig} disabled={loading}>
            Reload
          </button>
        </div>
      </div>
    {/if}

    {#if activeTab === 'channels'}
      <div class="card">
        <div class="card-header">
          <div>
            <h2>Channels</h2>
            <p>Configure messaging channels. Enable channels and set allow-lists for security.</p>
          </div>
          <div class="meta">{lastSaved ? `Saved at ${lastSaved}` : ''}</div>
        </div>

        <div class="fields">
          <div class="channels-grid">
            <div class="channel-section">
              <h3>Discord</h3>
            <label class="toggle">
              <input type="checkbox" bind:checked={form.discordEnabled} />
              <span>Enabled</span>
            </label>
            {#if form.discordEnabled}
              <label class="field">
                <span>Bot Token</span>
                <input type="password" bind:value={form.discordToken} placeholder="..." />
              </label>
              <label class="field">
                <span>Allow From (User IDs)</span>
                <input type="text" bind:value={form.discordAllowFrom} placeholder="123456789, 987654321" />
                <small>Comma-separated Discord user IDs</small>
              </label>
              <label class="field">
                <span>Allowed Channels</span>
                <input type="text" bind:value={form.discordAllowedChannels} placeholder="111222333, 444555666" />
                <small>Comma-separated channel IDs where bot responds</small>
              </label>
              <div class="test-row">
                <button class="test-btn" on:click={() => testChannel('discord', form.discordToken, null)} disabled={testStates.discord.testing || !form.discordToken}>
                  {testStates.discord.testing ? 'Testing...' : 'Test Connection'}
                </button>
                {#if testStates.discord.result}
                  <span class={`test-result ${testStates.discord.result.ok ? 'ok' : 'err'}`}>
                    {testStates.discord.result.ok ? '✓ ' + testStates.discord.result.message : '✗ ' + testStates.discord.result.error}
                  </span>
                {/if}
              </div>
            {/if}
          </div>

          <div class="channel-section">
            <h3>Telegram</h3>
            <label class="toggle">
              <input type="checkbox" bind:checked={form.telegramEnabled} />
              <span>Enabled</span>
            </label>
            {#if form.telegramEnabled}
              <label class="field">
                <span>Bot Token</span>
                <input type="password" bind:value={form.telegramToken} placeholder="123456:ABC-DEF..." />
              </label>
              <label class="field">
                <span>Allow From</span>
                <input type="text" bind:value={form.telegramAllowFrom} placeholder="123456, 78910" />
                <small>Comma-separated Telegram user IDs or usernames</small>
              </label>
              <div class="test-row">
                <button class="test-btn" on:click={() => testChannel('telegram', form.telegramToken, null)} disabled={testStates.telegram.testing || !form.telegramToken}>
                  {testStates.telegram.testing ? 'Testing...' : 'Test Connection'}
                </button>
                {#if testStates.telegram.result}
                  <span class={`test-result ${testStates.telegram.result.ok ? 'ok' : 'err'}`}>
                    {testStates.telegram.result.ok ? '✓ ' + testStates.telegram.result.message : '✗ ' + testStates.telegram.result.error}
                  </span>
                {/if}
              </div>
            {/if}
          </div>

          <div class="channel-section">
            <h3>WhatsApp</h3>
            <label class="toggle">
              <input type="checkbox" bind:checked={form.whatsappEnabled} />
              <span>Enabled</span>
            </label>
            {#if form.whatsappEnabled}
              <label class="field">
                <span>Bridge URL</span>
                <input type="text" bind:value={form.whatsappBridgeUrl} placeholder="ws://localhost:3001" />
                <small>URL of the WhatsApp bridge service</small>
              </label>
              <label class="field">
                <span>Allow From</span>
                <input type="text" bind:value={form.whatsappAllowFrom} placeholder="+15551234567" />
                <small>Comma-separated phone numbers</small>
              </label>
              <div class="test-row">
                <button class="test-btn" on:click={() => testChannel('whatsapp', null, form.whatsappBridgeUrl)} disabled={testStates.whatsapp.testing || !form.whatsappBridgeUrl}>
                  {testStates.whatsapp.testing ? 'Testing...' : 'Test Connection'}
                </button>
                {#if testStates.whatsapp.result}
                  <span class={`test-result ${testStates.whatsapp.result.ok ? 'ok' : 'err'}`}>
                    {testStates.whatsapp.result.ok ? '✓ ' + testStates.whatsapp.result.message : '✗ ' + testStates.whatsapp.result.error}
                  </span>
                {/if}
              </div>
            {/if}
            </div>
          </div>
        </div>

        <div class="actions">
          <button class="primary" on:click|preventDefault={saveForm} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
          <button class="ghost" on:click|preventDefault={loadConfig} disabled={loading}>
            Reload
          </button>
        </div>
      </div>
    {/if}

    {#if activeTab === 'memory'}
      <div class="card">
        <div class="card-header">
          <div>
            <h2>Memory Settings</h2>
            <p>Configure context limits and security settings.</p>
          </div>
          <div class="meta">{lastSaved ? `Saved at ${lastSaved}` : ''}</div>
        </div>

        <div class="fields">
          <label class="field">
            <span>Max Context Tokens</span>
            <input type="number" bind:value={form.maxContextTokens} min="10000" max="200000" step="10000" />
            <small>Maximum tokens for conversation history. Older messages are trimmed when exceeded.</small>
          </label>

          <label class="toggle">
            <input type="checkbox" bind:checked={form.restrictToWorkspace} />
            <span>Restrict Tools to Workspace</span>
          </label>
          <p class="hint">When enabled, file operations are limited to the workspace folder for security.</p>
        </div>

        <div class="actions">
          <button class="primary" on:click|preventDefault={saveForm} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
          <button class="ghost" on:click|preventDefault={loadConfig} disabled={loading}>
            Reload
          </button>
        </div>
      </div>
    {/if}

    {#if activeTab === 'tools'}
      <div class="card">
        <div class="card-header">
          <div>
            <h2>Tools</h2>
            <p>Configure external tools and integrations.</p>
          </div>
          <div class="meta">{lastSaved ? `Saved at ${lastSaved}` : ''}</div>
        </div>

        <div class="fields">
          <div class="tool-section">
            <h3>Web Search (Brave)</h3>
            <label class="field">
              <span>Brave Search API Key</span>
              <input type="password" bind:value={form.websearchApiKey} placeholder="BSA..." />
              <small>Required for web search tool. Get one at <a href="https://brave.com/search/api" target="_blank">brave.com/search/api</a></small>
            </label>
          </div>
        </div>

        <div class="actions">
          <button class="primary" on:click|preventDefault={saveForm} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
          <button class="ghost" on:click|preventDefault={loadConfig} disabled={loading}>
            Reload
          </button>
        </div>
      </div>
    {/if}

    {#if activeTab === 'mcp'}
      <div class="card">
        <div class="card-header">
          <div>
            <h2>MCP Servers</h2>
            <p>Model Context Protocol servers extend icron with external tools.</p>
          </div>
          <div class="meta">{lastSaved ? `Saved at ${lastSaved}` : ''}</div>
        </div>

        <div class="fields">
          <label class="toggle">
            <input type="checkbox" bind:checked={form.mcpEnabled} />
            <span>Enable MCP</span>
          </label>
          <p class="hint">When enabled, icron will connect to configured MCP servers and expose their tools.</p>

          <!-- Runtime Status -->
          {#if form.mcpEnabled}
            <div class="mcp-status-card">
              <div class="mcp-status-header">
                <span class="mcp-status-label">Runtime Status</span>
                <button class="btn-refresh" on:click|preventDefault={fetchMcpStatus} disabled={mcpStatusLoading}>
                  {mcpStatusLoading ? '...' : '↻'}
                </button>
              </div>
              {#if mcpStatus.initialized}
                <div class="mcp-status-summary">
                  <span class="status-badge ok">{mcpStatus.totalTools} tools loaded</span>
                  <span class="status-count">{mcpStatus.servers.length} server{mcpStatus.servers.length !== 1 ? 's' : ''} connected</span>
                </div>
                {#if mcpStatus.servers.length > 0}
                  <div class="mcp-server-list">
                    {#each mcpStatus.servers as server}
                      <div class="mcp-server-item">
                        <span class="server-name">{server.name}</span>
                        <span class="server-tools">{server.toolCount} tools</span>
                      </div>
                    {/each}
                  </div>
                {/if}
              {:else}
                <div class="mcp-status-summary">
                  <span class="status-badge pending">Not initialized</span>
                  <span class="status-hint">Restart icron to connect MCP servers</span>
                </div>
              {/if}
            </div>
          {/if}

          <div class="divider"></div>

          <!-- Preset servers -->
          <div class="presets-section">
            <div class="presets-header">
              <div>
                <h4>Quick Add Presets</h4>
                <p class="hint">Enable popular MCP servers with one click. API keys are stored securely in your config.</p>
              </div>
              <label class="search-field">
                <input type="text" bind:value={mcpSearch} placeholder="Search presets..." />
              </label>
            </div>

            <div class="preset-scroll">
              <div class="preset-grid">
                {#each filteredPresets as preset}
                  <div class="preset-card">
                    <div class="preset-header">
                      <div class="preset-name">{preset.name}</div>
                      <label class="toggle-small">
                        <input type="checkbox" bind:checked={presetStates[preset.id].enabled} />
                        <span>{presetStates[preset.id].enabled ? 'On' : 'Off'}</span>
                      </label>
                    </div>
                    <p class="preset-desc">{preset.description}</p>
                    {#if preset.requiresApiKey && presetStates[preset.id].enabled}
                      <label class="field compact">
                        <span>{preset.apiKeyEnv?.replace(/_/g, ' ')}</span>
                        <input
                          type="password"
                          bind:value={presetStates[preset.id].apiKey}
                          placeholder={preset.apiKeyPlaceholder}
                        />
                      </label>
                    {/if}
                  </div>
                {/each}
                {#if filteredPresets.length === 0}
                  <p class="no-results">No presets match "{mcpSearch}"</p>
                {/if}
              </div>
            </div>
          </div>

          <div class="divider"></div>

          <!-- Custom servers (non-preset) -->
          <div class="info-box">
            <h4>Custom Servers ({getCustomServers().length})</h4>
            {#if getCustomServers().length > 0}
              <ul class="server-list">
                {#each getCustomServers() as [name, server]}
                  <li>
                    <div class="server-info">
                      <strong>{name}</strong>
                      <span class="server-type">{server.transport || 'stdio'}</span>
                      {#if server.transport === 'sse'}
                        <code>{server.url}</code>
                      {:else}
                        <code>{server.command} {(server.args || []).join(' ')}</code>
                      {/if}
                    </div>
                    <button class="delete-btn" on:click={() => deleteMcpServer(name)}>Delete</button>
                  </li>
                {/each}
              </ul>
            {:else}
              <p class="empty">No custom MCP servers. Use presets above or add one below.</p>
            {/if}
          </div>

          <div class="divider"></div>

          <!-- Add new server form -->
          <div class="add-server-form">
            <h4>Add New Server</h4>
            <label class="field">
              <span>Server Name</span>
              <input type="text" bind:value={newMcpServer.name} placeholder="e.g. filesystem" />
            </label>

            <label class="field">
              <span>Transport</span>
              <select bind:value={newMcpServer.transport}>
                <option value="stdio">stdio (local command)</option>
                <option value="sse">sse (remote URL)</option>
              </select>
            </label>

            {#if newMcpServer.transport === 'stdio'}
              <label class="field">
                <span>Command</span>
                <input type="text" bind:value={newMcpServer.command} placeholder="e.g. npx or python" />
              </label>
              <label class="field">
                <span>Arguments (space-separated)</span>
                <input type="text" bind:value={newMcpServer.args} placeholder="e.g. -y @modelcontextprotocol/server-filesystem /path" />
              </label>
            {:else}
              <label class="field">
                <span>URL</span>
                <input type="text" bind:value={newMcpServer.url} placeholder="https://mcp.example.com/server" />
              </label>
              <label class="field">
                <span>Headers (JSON, optional)</span>
                <input type="text" bind:value={newMcpServer.headers} placeholder="e.g. Authorization: Bearer token" />
                <small>Enter as JSON object if needed</small>
              </label>
            {/if}

            <button class="secondary" on:click={addMcpServer}>Add Server</button>
          </div>
        </div>

        <div class="actions">
          <button class="primary" on:click|preventDefault={saveForm} disabled={saving}>
            {saving ? 'Saving…' : 'Save'}
          </button>
          <button class="ghost" on:click|preventDefault={loadConfig} disabled={loading}>
            Reload
          </button>
        </div>
      </div>
    {/if}

    {#if activeTab === 'raw'}
      <div class="card raw">
        <div class="card-header">
          <div>
            <h2>Raw Configuration</h2>
            <p>Full JSON configuration editor. Be careful - invalid JSON will be rejected.</p>
          </div>
          <div class={`meta ${rawDirty ? 'warn' : ''}`}>
            {rawDirty ? 'Unsaved edits' : 'In sync'}
          </div>
        </div>

        <textarea
          class="raw-editor"
          bind:value={rawJson}
          on:input={() => (rawDirty = true)}
          spellcheck="false"
        ></textarea>

        <div class="actions">
          <button class="primary" on:click|preventDefault={saveRaw} disabled={saving}>
            {saving ? 'Saving…' : 'Save Raw JSON'}
          </button>
          <button class="ghost" on:click|preventDefault={applyRawToForm}>
            Apply to Form
          </button>
          <button class="ghost" on:click|preventDefault={resetRaw}>
            Reset
          </button>
        </div>
      </div>
    {/if}
  </main>
</div>

<style>
  :global(body) {
    margin: 0;
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
    background: #0a0a0a;
    color: #ffffff;
  }

  .shell {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
  }

  .hero {
    background: linear-gradient(135deg, rgba(34, 211, 208, 0.12), rgba(248, 113, 113, 0.08));
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
    padding: 24px 32px;
    display: flex;
    justify-content: space-between;
    align-items: center;
  }

  .eyebrow {
    font-size: 12px;
    text-transform: uppercase;
    letter-spacing: 1px;
    color: #22d3d0;
    margin-bottom: 4px;
    display: block;
  }

  .hero h1 {
    margin: 0 0 8px 0;
    font-size: 24px;
  }

  .hero p {
    margin: 0;
    color: #9ca3af;
    font-size: 14px;
  }

  .status-pill {
    padding: 8px 16px;
    border-radius: 24px;
    font-size: 13px;
    font-weight: 500;
    background: rgba(255, 255, 255, 0.1);
  }

  .status-pill.ok {
    background: rgba(34, 211, 208, 0.2);
    color: #22d3d0;
  }

  .status-pill.err {
    background: rgba(248, 113, 113, 0.2);
    color: #f87171;
  }

  .notice {
    margin: 16px 32px;
    padding: 12px 16px;
    border-radius: 8px;
  }

  .notice.err {
    background: rgba(248, 113, 113, 0.15);
    border: 1px solid rgba(248, 113, 113, 0.3);
    color: #fca5a5;
  }

  .tabs {
    display: flex;
    gap: 4px;
    padding: 0 32px;
    background: #0a0a0a;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
  }

  .tab {
    padding: 14px 24px;
    background: none;
    border: none;
    color: #9ca3af;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    border-bottom: 2px solid transparent;
    transition: all 0.2s;
  }

  .tab:hover {
    color: #ffffff;
  }

  .tab.active {
    color: #22d3d0;
    border-bottom-color: #22d3d0;
  }

  .tab-content {
    flex: 1;
    padding: 24px 32px;
    max-width: 1200px;
    margin: 0 auto;
  }

  .card {
    background: #1a1a1a;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 12px;
    padding: 24px;
  }

  .card.raw {
    display: flex;
    flex-direction: column;
  }

  .card-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    margin-bottom: 24px;
  }

  .card-header h2 {
    margin: 0 0 4px 0;
    font-size: 18px;
  }

  .card-header p {
    margin: 0;
    color: #9ca3af;
    font-size: 13px;
  }

  .meta {
    font-size: 12px;
    color: #9ca3af;
  }

  .meta.warn {
    color: #fbbf24;
  }

  .fields {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .field {
    display: flex;
    flex-direction: column;
    gap: 6px;
  }

  .field.full {
    width: 100%;
  }

  .field span {
    font-size: 13px;
    font-weight: 500;
    color: #ffffff;
  }

  .field input, .field select {
    padding: 10px 12px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    border-radius: 8px;
    background: #2a2a2a;
    color: #ffffff;
    font-size: 14px;
  }

  .field input::placeholder {
    color: #6b7280;
  }

  .field small {
    font-size: 12px;
    color: #9ca3af;
  }

  .field small code {
    background: rgba(34, 211, 208, 0.1);
    color: #22d3d0;
    padding: 2px 6px;
    border-radius: 4px;
    font-family: monospace;
    font-size: 11px;
  }

  .field small a {
    color: #22d3d0;
  }

  .split {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }

  .toggle {
    display: flex;
    align-items: center;
    gap: 10px;
    cursor: pointer;
  }

  .toggle input[type='checkbox'] {
    width: 18px;
    height: 18px;
    accent-color: #22d3d0;
  }

  .toggle span {
    font-size: 14px;
    font-weight: 500;
  }

  .toggle-small {
    display: flex;
    align-items: center;
    gap: 8px;
    cursor: pointer;
  }

  .toggle-small input[type='checkbox'] {
    width: 16px;
    height: 16px;
    accent-color: #22d3d0;
  }

  .toggle-small span {
    font-size: 12px;
    color: #9ca3af;
  }

  .hint {
    font-size: 12px;
    color: #9ca3af;
    margin: 0;
  }

  .divider {
    height: 1px;
    background: rgba(255, 255, 255, 0.1);
    margin: 8px 0;
  }

  .providers-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 16px;
  }

  .channels-grid {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }

  @media (max-width: 900px) {
    .providers-grid {
      grid-template-columns: 1fr;
    }
    .channels-grid {
      grid-template-columns: 1fr;
    }
  }

  .provider-section,
  .channel-section,
  .tool-section {
    background: #141414;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 16px;
  }

  .provider-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0;
  }

  .provider-header h3 {
    margin: 0;
    font-size: 15px;
    color: #22d3d0;
  }

  .provider-fields {
    margin-top: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .test-row {
    display: flex;
    align-items: center;
    gap: 12px;
    margin-top: 8px;
  }

  .test-btn {
    padding: 8px 16px;
    background: transparent;
    border: 1px solid rgba(34, 211, 208, 0.5);
    border-radius: 6px;
    color: #22d3d0;
    font-size: 13px;
    cursor: pointer;
    transition: all 0.2s;
  }

  .test-btn:hover:not(:disabled) {
    background: rgba(34, 211, 208, 0.1);
    border-color: #22d3d0;
  }

  .test-btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  .test-result {
    font-size: 13px;
    padding: 4px 8px;
    border-radius: 4px;
  }

  .test-result.ok {
    color: #22c55e;
    background: rgba(34, 197, 94, 0.1);
  }

  .test-result.err {
    color: #ef4444;
    background: rgba(239, 68, 68, 0.1);
  }

  .channel-section h3,
  .tool-section h3 {
    margin: 0 0 16px 0;
    font-size: 15px;
    color: #22d3d0;
  }

  .info-box {
    background: #141414;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 16px;
  }

  .info-box h4 {
    margin: 0 0 12px 0;
    font-size: 14px;
    color: #ffffff;
  }

  .server-list {
    list-style: none;
    padding: 0;
    margin: 0;
  }

  .server-list li {
    padding: 10px 0;
    border-bottom: 1px solid rgba(255, 255, 255, 0.05);
    display: flex;
    justify-content: space-between;
    align-items: center;
    gap: 12px;
  }

  .server-list li:last-child {
    border-bottom: none;
  }

  .server-info {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .server-type {
    font-size: 11px;
    padding: 2px 6px;
    background: rgba(34, 211, 208, 0.2);
    color: #22d3d0;
    border-radius: 4px;
  }

  .server-list code {
    font-size: 12px;
    color: #9ca3af;
    background: rgba(255, 255, 255, 0.05);
    padding: 2px 6px;
    border-radius: 4px;
  }

  .delete-btn {
    padding: 4px 10px;
    font-size: 12px;
    background: rgba(248, 113, 113, 0.15);
    border: 1px solid rgba(248, 113, 113, 0.3);
    color: #f87171;
    border-radius: 4px;
    cursor: pointer;
  }

  .delete-btn:hover {
    background: rgba(248, 113, 113, 0.25);
  }

  .empty {
    color: #6b7280;
    font-size: 13px;
    margin: 0;
  }

  .presets-section h4 {
    margin: 0 0 4px 0;
    font-size: 15px;
    color: #ffffff;
  }

  .presets-header {
    display: flex;
    justify-content: space-between;
    align-items: flex-start;
    gap: 16px;
    margin-bottom: 12px;
  }

  .search-field {
    display: flex;
    align-items: center;
  }

  .search-field input {
    background: #1a1a1a;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 6px;
    padding: 8px 12px;
    color: #fff;
    font-size: 13px;
    width: 200px;
  }

  .search-field input::placeholder {
    color: #666;
  }

  .search-field input:focus {
    outline: none;
    border-color: #22d3d0;
  }

  .preset-scroll {
    max-height: 400px;
    overflow-y: auto;
    padding-right: 8px;
  }

  .preset-scroll::-webkit-scrollbar {
    width: 6px;
  }

  .preset-scroll::-webkit-scrollbar-track {
    background: rgba(255, 255, 255, 0.05);
    border-radius: 3px;
  }

  .preset-scroll::-webkit-scrollbar-thumb {
    background: rgba(255, 255, 255, 0.2);
    border-radius: 3px;
  }

  .preset-scroll::-webkit-scrollbar-thumb:hover {
    background: rgba(255, 255, 255, 0.3);
  }

  .no-results {
    grid-column: span 2;
    text-align: center;
    color: #666;
    padding: 24px;
    font-style: italic;
  }

  .preset-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 12px;
    margin-top: 12px;
  }

  @media (max-width: 700px) {
    .preset-grid {
      grid-template-columns: 1fr;
    }
  }

  .preset-card {
    background: #141414;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 14px;
  }

  .preset-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 6px;
  }

  .preset-name {
    font-size: 14px;
    font-weight: 600;
    color: #22d3d0;
  }

  .preset-desc {
    font-size: 12px;
    color: #9ca3af;
    margin: 0 0 8px 0;
    line-height: 1.4;
  }

  .field.compact {
    gap: 4px;
  }

  .field.compact span {
    font-size: 11px;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #9ca3af;
  }

  .field.compact input {
    padding: 8px 10px;
    font-size: 13px;
  }

  .add-server-form {
    background: #141414;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 16px;
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .add-server-form h4 {
    margin: 0 0 8px 0;
    font-size: 14px;
    color: #ffffff;
  }

  .raw-editor {
    width: 100%;
    min-height: 400px;
    padding: 12px;
    border: 1px solid rgba(255, 255, 255, 0.1);
    border-radius: 8px;
    background: #141414;
    color: #22d3d0;
    font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
    font-size: 13px;
    resize: vertical;
  }

  .actions {
    display: flex;
    gap: 12px;
    margin-top: 24px;
  }

  button {
    padding: 10px 20px;
    border-radius: 8px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
    transition: all 0.2s;
  }

  button:disabled {
    opacity: 0.5;
    cursor: not-allowed;
  }

  button.primary {
    background: linear-gradient(135deg, #22d3d0, #14b8a6);
    color: #0a0a0a;
    border: none;
  }

  button.primary:hover:not(:disabled) {
    opacity: 0.9;
  }

  button.secondary {
    background: rgba(34, 211, 208, 0.15);
    color: #22d3d0;
    border: 1px solid rgba(34, 211, 208, 0.3);
  }

  button.secondary:hover:not(:disabled) {
    background: rgba(34, 211, 208, 0.25);
  }

  button.ghost {
    background: transparent;
    color: #9ca3af;
    border: 1px solid rgba(255, 255, 255, 0.15);
  }

  button.ghost:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.05);
    color: #ffffff;
  }

  /* MCP Status Card */
  .mcp-status-card {
    background: #141414;
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 10px;
    padding: 14px;
    margin: 12px 0;
  }

  .mcp-status-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 10px;
  }

  .mcp-status-label {
    font-size: 12px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.5px;
    color: #9ca3af;
  }

  .btn-refresh {
    background: transparent;
    border: 1px solid rgba(255, 255, 255, 0.15);
    color: #9ca3af;
    padding: 4px 8px;
    border-radius: 6px;
    cursor: pointer;
    font-size: 14px;
  }

  .btn-refresh:hover:not(:disabled) {
    background: rgba(255, 255, 255, 0.05);
    color: #ffffff;
  }

  .mcp-status-summary {
    display: flex;
    align-items: center;
    gap: 12px;
    flex-wrap: wrap;
  }

  .status-badge {
    font-size: 13px;
    font-weight: 600;
    padding: 4px 10px;
    border-radius: 6px;
  }

  .status-badge.ok {
    background: rgba(34, 211, 208, 0.15);
    color: #22d3d0;
  }

  .status-badge.pending {
    background: rgba(251, 191, 36, 0.15);
    color: #fbbf24;
  }

  .status-count, .status-hint {
    font-size: 12px;
    color: #9ca3af;
  }

  .mcp-server-list {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    margin-top: 10px;
  }

  .mcp-server-item {
    display: flex;
    align-items: center;
    gap: 6px;
    background: #1a1a1a;
    border: 1px solid rgba(255, 255, 255, 0.06);
    padding: 6px 10px;
    border-radius: 6px;
    font-size: 12px;
  }

  .server-name {
    color: #ffffff;
  }

  .server-tools {
    color: #22d3d0;
    font-size: 11px;
  }
</style>

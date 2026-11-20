/**
 * API Service for CodePilot Web UI
 */

const API_BASE = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '');

async function apiFetch(path, options) {
  const res = await fetch(`${API_BASE}${path}`, options);
  if (res.status === 401 && !path.startsWith('/api/auth/')) {
    window.dispatchEvent(new Event('codepilot:unauthorized'));
  }
  return res;
}

export async function fetchAuthStatus() {
  const res = await apiFetch('/api/auth/status');
  if (!res.ok) throw new Error(`Login status request failed: ${res.statusText}`);
  return await res.json();
}

export async function login(username, password) {
  const res = await apiFetch('/api/auth/login', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ username, password }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Login failed: ${res.statusText}`);
  }
  return await res.json();
}

export async function logout() {
  const res = await apiFetch('/api/auth/logout', { method: 'POST' });
  if (!res.ok) throw new Error(`Logout failed: ${res.statusText}`);
}

export async function fetchHealth() {
  try {
    const res = await apiFetch('/api/health', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return await res.json();
  } catch {
    const isLocalBrowser = ['localhost', '127.0.0.1', '::1'].includes(window.location.hostname);
    if (isLocalBrowser) {
      try {
        const ollamaRes = await fetch('http://127.0.0.1:11434/api/tags');
        if (ollamaRes.ok) {
          const data = await ollamaRes.json();
          return {
            status: 'ready',
            ollama_connected: true,
            backend_connected: false,
            model: 'qwen2.5-coder:7b',
            available_models: (data.models || []).map(m => m.name),
            workspace: './workspace',
            note: 'Direct Ollama connected (FastAPI offline)',
          };
        }
      } catch {
        // offline
      }
    }
    return {
      status: 'offline',
      ollama_connected: false,
      backend_connected: false,
      model: 'qwen2.5-coder:7b',
      available_models: ['qwen2.5-coder:7b', 'qwen3.5:4b'],
      workspace: './workspace',
    };
  }
}

export async function fetchWorkspace() {
  const res = await apiFetch('/api/workspace');
  if (!res.ok) throw new Error(`Workspace request failed: ${res.statusText}`);
  return await res.json();
}

export async function fetchWorkspaceFile(path) {
  const res = await apiFetch(`/api/workspace/file?path=${encodeURIComponent(path)}`);
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `File request failed: ${res.statusText}`);
  }
  return await res.json();
}

export async function sendChatMessage({
  message,
  model = 'qwen2.5-coder:7b',
  history = [],
  workspace = null,
  allowEdits = false,
  allowTests = false,
}) {
  const res = await apiFetch('/api/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      model,
      history,
      workspace,
      allow_edits: allowEdits,
      allow_test_execution: allowTests,
    }),
  });
  if (!res.ok) {
    const errorData = await res.json().catch(() => ({}));
    throw new Error(errorData.detail || `Server error: ${res.statusText}`);
  }
  return await res.json();
}

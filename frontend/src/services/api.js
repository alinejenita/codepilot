/**
 * API Service for CodePilot Web UI
 */

const API_BASE = 'http://127.0.0.1:8000';

export async function fetchHealth() {
  try {
    const res = await fetch(`${API_BASE}/api/health`, {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
    if (!res.ok) throw new Error(`Health check failed: ${res.statusText}`);
    return await res.json();
  } catch (err) {
    // If FastAPI isn't running yet, check Ollama directly at 11434
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
      // both offline
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

export async function sendChatMessage({ message, model = 'qwen2.5-coder:7b' }) {
  try {
    const res = await fetch(`${API_BASE}/api/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message, model }),
    });
    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `Server error: ${res.statusText}`);
    }
    return await res.json();
  } catch (err) {
    // Fallback if FastAPI server isn't running yet
    throw err;
  }
}

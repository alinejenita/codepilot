import React from 'react';
import { 
  Cpu, 
  Layers, 
  Terminal, 
  Activity, 
  RefreshCw,
  FolderGit2
} from 'lucide-react';

export default function Header({ 
  currentModel, 
  onModelChange, 
  availableModels = [], 
  health, 
  onRefreshHealth,
  showActivityPanel,
  onToggleActivityPanel,
  showWorkspacePanel,
  onToggleWorkspacePanel
}) {
  return (
    <header className="h-14 border-b border-[#1e293b] bg-[#0d121f]/90 backdrop-blur px-6 flex items-center justify-between z-10 shrink-0">
      {/* Left: Active Status */}
      <div className="flex items-center space-x-3">
        <div className="flex items-center gap-2 text-xs font-semibold text-slate-200">
          <Layers size={16} className="text-blue-400" />
          <span>Local Agent Session</span>
        </div>

        <div className="h-4 w-px bg-slate-800" />

        <div className="flex items-center gap-1.5 text-xs">
          <span className="text-slate-400">Status:</span>
          {health?.ollama_connected ? (
            <span className="inline-flex items-center gap-1 text-[11px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full font-medium">
              <span className="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse"></span>
              Ollama Ready (Metal)
            </span>
          ) : (
            <span className="inline-flex items-center gap-1 text-[11px] text-amber-400 bg-amber-500/10 border border-amber-500/20 px-2 py-0.5 rounded-full font-medium">
              Ollama Standby
            </span>
          )}
        </div>
      </div>

      {/* Right: Model Selector & Panel Toggles */}
      <div className="flex items-center space-x-3">
        {/* Model dropdown */}
        <div className="flex items-center gap-2 bg-[#121a2d] border border-slate-700/60 rounded-lg px-2.5 py-1 text-xs">
          <Cpu size={14} className="text-indigo-400" />
          <span className="text-slate-400 text-[11px]">Model:</span>
          <select
            value={currentModel}
            onChange={(e) => onModelChange(e.target.value)}
            className="bg-transparent text-slate-200 font-mono text-xs focus:outline-none cursor-pointer"
          >
            {availableModels.length > 0 ? (
              availableModels.map((m) => (
                <option key={m} value={m} className="bg-[#0f172a] text-slate-200">
                  {m}
                </option>
              ))
            ) : (
              <>
                <option value="qwen2.5-coder:7b" className="bg-[#0f172a] text-slate-200">
                  qwen2.5-coder:7b (Recommended)
                </option>
                <option value="qwen3.5:4b" className="bg-[#0f172a] text-slate-200">
                  qwen3.5:4b
                </option>
              </>
            )}
          </select>
        </div>

        {/* Refresh Status */}
        <button
          onClick={onRefreshHealth}
          title="Refresh Ollama Connection"
          className="p-1.5 text-slate-400 hover:text-white hover:bg-slate-800 rounded-md transition-colors"
        >
          <RefreshCw size={14} />
        </button>

        {/* Workspace Explorer Toggle */}
        <button
          onClick={onToggleWorkspacePanel}
          className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-lg border transition-all ${
            showWorkspacePanel
              ? 'bg-blue-600/20 text-blue-300 border-blue-500/40 shadow-sm shadow-blue-500/10'
              : 'bg-[#121a2d] text-slate-300 border-slate-700/60 hover:bg-slate-800'
          }`}
        >
          <FolderGit2 size={14} className="text-blue-400" />
          <span>Workspace</span>
        </button>

        {/* Activity Panel Toggle */}
        <button
          onClick={onToggleActivityPanel}
          className={`flex items-center gap-1.5 px-2.5 py-1 text-xs font-medium rounded-lg border transition-all ${
            showActivityPanel
              ? 'bg-indigo-600/20 text-indigo-300 border-indigo-500/40 shadow-sm shadow-indigo-500/10'
              : 'bg-[#121a2d] text-slate-300 border-slate-700/60 hover:bg-slate-800'
          }`}
        >
          <Activity size={14} className="text-indigo-400" />
          <span>Tool Activity</span>
        </button>
      </div>
    </header>
  );
}

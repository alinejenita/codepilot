import React from 'react';
import { 
  Bot, 
  Terminal, 
  FolderGit2, 
  Cpu, 
  ShieldCheck, 
  Plus, 
  MessageSquare, 
  Sparkles,
  CheckCircle2,
  XCircle,
  HelpCircle
} from 'lucide-react';

export default function Sidebar({ 
  health, 
  sessions, 
  currentSessionId, 
  onSelectSession, 
  onNewSession,
  onSelectPromptTemplate 
}) {
  const templates = [
    { title: "Inspect workspace", prompt: "Inspect this project and explain its directory structure and files." },
    { title: "Create Python script", prompt: "Create a Python module in the workspace called math_utils.py with add, subtract, and multiply functions." },
    { title: "Run pytest", prompt: "Run pytest inside the workspace and tell me if all tests pass." },
    { title: "Find & fix bugs", prompt: "Search the workspace for any syntax or logic errors, propose fixes, and verify them." },
  ];

  return (
    <aside className="w-72 bg-[#0d121f] border-r border-[#1e293b] flex flex-col h-full select-none">
      {/* Brand Header */}
      <div className="p-4 border-b border-[#1e293b] flex items-center justify-between">
        <div className="flex items-center space-x-2.5">
          <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-blue-600 to-indigo-500 flex items-center justify-center text-white shadow-lg shadow-blue-500/20">
            <Bot size={20} />
          </div>
          <div>
            <h1 className="font-bold text-white text-base tracking-tight flex items-center gap-1.5">
              CodePilot
              <span className="text-[10px] bg-blue-500/10 text-blue-400 font-semibold px-1.5 py-0.5 rounded border border-blue-500/20">
                LOCAL
              </span>
            </h1>
            <p className="text-[11px] text-slate-400">Autonomous Coding Agent</p>
          </div>
        </div>
      </div>

      {/* New Task Action */}
      <div className="p-3">
        <button
          onClick={onNewSession}
          className="w-full flex items-center justify-center gap-2 px-3 py-2 text-xs font-semibold text-white bg-blue-600 hover:bg-blue-500 rounded-lg shadow-md transition-all active:scale-[0.98]"
        >
          <Plus size={15} />
          New Coding Task
        </button>
      </div>

      {/* Quick Starter Prompts */}
      <div className="px-3 py-2">
        <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5 px-1 flex items-center gap-1">
          <Sparkles size={12} className="text-amber-400" />
          Quick Actions
        </div>
        <div className="space-y-1">
          {templates.map((t, idx) => (
            <button
              key={idx}
              onClick={() => onSelectPromptTemplate(t.prompt)}
              className="w-full text-left px-2.5 py-1.5 rounded-md text-xs text-slate-300 hover:bg-[#1a2333] hover:text-white transition-colors truncate block"
              title={t.prompt}
            >
              • {t.title}
            </button>
          ))}
        </div>
      </div>

      {/* Recent Sessions */}
      <div className="flex-1 overflow-y-auto px-3 py-2">
        <div className="text-[11px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5 px-1">
          Recent Tasks
        </div>
        <div className="space-y-1">
          {sessions.map((sess) => (
            <button
              key={sess.id}
              onClick={() => onSelectSession(sess.id)}
              className={`w-full text-left px-2.5 py-2 rounded-lg text-xs flex items-center gap-2 transition-all ${
                sess.id === currentSessionId
                  ? 'bg-blue-600/15 text-blue-300 border border-blue-500/30'
                  : 'text-slate-400 hover:bg-[#1a2333] hover:text-slate-200'
              }`}
            >
              <MessageSquare size={14} className="shrink-0" />
              <span className="truncate">{sess.title || 'Untitled Task'}</span>
            </button>
          ))}
        </div>
      </div>

      {/* System Status & Guardrails Card */}
      <div className="p-3 border-t border-[#1e293b] bg-[#090d16]/70 text-[11px] space-y-2">
        <div className="flex items-center justify-between">
          <span className="text-slate-400 flex items-center gap-1.5">
            <Cpu size={13} className="text-indigo-400" />
            Ollama Engine
          </span>
          <span className="flex items-center gap-1 font-medium">
            {health?.ollama_connected ? (
              <>
                <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
                <span className="text-emerald-400">Online</span>
              </>
            ) : (
              <>
                <span className="w-2 h-2 rounded-full bg-rose-400"></span>
                <span className="text-rose-400">Offline</span>
              </>
            )}
          </span>
        </div>

        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center gap-1.5">
            <FolderGit2 size={13} className="text-blue-400" />
            Workspace
          </span>
          <span className="text-slate-200 font-mono text-[10px] bg-slate-800/80 px-1.5 py-0.5 rounded">
            {health?.workspace || './workspace'}
          </span>
        </div>

        <div className="flex items-center justify-between text-slate-400">
          <span className="flex items-center gap-1.5">
            <ShieldCheck size={13} className="text-emerald-400" />
            Containment
          </span>
          <span className="text-emerald-400 font-medium">Active (Sandboxed)</span>
        </div>

        <div className="pt-1.5 border-t border-slate-800/80 text-[10px] text-slate-400 flex items-center justify-between">
          <span>Target: MacBook M4 Metal</span>
          <span>Max Turns: 8</span>
        </div>
      </div>
    </aside>
  );
}

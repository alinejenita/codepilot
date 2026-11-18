import React, { useState } from 'react';
import { 
  SquarePen, 
  MessageSquare, 
  Trash2, 
  Cpu, 
  FolderGit2, 
  Sparkles, 
  ChevronRight,
  ShieldCheck,
  CheckCircle2,
  Clock
} from 'lucide-react';

export default function Sidebar({
  health,
  sessions,
  currentSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  onSelectPromptTemplate
}) {
  const [hoveredSession, setHoveredSession] = useState(null);

  const templates = [
    { title: "Inspect workspace structure", prompt: "Inspect this project and explain its directory structure and files." },
    { title: "Create Python math module", prompt: "Create a Python module in the workspace called math_utils.py with add, subtract, and multiply functions." },
    { title: "Run pytest test suite", prompt: "Run pytest inside the workspace and tell me if all tests pass." },
    { title: "Fix syntax & logic bugs", prompt: "Search the workspace for any syntax or logic errors, propose fixes, and verify them." },
  ];

  return (
    <aside className="w-68 bg-[#1e1e1c] border-r border-[#31312e] flex flex-col h-full select-none shrink-0 text-[#edece6]">
      {/* Brand Header */}
      <div className="p-3.5 flex items-center justify-between border-b border-[#2b2b28]">
        <div className="flex items-center space-x-2">
          <div className="w-7 h-7 rounded-lg bg-[#d97757] flex items-center justify-center text-white font-serif font-bold text-sm shadow-sm">
            C
          </div>
          <div>
            <h1 className="font-semibold text-sm tracking-tight text-[#f3f2ec]">
              CodePilot
            </h1>
            <p className="text-[10px] text-[#9c9a92]">Local AI Coding Agent</p>
          </div>
        </div>

        {/* Start new chat button */}
        <button
          onClick={onNewSession}
          title="New Chat"
          className="p-1.5 rounded-lg text-[#9c9a92] hover:text-[#edece6] hover:bg-[#2b2b28] transition-colors"
        >
          <SquarePen size={17} />
        </button>
      </div>

      {/* New Chat Primary Button */}
      <div className="p-3 pb-2">
        <button
          onClick={onNewSession}
          className="w-full flex items-center justify-between px-3 py-2 text-xs font-medium text-[#edece6] bg-[#292926] hover:bg-[#33332f] border border-[#383834] rounded-xl transition-all shadow-sm active:scale-[0.99]"
        >
          <span className="flex items-center gap-2">
            <SquarePen size={14} className="text-[#d97757]" />
            <span>Start new chat</span>
          </span>
          <span className="text-[10px] font-mono text-[#8a8880] bg-[#1e1e1c] px-1.5 py-0.5 rounded border border-[#383834]">
            ⌘K
          </span>
        </button>
      </div>

      {/* Chat History List */}
      <div className="flex-1 overflow-y-auto px-2 py-2 space-y-1">
        <div className="px-2 pt-1 pb-1.5 text-[11px] font-medium text-[#8a8880] flex items-center justify-between">
          <span>Recent Chats</span>
          <span className="text-[10px] font-mono">{sessions.length}</span>
        </div>

        {sessions.length === 0 ? (
          <div className="px-3 py-6 text-center text-xs text-[#8a8880]">
            No previous chats
          </div>
        ) : (
          sessions.map((sess) => {
            const isSelected = sess.id === currentSessionId;
            const traceCount = sess.messages?.reduce((acc, m) => acc + (m.steps?.length || 0), 0) || 0;

            return (
              <div
                key={sess.id}
                onMouseEnter={() => setHoveredSession(sess.id)}
                onMouseLeave={() => setHoveredSession(null)}
                className={`group relative flex items-center justify-between w-full px-2.5 py-2 rounded-xl text-xs transition-all cursor-pointer ${
                  isSelected
                    ? 'bg-[#292926] text-[#edece6] border border-[#3b3b36]'
                    : 'text-[#bbb9b0] hover:bg-[#252523] hover:text-[#edece6]'
                }`}
                onClick={() => onSelectSession(sess.id)}
              >
                <div className="flex items-center gap-2 min-w-0 pr-6">
                  <MessageSquare size={13} className={`shrink-0 ${isSelected ? 'text-[#d97757]' : 'text-[#8a8880]'}`} />
                  <div className="truncate">
                    <div className="truncate font-medium">{sess.title || 'Untitled task'}</div>
                    {traceCount > 0 && (
                      <div className="text-[10px] text-[#8a8880] flex items-center gap-1 font-mono">
                        <Clock size={9} />
                        <span>{traceCount} tool {traceCount === 1 ? 'trace' : 'traces'}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Delete chat button on hover */}
                {hoveredSession === sess.id && sessions.length > 1 && (
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteSession(sess.id);
                    }}
                    title="Delete chat"
                    className="absolute right-2 p-1 text-[#8a8880] hover:text-rose-400 hover:bg-[#33332f] rounded transition-colors"
                  >
                    <Trash2 size={12} />
                  </button>
                )}
              </div>
            );
          })
        )}
      </div>

      {/* Suggested Starters */}
      <div className="p-3 border-t border-[#2b2b28] bg-[#1b1b19]/60">
        <div className="text-[11px] font-medium text-[#8a8880] mb-1.5 px-1 flex items-center gap-1">
          <Sparkles size={11} className="text-[#d97757]" />
          <span>Quick Starters</span>
        </div>
        <div className="space-y-1">
          {templates.slice(0, 2).map((t, idx) => (
            <button
              key={idx}
              onClick={() => onSelectPromptTemplate(t.prompt)}
              className="w-full text-left px-2 py-1 rounded-lg text-[11px] text-[#9c9a92] hover:bg-[#262624] hover:text-[#edece6] truncate block transition-colors"
            >
              • {t.title}
            </button>
          ))}
        </div>
      </div>

      {/* Footer Status Panel */}
      <div className="p-3 border-t border-[#2b2b28] bg-[#181816] text-[11px] space-y-1.5">
        <div className="flex items-center justify-between">
          <span className="text-[#8a8880] flex items-center gap-1.5">
            <Cpu size={12} className="text-[#d97757]" />
            Local Model
          </span>
          <span className="font-mono text-[10px] text-[#edece6] bg-[#262624] px-1.5 py-0.5 rounded border border-[#333330]">
            {health?.model || 'qwen2.5-coder:7b'}
          </span>
        </div>

        <div className="flex items-center justify-between text-[#8a8880]">
          <span className="flex items-center gap-1.5">
            <FolderGit2 size={12} className="text-cyan-400" />
            Workspace
          </span>
          <span className="font-mono text-[10px] text-[#9c9a92]">
            {health?.workspace || './workspace'}
          </span>
        </div>

        <div className="flex items-center justify-between text-[#8a8880]">
          <span className="flex items-center gap-1.5">
            <ShieldCheck size={12} className="text-emerald-400" />
            Sandbox
          </span>
          <span className="flex items-center gap-1 text-[10px] text-emerald-400">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-400"></span>
            Contained
          </span>
        </div>
      </div>
    </aside>
  );
}

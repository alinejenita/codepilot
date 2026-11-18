import React from 'react';
import { 
  Activity, 
  Terminal, 
  Clock, 
  CheckCircle2, 
  XCircle, 
  Loader2, 
  ShieldCheck, 
  X,
  Code2
} from 'lucide-react';

export default function ToolActivityPanel({ onClose, steps = [] }) {
  return (
    <aside className="w-80 border-l border-[#1e293b] bg-[#0c111e] flex flex-col h-full shrink-0 select-none">
      <div className="p-4 border-b border-[#1e293b] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <Activity size={16} className="text-indigo-400" />
          <h2 className="font-semibold text-white text-xs tracking-tight">Agent Tool Activity</h2>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800 transition-colors"
        >
          <X size={15} />
        </button>
      </div>

      <div className="p-3 bg-[#080d19] border-b border-slate-800 text-[11px] text-slate-300 flex items-center justify-between">
        <span className="flex items-center gap-1.5">
          <ShieldCheck size={13} className="text-emerald-400" />
          Execution Sandbox
        </span>
        <span className="font-mono text-[10px] bg-slate-800 px-1.5 py-0.5 rounded text-emerald-300">
          STRICT ISOLATION
        </span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-3">
        {steps.length === 0 ? (
          <div className="text-center py-12 px-4 text-slate-400 text-xs">
            <Terminal size={32} className="mx-auto text-slate-600 mb-3 opacity-60" />
            <p className="font-medium text-slate-300">No tool actions yet</p>
            <p className="text-[11px] mt-1 text-slate-400">
              When you submit a coding task, CodePilot's tool calls (listing, reading, editing, testing) will appear here live.
            </p>
          </div>
        ) : (
          steps.map((step, idx) => (
            <div
              key={idx}
              className="p-3 bg-[#111827] border border-slate-800 rounded-lg text-xs space-y-2 shadow-sm"
            >
              <div className="flex items-center justify-between">
                <span className="font-mono font-semibold text-cyan-300 text-[11px] flex items-center gap-1.5">
                  <Code2 size={13} className="text-blue-400" />
                  {step.tool}
                </span>
                <span className="text-[10px]">
                  {step.status === 'completed' && (
                    <span className="text-emerald-400 flex items-center gap-1 font-medium">
                      <CheckCircle2 size={11} /> OK
                    </span>
                  )}
                  {step.status === 'running' && (
                    <span className="text-blue-400 flex items-center gap-1 font-medium">
                      <Loader2 size={11} className="animate-spin" /> RUN
                    </span>
                  )}
                  {step.status === 'failed' && (
                    <span className="text-rose-400 flex items-center gap-1 font-medium">
                      <XCircle size={11} /> ERR
                    </span>
                  )}
                </span>
              </div>

              {step.args && (
                <div className="text-[10px] font-mono text-slate-400 bg-[#090d18] p-1.5 rounded border border-slate-800/80 truncate">
                  args: {typeof step.args === 'string' ? step.args : JSON.stringify(step.args)}
                </div>
              )}

              {step.summary && (
                <div className="text-slate-300 text-[11px]">
                  {step.summary}
                </div>
              )}
            </div>
          ))
        )}
      </div>

      <div className="p-3 border-t border-[#1e293b] bg-[#090d16] text-[10px] text-slate-400 flex items-center justify-between">
        <span>Bounded loop: Max 8 steps</span>
        <span>Timeout: 30s</span>
      </div>
    </aside>
  );
}

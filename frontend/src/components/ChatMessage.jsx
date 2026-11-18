import React, { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { 
  Bot, 
  User, 
  Terminal, 
  FileText, 
  Search, 
  FileEdit, 
  FolderSearch, 
  ChevronDown, 
  ChevronRight, 
  CheckCircle2, 
  XCircle, 
  Loader2,
  Copy,
  Check
} from 'lucide-react';

function ToolIcon({ tool }) {
  switch (tool) {
    case 'list_files':
      return <FolderSearch size={14} className="text-cyan-400" />;
    case 'read_file':
      return <FileText size={14} className="text-amber-400" />;
    case 'search_files':
      return <Search size={14} className="text-purple-400" />;
    case 'write_file':
      return <FileEdit size={14} className="text-emerald-400" />;
    case 'run_command':
      return <Terminal size={14} className="text-orange-400" />;
    default:
      return <Terminal size={14} className="text-blue-400" />;
  }
}

function ToolCard({ step }) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <div className="my-2 border border-[#223049] rounded-lg bg-[#0e1626] overflow-hidden text-xs">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2 bg-[#121c2f] hover:bg-[#162238] transition-colors text-left"
      >
        <div className="flex items-center gap-2">
          <ToolIcon tool={step.tool} />
          <span className="font-mono font-medium text-slate-200">{step.tool}</span>
          {step.args && (
            <span className="text-[11px] font-mono text-slate-400 truncate max-w-xs">
              {typeof step.args === 'string' ? step.args : JSON.stringify(step.args)}
            </span>
          )}
        </div>

        <div className="flex items-center gap-2">
          {step.status === 'completed' && (
            <span className="inline-flex items-center gap-1 text-[10px] text-emerald-400 bg-emerald-500/10 border border-emerald-500/20 px-2 py-0.5 rounded-full font-medium">
              <CheckCircle2 size={11} /> Completed
            </span>
          )}
          {step.status === 'running' && (
            <span className="inline-flex items-center gap-1 text-[10px] text-blue-400 bg-blue-500/10 border border-blue-500/20 px-2 py-0.5 rounded-full font-medium animate-pulse">
              <Loader2 size={11} className="animate-spin" /> Running
            </span>
          )}
          {step.status === 'failed' && (
            <span className="inline-flex items-center gap-1 text-[10px] text-rose-400 bg-rose-500/10 border border-rose-500/20 px-2 py-0.5 rounded-full font-medium">
              <XCircle size={11} /> Failed
            </span>
          )}
          {isOpen ? <ChevronDown size={14} className="text-slate-400" /> : <ChevronRight size={14} className="text-slate-400" />}
        </div>
      </button>

      {isOpen && (
        <div className="p-3 bg-[#0a0f1d] border-t border-[#1e2c45] space-y-2">
          {step.args && (
            <div>
              <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Arguments:
              </div>
              <pre className="p-2 bg-[#060a13] rounded border border-slate-800 text-[11px] font-mono text-cyan-300 overflow-x-auto">
                {typeof step.args === 'string' ? step.args : JSON.stringify(step.args, null, 2)}
              </pre>
            </div>
          )}

          {step.summary && (
            <div>
              <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Summary:
              </div>
              <div className="text-slate-300 text-xs">
                {step.summary}
              </div>
            </div>
          )}

          {step.result && (
            <div>
              <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
                Output Data:
              </div>
              <pre className="p-2 bg-[#060a13] rounded border border-slate-800 text-[11px] font-mono text-slate-300 overflow-x-auto max-h-48">
                {typeof step.result === 'string' ? step.result : JSON.stringify(step.result, null, 2)}
              </pre>
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className={`py-4 px-6 ${isUser ? 'bg-[#0b101c]/40' : 'bg-[#0f172a]/30 border-y border-[#182338]/40'}`}>
      <div className="max-w-3xl mx-auto flex items-start gap-4">
        {/* Avatar */}
        <div
          className={`w-8 h-8 rounded-lg shrink-0 flex items-center justify-center text-white ${
            isUser
              ? 'bg-gradient-to-tr from-slate-600 to-slate-500'
              : 'bg-gradient-to-tr from-blue-600 to-indigo-600 shadow-md shadow-blue-500/20'
          }`}
        >
          {isUser ? <User size={16} /> : <Bot size={16} />}
        </div>

        {/* Content Body */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center justify-between mb-1.5">
            <span className="text-xs font-semibold text-slate-200">
              {isUser ? 'You' : 'CodePilot AI'}
            </span>
            {message.timestamp && (
              <span className="text-[10px] text-slate-400">{message.timestamp}</span>
            )}
          </div>

          {/* Tool Calls Executed by Agent */}
          {message.steps && message.steps.length > 0 && (
            <div className="my-2">
              <div className="text-[11px] font-medium text-slate-400 mb-1 flex items-center gap-1.5">
                <Terminal size={12} className="text-blue-400" />
                Executed {message.steps.length} Tool Actions:
              </div>
              {message.steps.map((step, idx) => (
                <ToolCard key={idx} step={step} />
              ))}
            </div>
          )}

          {/* Main Message Text / Markdown */}
          <div className="prose prose-invert prose-sm max-w-none text-slate-200 leading-relaxed break-words">
            <ReactMarkdown
              components={{
                code({ node, inline, className, children, ...props }) {
                  const match = /language-(\w+)/.exec(className || '');
                  return !inline ? (
                    <div className="relative my-3 rounded-lg overflow-hidden border border-slate-700/60 bg-[#080d19]">
                      <div className="flex items-center justify-between px-3 py-1.5 bg-[#101728] border-b border-slate-700/60 text-[11px] text-slate-400 font-mono">
                        <span>{match ? match[1] : 'code'}</span>
                        <button
                          onClick={() => copyToClipboard(String(children).replace(/\n$/, ''))}
                          className="flex items-center gap-1 hover:text-white transition-colors"
                        >
                          {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                          <span>{copied ? 'Copied' : 'Copy'}</span>
                        </button>
                      </div>
                      <pre className="p-3 text-xs font-mono text-slate-200 overflow-x-auto m-0">
                        <code>{children}</code>
                      </pre>
                    </div>
                  ) : (
                    <code className="bg-[#182338] text-cyan-300 font-mono px-1.5 py-0.5 rounded text-[12px]" {...props}>
                      {children}
                    </code>
                  );
                },
                table({ children }) {
                  return (
                    <div className="overflow-x-auto my-3 border border-slate-700/60 rounded-lg">
                      <table className="min-w-full divide-y divide-slate-700 text-xs text-left">
                        {children}
                      </table>
                    </div>
                  );
                },
                th({ children }) {
                  return <th className="px-3 py-2 bg-[#121c2f] font-semibold text-slate-200">{children}</th>;
                },
                td({ children }) {
                  return <td className="px-3 py-2 border-t border-slate-800 text-slate-300">{children}</td>;
                }
              }}
            >
              {message.content}
            </ReactMarkdown>
          </div>
        </div>
      </div>
    </div>
  );
}

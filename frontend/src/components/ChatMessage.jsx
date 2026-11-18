import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import { 
  Copy, 
  Check, 
  ChevronDown, 
  ChevronRight, 
  Terminal, 
  FolderSearch, 
  FileText, 
  FileEdit, 
  Search, 
  CheckCircle2, 
  XCircle, 
  Wrench
} from 'lucide-react';

function getToolIcon(tool) {
  switch (tool) {
    case 'list_files':
      return <FolderSearch size={13} className="text-cyan-400" />;
    case 'read_file':
      return <FileText size={13} className="text-amber-400" />;
    case 'run_tests':
      return <Terminal size={13} className="text-orange-400" />;
    case 'search_files':
      return <Search size={13} className="text-purple-400" />;
    case 'write_file':
      return <FileEdit size={13} className="text-emerald-400" />;
    case 'run_command':
      return <Terminal size={13} className="text-orange-400" />;
    default:
      return <Wrench size={13} className="text-[#d97757]" />;
  }
}

/**
 * Claude-style collapsible Execution Trace block
 */
function ExecutionTracePill({ steps = [] }) {
  const [isOpen, setIsOpen] = useState(false);
  if (!steps || steps.length === 0) return null;

  const toolNames = Array.from(new Set(steps.map((s) => s.tool))).join(', ');
  const hasFailure = steps.some((step) => step.status === 'failed');

  return (
    <div className="my-2.5 rounded-xl border border-[#33332f] bg-[#222220] overflow-hidden text-xs transition-all">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-3 py-2 text-[#9c9a92] hover:text-[#edece6] hover:bg-[#282825] transition-colors text-left"
      >
        <div className="flex items-center gap-2">
          <span className="w-5 h-5 rounded-md bg-[#2b2b27] flex items-center justify-center text-[#d97757]">
            <Wrench size={12} />
          </span>
          <span className="font-medium text-[#edece6]">
            Tool Execution Trace ({steps.length} {steps.length === 1 ? 'step' : 'steps'})
          </span>
          <span className="text-[11px] font-mono text-[#8a8880] hidden sm:inline">
            — {toolNames}
          </span>
        </div>

        <div className="flex items-center gap-2">
          <span className={`inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full font-medium ${
            hasFailure ? 'text-rose-400 bg-rose-500/10' : 'text-emerald-400 bg-emerald-500/10'
          }`}>
            {hasFailure ? <XCircle size={10} /> : <CheckCircle2 size={10} />}
            {hasFailure ? 'some actions failed' : 'completed'}
          </span>
          {isOpen ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </div>
      </button>

      {isOpen && (
        <div className="p-3 bg-[#1c1c1a] border-t border-[#2d2d2a] space-y-2.5">
          {steps.map((step, idx) => (
            <div
              key={idx}
              className="p-2.5 rounded-lg bg-[#242422] border border-[#333330] space-y-1.5"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  {getToolIcon(step.tool)}
                  <span className="font-mono font-semibold text-[#edece6] text-[11px]">
                    {step.tool}
                  </span>
                </div>
                <span className={`text-[10px] font-mono ${
                  step.status === 'failed' ? 'text-rose-400' : 'text-emerald-400'
                }`}>
                  {step.status === 'failed' ? '✗' : '✓'} {step.status}
                </span>
              </div>

              {step.args && (
                <div className="text-[10px] font-mono text-[#a5a49c] bg-[#1a1a18] p-1.5 rounded border border-[#2e2e2b]">
                  <span className="text-[#8a8880]">arguments: </span>
                  {typeof step.args === 'string' ? step.args : JSON.stringify(step.args)}
                </div>
              )}

              {step.summary && (
                <div className="text-[11px] text-[#bbb9b0]">
                  {step.summary}
                </div>
              )}

              {step.result && (
                <div>
                  <div className="text-[9px] font-semibold text-[#8a8880] uppercase tracking-wider mb-0.5">
                    Output:
                  </div>
                  <pre className="p-2 bg-[#171715] rounded border border-[#2b2b28] text-[10px] font-mono text-cyan-300 overflow-x-auto max-h-36">
                    {typeof step.result === 'string' ? step.result : JSON.stringify(step.result, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

// Strip any raw tool-call JSON/XML the model might have leaked into the reply
const TOOL_CALL_RE = [
  /\{"?name"?\s*:\s*"(?:list_files|read_file|search_files|run_command|write_file|run_tests)".*?\}/gs,
  /<tool_call>.*?<\/tool_call>/gis,
  /<function=\w+>.*?<\/function>/gis,
];

function cleanContent(text) {
  if (!text) return text;
  let out = text;
  for (const re of TOOL_CALL_RE) out = out.replace(re, '');
  return out.replace(/\n{3,}/g, '\n\n').trim();
}

export default function ChatMessage({ message }) {
  const isUser = message.role === 'user';
  const [copied, setCopied] = useState(false);

  const copyToClipboard = (text) => {
    navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  if (isUser) {
    return (
      <div className="py-3 px-4 sm:px-6">
        <div className="max-w-3xl mx-auto flex justify-end">
          <div className="max-w-[85%] sm:max-w-[75%] rounded-2xl px-4 py-2.5 bg-[#2b2a27] text-[#edece6] text-sm leading-relaxed border border-[#383734] shadow-sm">
            <div className="whitespace-pre-wrap">{message.content}</div>
            {message.timestamp && (
              <div className="text-[10px] text-[#8a8880] text-right mt-1">
                {message.timestamp}
              </div>
            )}
          </div>
        </div>
      </div>
    );
  }

  // Assistant Message (Claude Style: clean text block, warm styling, collapsible traces)
  return (
    <div className="py-4 px-4 sm:px-6">
      <div className="max-w-3xl mx-auto">
        {/* Assistant Header: Claude style icon + label */}
        <div className="flex items-center gap-2 mb-2 text-xs text-[#9c9a92]">
          <div className="w-5 h-5 rounded-md bg-[#d97757] flex items-center justify-center text-white font-serif font-bold text-[10px] shadow-sm">
            C
          </div>
          <span className="font-semibold text-[#edece6]">CodePilot</span>
          {message.timestamp && (
            <span className="text-[10px] text-[#8a8880]">• {message.timestamp}</span>
          )}
        </div>

        {/* Collapsible Tool Execution Trace Pill */}
        {message.steps && message.steps.length > 0 && (
          <ExecutionTracePill steps={message.steps} />
        )}

        {/* Markdown Content */}
        <div className="prose prose-invert prose-sm max-w-none text-[#edece6] leading-relaxed text-sm">
          <ReactMarkdown
            components={{              code({ inline, className, children, ...props }) {
                const match = /language-(\w+)/.exec(className || '');
                return !inline ? (
                  <div className="relative my-3 rounded-xl overflow-hidden border border-[#383834] bg-[#1a1a18]">
                    <div className="flex items-center justify-between px-3 py-1.5 bg-[#232320] border-b border-[#33332f] text-[11px] text-[#9c9a92] font-mono">
                      <span>{match ? match[1] : 'code'}</span>
                      <button
                        onClick={() => copyToClipboard(String(children).replace(/\n$/, ''))}
                        className="flex items-center gap-1 hover:text-white transition-colors"
                      >
                        {copied ? <Check size={12} className="text-emerald-400" /> : <Copy size={12} />}
                        <span>{copied ? 'Copied' : 'Copy'}</span>
                      </button>
                    </div>
                    <pre className="p-3.5 text-xs font-mono text-[#f3f2ec] overflow-x-auto m-0">
                      <code>{children}</code>
                    </pre>
                  </div>
                ) : (
                  <code className="bg-[#262624] text-[#d97757] font-mono px-1.5 py-0.5 rounded text-[12px] border border-[#363632]" {...props}>
                    {children}
                  </code>
                );
              },
              p({ children }) {
                return <p className="mb-3 last:mb-0 text-[#edece6] leading-relaxed">{children}</p>;
              },
              ul({ children }) {
                return <ul className="list-disc pl-5 my-2 space-y-1 text-[#edece6]">{children}</ul>;
              },
              ol({ children }) {
                return <ol className="list-decimal pl-5 my-2 space-y-1 text-[#edece6]">{children}</ol>;
              },
              li({ children }) {
                return <li className="text-[#edece6]">{children}</li>;
              },
              h1({ children }) {
                return <h1 className="text-lg font-semibold text-[#f3f2ec] mt-4 mb-2">{children}</h1>;
              },
              h2({ children }) {
                return <h2 className="text-base font-semibold text-[#f3f2ec] mt-3 mb-1.5">{children}</h2>;
              },
              h3({ children }) {
                return <h3 className="text-sm font-semibold text-[#f3f2ec] mt-2 mb-1">{children}</h3>;
              },
              table({ children }) {
                return (
                  <div className="overflow-x-auto my-3 border border-[#363632] rounded-xl">
                    <table className="min-w-full divide-y divide-[#363632] text-xs text-left">
                      {children}
                    </table>
                  </div>
                );
              },
              th({ children }) {
                return <th className="px-3 py-2 bg-[#232320] font-semibold text-[#edece6]">{children}</th>;
              },
              td({ children }) {
                return <td className="px-3 py-2 border-t border-[#2e2e2b] text-[#bbb9b0]">{children}</td>;
              }
            }}
          >
            {cleanContent(message.content)}
          </ReactMarkdown>
        </div>
      </div>
    </div>
  );
}

import React, { useState } from 'react';
import { FolderGit2, FileCode, File, X, RefreshCw, Eye } from 'lucide-react';

export default function WorkspacePanel({ onClose, workspaceFiles = ['hello_world.py', '.gitkeep'] }) {
  const [selectedFile, setSelectedFile] = useState('hello_world.py');

  const sampleContents = {
    'hello_world.py': "# Hello from CodePilot workspace\nprint('Hello, world!')\n",
    '.gitkeep': '# Gitkeep marker for workspace root\n',
  };

  return (
    <aside className="w-80 border-l border-[#1e293b] bg-[#0c111e] flex flex-col h-full shrink-0 select-none">
      <div className="p-4 border-b border-[#1e293b] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FolderGit2 size={16} className="text-blue-400" />
          <h2 className="font-semibold text-white text-xs tracking-tight">Workspace Files</h2>
        </div>
        <button
          onClick={onClose}
          className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800 transition-colors"
        >
          <X size={15} />
        </button>
      </div>

      <div className="p-3 bg-[#080d19] border-b border-slate-800 text-[11px] text-slate-400 flex items-center justify-between">
        <span>Root: ./workspace</span>
        <span className="font-mono text-[10px] text-cyan-400">{workspaceFiles.length} files</span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        {workspaceFiles.map((file) => (
          <button
            key={file}
            onClick={() => setSelectedFile(file)}
            className={`w-full flex items-center justify-between px-2.5 py-1.5 rounded-lg text-xs font-mono transition-all ${
              selectedFile === file
                ? 'bg-blue-600/20 text-blue-300 border border-blue-500/30'
                : 'text-slate-300 hover:bg-[#151f33]'
            }`}
          >
            <div className="flex items-center gap-2 truncate">
              {file.endsWith('.py') ? (
                <FileCode size={14} className="text-amber-400 shrink-0" />
              ) : (
                <File size={14} className="text-slate-400 shrink-0" />
              )}
              <span className="truncate">{file}</span>
            </div>
            <Eye size={12} className="text-slate-400" />
          </button>
        ))}

        {selectedFile && (
          <div className="mt-4 pt-4 border-t border-slate-800">
            <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1 flex items-center justify-between">
              <span>Preview: {selectedFile}</span>
            </div>
            <pre className="p-2.5 bg-[#070b14] rounded-lg border border-slate-800 text-[11px] font-mono text-emerald-300 overflow-x-auto max-h-56">
              {sampleContents[selectedFile] || '# File loaded from workspace\n'}
            </pre>
          </div>
        )}
      </div>

      <div className="p-3 border-t border-[#1e293b] bg-[#090d16] text-[10px] text-slate-400">
        Workspace containment prevents editing outside this directory.
      </div>
    </aside>
  );
}

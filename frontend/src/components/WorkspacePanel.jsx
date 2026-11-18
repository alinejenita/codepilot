import { useEffect, useState } from 'react';
import { FolderGit2, FileCode, File, X, RefreshCw, Eye } from 'lucide-react';
import { fetchWorkspace, fetchWorkspaceFile } from '../services/api';

export default function WorkspacePanel({ onClose }) {
  const [workspace, setWorkspace] = useState('./workspace');
  const [files, setFiles] = useState([]);
  const [selectedFile, setSelectedFile] = useState('');
  const [content, setContent] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const loadWorkspace = async () => {
    try {
      const data = await fetchWorkspace();
      setWorkspace(data.workspace);
      setFiles(data.files);
      setError('');
      setSelectedFile((current) => data.files.includes(current) ? current : (data.files[0] || ''));
    } catch (loadError) {
      setError(loadError.message);
    }
  };

  useEffect(() => {
    loadWorkspace();
  }, []);

  useEffect(() => {
    if (!selectedFile) {
      setContent('');
      return;
    }
    let active = true;
    setLoading(true);
    fetchWorkspaceFile(selectedFile)
      .then((data) => {
        if (active) {
          setContent(data.content);
          setError('');
        }
      })
      .catch((loadError) => {
        if (active) setError(loadError.message);
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [selectedFile]);

  return (
    <aside className="w-80 border-l border-[#1e293b] bg-[#0c111e] flex flex-col h-full shrink-0 select-none">
      <div className="p-4 border-b border-[#1e293b] flex items-center justify-between">
        <div className="flex items-center gap-2">
          <FolderGit2 size={16} className="text-blue-400" />
          <h2 className="font-semibold text-white text-xs tracking-tight">Workspace Files</h2>
        </div>
        <div className="flex items-center gap-1">
          <button onClick={loadWorkspace} title="Refresh files" className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800">
            <RefreshCw size={14} />
          </button>
          <button onClick={onClose} title="Close workspace" className="text-slate-400 hover:text-white p-1 rounded-md hover:bg-slate-800">
            <X size={15} />
          </button>
        </div>
      </div>

      <div className="p-3 bg-[#080d19] border-b border-slate-800 text-[11px] text-slate-400 flex items-center justify-between gap-2">
        <span className="truncate" title={workspace}>Root: {workspace}</span>
        <span className="font-mono text-[10px] text-cyan-400 shrink-0">{files.length} files</span>
      </div>

      <div className="flex-1 overflow-y-auto p-3 space-y-1">
        {error && <p className="text-xs text-rose-400 break-words">{error}</p>}
        {files.map((file) => (
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
              {file.endsWith('.py') || file.endsWith('.js') || file.endsWith('.jsx') ? (
                <FileCode size={14} className="text-amber-400 shrink-0" />
              ) : (
                <File size={14} className="text-slate-400 shrink-0" />
              )}
              <span className="truncate">{file}</span>
            </div>
            <Eye size={12} className="text-slate-400" />
          </button>
        ))}
        {!error && files.length === 0 && (
          <p className="py-6 text-center text-xs text-slate-400">No files in this workspace.</p>
        )}

        {selectedFile && (
          <div className="mt-4 pt-4 border-t border-slate-800">
            <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1">
              Preview: {selectedFile}
            </div>
            <pre className="p-2.5 bg-[#070b14] rounded-lg border border-slate-800 text-[11px] font-mono text-emerald-300 overflow-x-auto max-h-56 whitespace-pre-wrap">
              {loading ? 'Loading…' : content}
            </pre>
          </div>
        )}
      </div>

      <div className="p-3 border-t border-[#1e293b] bg-[#090d16] text-[10px] text-slate-400">
        File reads and edits are confined to this workspace.
      </div>
    </aside>
  );
}

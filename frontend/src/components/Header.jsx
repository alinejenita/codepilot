import React from 'react';
import { 
  PanelLeft, 
  FolderGit2, 
  Cpu, 
  RefreshCw,
  Sparkles,
  ChevronDown
} from 'lucide-react';

export default function Header({
  currentModel,
  onModelChange,
  availableModels = [],
  health,
  onRefreshHealth,
  showWorkspacePanel,
  onToggleWorkspacePanel,
  isSidebarOpen,
  onToggleSidebar,
  currentChatTitle = "New Chat"
}) {
  return (
    <header className="h-13 border-b border-[#31312e] bg-[#181816]/95 backdrop-blur px-4 flex items-center justify-between shrink-0 z-10 text-[#edece6]">
      {/* Left: Sidebar toggle & Title */}
      <div className="flex items-center gap-3 min-w-0">
        <button
          onClick={onToggleSidebar}
          title="Toggle Sidebar"
          className="p-1.5 rounded-lg text-[#9c9a92] hover:text-[#edece6] hover:bg-[#262624] transition-colors"
        >
          <PanelLeft size={17} />
        </button>

        <h2 className="text-xs font-medium text-[#edece6] truncate max-w-xs sm:max-w-md">
          {currentChatTitle}
        </h2>
      </div>

      {/* Right: Model Pill & Workspace Toggle */}
      <div className="flex items-center gap-2">
        {/* Claude-style Model Pill Selector */}
        <div className="relative flex items-center gap-1.5 bg-[#242422] hover:bg-[#2b2b28] border border-[#383834] rounded-full px-3 py-1 text-xs transition-colors">
          <span className="w-2 h-2 rounded-full bg-[#d97757]"></span>
          <select
            value={currentModel}
            onChange={(e) => onModelChange(e.target.value)}
            className="bg-transparent text-[#edece6] font-mono text-[11px] focus:outline-none cursor-pointer pr-4 appearance-none"
          >
            {availableModels.length > 0 ? (
              availableModels.map((m) => (
                <option key={m} value={m} className="bg-[#1f1f1d] text-[#edece6]">
                  {m}
                </option>
              ))
            ) : (
              <>
                <option value="qwen2.5-coder:7b" className="bg-[#1f1f1d] text-[#edece6]">
                  qwen2.5-coder:7b (Recommended)
                </option>
                <option value="qwen3.5:4b" className="bg-[#1f1f1d] text-[#edece6]">
                  qwen3.5:4b
                </option>
              </>
            )}
          </select>
          <ChevronDown size={11} className="text-[#8a8880] pointer-events-none -ml-3" />
        </div>

        {/* Workspace explorer pill */}
        <button
          onClick={onToggleWorkspacePanel}
          className={`flex items-center gap-1.5 px-3 py-1 text-xs rounded-full border transition-all ${
            showWorkspacePanel
              ? 'bg-[#d97757]/15 text-[#e08465] border-[#d97757]/40 font-medium'
              : 'bg-[#242422] text-[#9c9a92] border-[#383834] hover:text-[#edece6] hover:bg-[#2b2b28]'
          }`}
          title="Toggle Workspace File Explorer"
        >
          <FolderGit2 size={13} className="text-cyan-400" />
          <span className="text-[11px] font-mono hidden sm:inline">./workspace</span>
        </button>

        {/* Refresh status */}
        <button
          onClick={onRefreshHealth}
          title="Refresh connection"
          className="p-1.5 text-[#8a8880] hover:text-[#edece6] hover:bg-[#262624] rounded-lg transition-colors"
        >
          <RefreshCw size={13} />
        </button>
      </div>
    </header>
  );
}

import { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ChatMessage from './components/ChatMessage';
import WorkspacePanel from './components/WorkspacePanel';
import { fetchHealth, sendChatMessage } from './services/api';
import { ArrowUp, Loader2, FolderSearch, Terminal, FileCode2 } from 'lucide-react';

const STORAGE_KEY = 'codepilot_chat_sessions_v2';
const CURRENT_ID_KEY = 'codepilot_current_session_id_v2';

const DEFAULT_WELCOME_MESSAGE = {
  id: 'welcome-msg',
  role: 'assistant',
  content: `I am **CodePilot**, your local coding agent running through Ollama.

I can inspect and search your configured workspace. Enable **Allow file edits** to create or replace files, or **Allow pytest** to run tests in a trusted workspace. General shell commands are not available.

Ask me a question or try one of the suggestions below to get started.`,
  timestamp: 'Just now',
  steps: [],
};

export default function App() {
  // Load sessions from localStorage or initialize with default
  const [sessions, setSessions] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) return parsed;
      }
    } catch (e) {
      console.warn('Could not parse saved sessions:', e);
    }
    return [
      {
        id: 'session-default',
        title: 'Inspect workspace files',
        createdAt: new Date().toISOString(),
        messages: [DEFAULT_WELCOME_MESSAGE],
      },
    ];
  });

  const [currentSessionId, setCurrentSessionId] = useState(() => {
    try {
      const savedId = localStorage.getItem(CURRENT_ID_KEY);
      if (savedId) return savedId;
    } catch (error) {
      console.warn('Could not read the saved session ID:', error);
    }
    return 'session-default';
  });

  const [currentModel, setCurrentModel] = useState('qwen2.5-coder:7b');
  const [health, setHealth] = useState(null);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [allowEdits, setAllowEdits] = useState(false);
  const [allowTests, setAllowTests] = useState(false);
  const [isSidebarOpen, setIsSidebarOpen] = useState(true);
  const [showWorkspacePanel, setShowWorkspacePanel] = useState(false);
  const messagesEndRef = useRef(null);

  // Sync sessions to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(sessions));
    } catch (e) {
      console.warn('Failed to save sessions:', e);
    }
  }, [sessions]);

  // Sync currentSessionId to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(CURRENT_ID_KEY, currentSessionId);
    } catch (error) {
      console.warn('Could not save the current session ID:', error);
    }
  }, [currentSessionId]);

  // Check backend and Ollama health
  useEffect(() => {
    loadHealth();
    const interval = setInterval(loadHealth, 10000);
    return () => clearInterval(interval);
  }, []);

  const loadHealth = async () => {
    const data = await fetchHealth();
    setHealth(data);
    if (data.model) setCurrentModel(data.model);
  };

  const currentSession = sessions.find((s) => s.id === currentSessionId) || sessions[0];

  // Auto-scroll on new message
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentSession?.messages, isLoading]);

  const handleNewSession = () => {
    const newId = `session-${Date.now()}`;
    const newSession = {
      id: newId,
      title: 'New chat',
      createdAt: new Date().toISOString(),
      messages: [DEFAULT_WELCOME_MESSAGE],
    };
    setSessions([newSession, ...sessions]);
    setCurrentSessionId(newId);
  };

  const handleDeleteSession = (idToDelete) => {
    const remaining = sessions.filter((s) => s.id !== idToDelete);
    if (remaining.length === 0) {
      const freshId = `session-${Date.now()}`;
      setSessions([{
        id: freshId,
        title: 'New chat',
        createdAt: new Date().toISOString(),
        messages: [DEFAULT_WELCOME_MESSAGE],
      }]);
      setCurrentSessionId(freshId);
    } else {
      setSessions(remaining);
      if (currentSessionId === idToDelete) {
        setCurrentSessionId(remaining[0].id);
      }
    }
  };

  const handleSendMessage = async (textToSend) => {
    const prompt = (textToSend || inputValue).trim();
    if (!prompt || isLoading) return;

    const allowEditsForRequest = allowEdits;
    const allowTestsForRequest = allowTests;
    setInputValue('');
    setAllowEdits(false);
    setAllowTests(false);
    const userMsgId = `usr-${Date.now()}`;
    const assistantMsgId = `asst-${Date.now()}`;
    const timeString = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // 1. Add user message
    const updatedMessages = [
      ...currentSession.messages,
      {
        id: userMsgId,
        role: 'user',
        content: prompt,
        timestamp: timeString,
      },
    ];

    // Compute title from first prompt if needed
    const isFirstUserMsg = currentSession.messages.filter(m => m.role === 'user').length === 0;
    const updatedTitle = isFirstUserMsg
      ? (prompt.length > 36 ? prompt.slice(0, 36) + '...' : prompt)
      : currentSession.title;

    setSessions((prev) =>
      prev.map((s) =>
        s.id === currentSessionId
          ? { ...s, title: updatedTitle, messages: updatedMessages }
          : s
      )
    );

    setIsLoading(true);

    try {
      // Build conversation history (excluding initial welcome banner)
      const historyPayload = currentSession.messages
        .filter((m) => m.id !== 'welcome-msg')
        .map((m) => ({ role: m.role, content: m.content }));

      // 2. Call FastAPI backend (/api/chat) with history and workspace
      const data = await sendChatMessage({
        message: prompt,
        model: currentModel,
        history: historyPayload,
        workspace: currentSession.workspace,
        allowEdits: allowEditsForRequest,
        allowTests: allowTestsForRequest,
      });

      const assistantMsg = {
        id: assistantMsgId,
        role: 'assistant',
        content: data.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        steps: data.steps || [],
      };

      setSessions((prev) =>
        prev.map((s) =>
          s.id === currentSessionId
            ? {
                ...s,
                workspace: data.workspace || s.workspace,
                messages: [...updatedMessages, assistantMsg],
              }
            : s
        )
      );
    } catch (err) {
      const fallbackMsg = {
        id: assistantMsgId,
        role: 'assistant',
        content: `I received your prompt: "${prompt}".

The backend or model adapter encountered an error: \`${err.message}\`.
Make sure the backend is active at \`http://127.0.0.1:8000\` and Ollama is running.`,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        steps: [],
      };

      setSessions((prev) =>
        prev.map((s) =>
          s.id === currentSessionId
            ? { ...s, messages: [...updatedMessages, fallbackMsg] }
            : s
        )
      );
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const promptStarters = [
    { label: "Inspect workspace structure", icon: <FolderSearch size={14} className="text-cyan-400" /> },
    { label: "Search for a function or symbol", icon: <FileCode2 size={14} className="text-emerald-400" /> },
    { label: "Explain a file in the workspace", icon: <Terminal size={14} className="text-orange-400" /> },
  ];

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#181816] text-[#edece6]">
      {/* Claude-style Left Sidebar */}
      {isSidebarOpen && (
        <Sidebar
          health={health}
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSelectSession={setCurrentSessionId}
          onNewSession={handleNewSession}
          onDeleteSession={handleDeleteSession}
          onSelectPromptTemplate={(t) => handleSendMessage(t)}
        />
      )}

      {/* Main Chat Column */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden bg-[#181816]">
        {/* Top Minimalist Header */}
        <Header
          currentModel={currentModel}
          onModelChange={setCurrentModel}
          availableModels={health?.available_models}
          health={health}
          onRefreshHealth={loadHealth}
          showWorkspacePanel={showWorkspacePanel}
          onToggleWorkspacePanel={() => setShowWorkspacePanel(!showWorkspacePanel)}
          isSidebarOpen={isSidebarOpen}
          onToggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
          currentChatTitle={currentSession?.title}
        />

        {/* Conversation Feed */}
        <div className="flex-1 overflow-y-auto min-h-0 pt-2 pb-6">
          <div className="space-y-1">
            {currentSession?.messages?.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}

            {/* Thinking / Tool Execution Indicator */}
            {isLoading && (
              <div className="py-4 px-4 sm:px-6">
                <div className="max-w-3xl mx-auto flex items-center gap-2.5 text-xs text-[#9c9a92]">
                  <div className="w-5 h-5 rounded-md bg-[#2b2b27] border border-[#383834] flex items-center justify-center text-[#d97757]">
                    <Loader2 size={12} className="animate-spin" />
                  </div>
                  <span className="font-medium text-[#edece6]">
                    CodePilot is planning actions & running tools...
                  </span>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Claude-style Floating Bottom Composer */}
        <div className="px-4 pb-5 pt-2 bg-gradient-to-t from-[#181816] via-[#181816] to-transparent shrink-0">
          <div className="max-w-3xl mx-auto space-y-2.5">
            {/* Quick Starters (shown if only welcome message present) */}
            {currentSession?.messages?.length <= 1 && (
              <div className="flex flex-wrap gap-2 pb-1">
                {promptStarters.map((starter, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleSendMessage(starter.label)}
                    className="flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs bg-[#242422] hover:bg-[#2e2e2b] text-[#bbb9b0] hover:text-[#edece6] border border-[#383834] transition-all shadow-sm"
                  >
                    {starter.icon}
                    <span>{starter.label}</span>
                  </button>
                ))}
              </div>
            )}

            {/* Claude-style Rounded Card Composer */}
            <div className="relative rounded-2xl bg-[#242422] border border-[#383834] focus-within:border-[#4f4f49] focus-within:shadow-md transition-all shadow-lg p-3">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Reply to CodePilot or describe a coding task..."
                rows={2}
                className="w-full bg-transparent text-sm text-[#edece6] placeholder-[#8a8880] resize-none focus:outline-none pr-12 leading-relaxed"
              />

              <div className="flex items-center justify-between pt-1 border-t border-[#2e2e2b] text-[11px] text-[#8a8880]">
                <div className="flex items-center gap-2">
                  <span className="font-mono text-[10px] bg-[#1a1a18] px-2 py-0.5 rounded text-[#bbb9b0] border border-[#33332f]">
                    {currentModel}
                  </span>
                  <label className="flex items-center gap-1.5 cursor-pointer select-none" title="Allow CodePilot to create or replace files inside the configured workspace for the next request.">
                    <input
                      type="checkbox"
                      checked={allowEdits}
                      onChange={(event) => setAllowEdits(event.target.checked)}
                      disabled={isLoading}
                      className="accent-[#d97757]"
                    />
                    <span>Allow file edits</span>
                  </label>
                  <label className="flex items-center gap-1.5 cursor-pointer select-none" title="Pytest runs project code and configuration. Enable only for a workspace you trust.">
                    <input
                      type="checkbox"
                      checked={allowTests}
                      onChange={(event) => setAllowTests(event.target.checked)}
                      disabled={isLoading}
                      className="accent-[#d97757]"
                    />
                    <span>Allow pytest</span>
                  </label>
                </div>

                {/* Claude-style Round Terracotta Send Button */}
                <button
                  onClick={() => handleSendMessage()}
                  disabled={!inputValue.trim() || isLoading}
                  className={`w-7 h-7 rounded-full flex items-center justify-center transition-all ${
                    inputValue.trim() && !isLoading
                      ? 'bg-[#d97757] hover:bg-[#e28567] text-white shadow-md active:scale-95'
                      : 'bg-[#31312d] text-[#6e6d67] cursor-not-allowed'
                  }`}
                  title="Send message"
                >
                  <ArrowUp size={15} />
                </button>
              </div>
            </div>

            <div className="text-center text-[11px] text-[#8a8880]">
              CodePilot executes locally via Ollama. Always inspect generated code before deployment.
            </div>
          </div>
        </div>
      </div>

      {/* Workspace Panel Right Drawer */}
      {showWorkspacePanel && (
        <WorkspacePanel
          onClose={() => setShowWorkspacePanel(false)}
        />
      )}
    </div>
  );
}

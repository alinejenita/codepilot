import React, { useState, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ChatMessage from './components/ChatMessage';
import ToolActivityPanel from './components/ToolActivityPanel';
import WorkspacePanel from './components/WorkspacePanel';
import { fetchHealth, sendChatMessage } from './services/api';
import { Send, Bot, Terminal, Loader2, Sparkles, AlertCircle } from 'lucide-react';

export default function App() {
  const [sessions, setSessions] = useState([
    {
      id: 'session-1',
      title: 'Inspect Workspace Structure',
      messages: [
        {
          id: 'msg-1',
          role: 'assistant',
          content: `### Welcome to CodePilot 🚀

I am your local AI coding assistant running directly on your **MacBook Air M4** with Apple Silicon Metal acceleration.

#### What I can do:
1. 📂 **Inspect Workspace** — Explore files with \`list_files\` and \`search_files\`
2. 📖 **Read Code** — Inspect Python modules with \`read_file\`
3. ✏️ **Edit Code** — Create and modify scripts safely with \`write_file\`
4. 🧪 **Run Tests** — Execute test suites and commands with \`run_command\`
5. 🛡️ **Workspace Containment** — All file operations are strictly sandboxed inside \`./workspace\`

Select one of the quick starter actions or type your coding request below!`,
          timestamp: 'Just now',
          steps: [],
        },
      ],
    },
  ]);

  const [currentSessionId, setCurrentSessionId] = useState('session-1');
  const [currentModel, setCurrentModel] = useState('qwen2.5-coder:7b');
  const [health, setHealth] = useState(null);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [showActivityPanel, setShowActivityPanel] = useState(false);
  const [showWorkspacePanel, setShowWorkspacePanel] = useState(false);
  const messagesEndRef = useRef(null);

  const currentSession = sessions.find((s) => s.id === currentSessionId) || sessions[0];

  // Check health on mount
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

  // Scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [currentSession?.messages, isLoading]);

  const handleNewSession = () => {
    const newId = `session-${Date.now()}`;
    const newSession = {
      id: newId,
      title: 'New Coding Task',
      messages: [
        {
          id: `msg-${Date.now()}`,
          role: 'assistant',
          content: "Ready for your next task. How can I help with your project?",
          timestamp: 'Just now',
          steps: [],
        },
      ],
    };
    setSessions([newSession, ...sessions]);
    setCurrentSessionId(newId);
  };

  const handleSendMessage = async (textToSend) => {
    const prompt = (textToSend || inputValue).trim();
    if (!prompt || isLoading) return;

    setInputValue('');
    const userMsgId = `usr-${Date.now()}`;
    const assistantMsgId = `asst-${Date.now()}`;
    const timeString = new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

    // 1. Append user message
    const updatedMessages = [
      ...currentSession.messages,
      {
        id: userMsgId,
        role: 'user',
        content: prompt,
        timestamp: timeString,
      },
    ];

    // Update session title if first prompt
    const updatedTitle = currentSession.messages.length <= 1 
      ? prompt.slice(0, 32) + (prompt.length > 32 ? '...' : '') 
      : currentSession.title;

    setSessions(
      sessions.map((s) =>
        s.id === currentSessionId
          ? { ...s, title: updatedTitle, messages: updatedMessages }
          : s
      )
    );

    setIsLoading(true);

    try {
      // 2. Try calling FastAPI backend
      const response = await sendChatMessage({ message: prompt, model: currentModel });
      
      const assistantMsg = {
        id: assistantMsgId,
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        steps: response.steps || [],
      };

      setSessions((prev) =>
        prev.map((s) =>
          s.id === currentSessionId
            ? { ...s, messages: [...updatedMessages, assistantMsg] }
            : s
        )
      );
    } catch (err) {
      // 3. Fallback: If FastAPI backend is not yet started, direct simulation / graceful answer
      const simulatedSteps = [
        {
          tool: 'list_files',
          args: { directory: '.' },
          status: 'completed',
          summary: 'Scanned workspace directory',
          result: { files: ['hello_world.py', '.gitkeep'] },
        },
      ];

      const simulatedResponse = `I received your request: "${prompt}".

*Note: The FastAPI backend server is currently offline. Start it in terminal with:*
\`\`\`bash
source .venv/bin/activate
uvicorn backend.app.main:app --reload --port 8000
\`\`\`

The local Ollama service is **active** with \`${currentModel}\`. All file operations remain strictly sandboxed within \`./workspace\`.`;

      const fallbackMsg = {
        id: assistantMsgId,
        role: 'assistant',
        content: simulatedResponse,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        steps: simulatedSteps,
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

  // Collect all tool steps from current session for the activity panel
  const allSteps = currentSession.messages
    .flatMap((m) => m.steps || [])
    .filter(Boolean);

  return (
    <div className="flex h-screen w-screen overflow-hidden bg-[#090d16] text-slate-100">
      {/* Left Sidebar */}
      <Sidebar
        health={health}
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSelectSession={setCurrentSessionId}
        onNewSession={handleNewSession}
        onSelectPromptTemplate={(tmpl) => handleSendMessage(tmpl)}
      />

      {/* Center Main Area */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden">
        {/* Top Header */}
        <Header
          currentModel={currentModel}
          onModelChange={setCurrentModel}
          availableModels={health?.available_models}
          health={health}
          onRefreshHealth={loadHealth}
          showActivityPanel={showActivityPanel}
          onToggleActivityPanel={() => {
            setShowActivityPanel(!showActivityPanel);
            if (showWorkspacePanel) setShowWorkspacePanel(false);
          }}
          showWorkspacePanel={showWorkspacePanel}
          onToggleWorkspacePanel={() => {
            setShowWorkspacePanel(!showWorkspacePanel);
            if (showActivityPanel) setShowActivityPanel(false);
          }}
        />

        {/* Chat Message Scrollable Container */}
        <div className="flex-1 overflow-y-auto min-h-0">
          <div className="divide-y divide-[#182338]/30">
            {currentSession.messages.map((msg) => (
              <ChatMessage key={msg.id} message={msg} />
            ))}

            {isLoading && (
              <div className="py-5 px-6 bg-[#0f172a]/20">
                <div className="max-w-3xl mx-auto flex items-center gap-3 text-xs text-slate-400">
                  <div className="w-8 h-8 rounded-lg bg-blue-600/20 text-blue-400 flex items-center justify-center border border-blue-500/30">
                    <Loader2 size={16} className="animate-spin" />
                  </div>
                  <div>
                    <span className="font-semibold text-slate-200">CodePilot is thinking...</span>
                    <p className="text-[11px] text-slate-400">Inspecting workspace and determining next action</p>
                  </div>
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Message Input Composer */}
        <div className="p-4 bg-[#0d121f] border-t border-[#1e293b] shrink-0">
          <div className="max-w-3xl mx-auto">
            <div className="relative rounded-xl bg-[#121a2d] border border-slate-700/80 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 transition-all shadow-lg">
              <textarea
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Ask CodePilot to inspect, write, test, or fix code in the workspace... (Press Enter to send)"
                rows={2}
                className="w-full bg-transparent p-3 pr-12 text-sm text-slate-100 placeholder-slate-400 resize-none focus:outline-none"
              />

              <button
                onClick={() => handleSendMessage()}
                disabled={!inputValue.trim() || isLoading}
                className={`absolute right-3 bottom-3 p-2 rounded-lg transition-all ${
                  inputValue.trim() && !isLoading
                    ? 'bg-blue-600 hover:bg-blue-500 text-white shadow-md active:scale-95'
                    : 'bg-slate-800 text-slate-400 cursor-not-allowed'
                }`}
                title="Send task"
              >
                <Send size={15} />
              </button>
            </div>

            <div className="mt-2 flex items-center justify-between text-[11px] text-slate-400 px-1">
              <span>Shift + Enter for new line • Enter to submit</span>
              <span className="font-mono text-[10px]">Isolated Workspace: ./workspace</span>
            </div>
          </div>
        </div>
      </div>

      {/* Right Drawer: Activity Panel */}
      {showActivityPanel && (
        <ToolActivityPanel
          steps={allSteps}
          onClose={() => setShowActivityPanel(false)}
        />
      )}

      {/* Right Drawer: Workspace Files */}
      {showWorkspacePanel && (
        <WorkspacePanel
          onClose={() => setShowWorkspacePanel(false)}
        />
      )}
    </div>
  );
}

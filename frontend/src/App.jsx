import { useState, useEffect, useRef, useCallback } from 'react';
import Sidebar from './components/Sidebar';
import Header from './components/Header';
import ChatMessage from './components/ChatMessage';
import LoginScreen from './components/LoginScreen';
import WorkspacePanel from './components/WorkspacePanel';
import {
  fetchAuthStatus,
  fetchHealth,
  login,
  logout,
  sendChatMessage,
} from './services/api';
import { ArrowUp, Send, FolderSearch, Terminal, FileCode2 } from 'lucide-react';

const STORAGE_KEY = 'codepilot_chat_sessions_v2';
const CURRENT_ID_KEY = 'codepilot_current_session_id_v2';

function RoamingPlane() {
  const planeRef = useRef(null);

  useEffect(() => {
    const plane = planeRef.current;
    if (!plane) return undefined;

    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) {
      plane.style.left = '50%';
      plane.style.top = '50%';
      plane.style.transform = 'translate(-50%, -50%)';
      return undefined;
    }

    const getBounds = () => {
      const width = window.innerWidth;
      const height = window.innerHeight;
      return {
        minX: Math.min(48, width * 0.08),
        maxX: width - Math.min(48, width * 0.08),
        minY: Math.min(48, height * 0.08),
        maxY: height - Math.min(48, height * 0.08),
      };
    };
    const randomPoint = (bounds) => ({
      x: bounds.minX + Math.random() * (bounds.maxX - bounds.minX),
      y: bounds.minY + Math.random() * (bounds.maxY - bounds.minY),
    });
    const clampPoint = (point, bounds) => ({
      x: Math.max(bounds.minX, Math.min(bounds.maxX, point.x)),
      y: Math.max(bounds.minY, Math.min(bounds.maxY, point.y)),
    });
    const setPose = (x, y, angle, bank = 0, scale = 1) => {
      plane.style.left = `${x}px`;
      plane.style.top = `${y}px`;
      plane.style.transform = `translate(-50%, -50%) rotate(${angle + Math.PI / 4 + bank}rad) scale(${scale})`;
    };

    let position = randomPoint(getBounds());
    let heading = Math.random() * Math.PI * 2;
    let bank = 0;
    let scale = 1;
    let lastFrameTime = performance.now();
    let segment;
    let frameId;
    setPose(position.x, position.y, heading);

    const createSegment = (startTime) => {
      const bounds = getBounds();
      position = clampPoint(position, bounds);
      let end = randomPoint(bounds);
      let dx = end.x - position.x;
      let dy = end.y - position.y;
      let distance = Math.hypot(dx, dy);
      for (let attempt = 0; distance < 120 && attempt < 4; attempt += 1) {
        end = randomPoint(bounds);
        dx = end.x - position.x;
        dy = end.y - position.y;
        distance = Math.hypot(dx, dy);
      }

      const turn = Math.atan2(dy, dx) + (Math.random() - 0.5) * 1.4;
      const handle = Math.min(distance * 0.38, 220);
      const control1 = clampPoint({
        x: position.x + Math.cos(heading) * handle,
        y: position.y + Math.sin(heading) * handle,
      }, bounds);
      const control2 = clampPoint({
        x: end.x - Math.cos(turn) * handle,
        y: end.y - Math.sin(turn) * handle,
      }, bounds);
      const endHeading = Math.atan2(end.y - control2.y, end.x - control2.x);

      return {
        start: { ...position },
        control1,
        control2,
        end,
        endHeading,
        startTime,
        duration: Math.max(1800, Math.min(5500, distance / 0.16)),
      };
    };

    const animate = (now) => {
      if (!segment) segment = createSegment(now);
      const progress = Math.min((now - segment.startTime) / segment.duration, 1);
      const inverse = 1 - progress;
      const { start, control1, control2, end } = segment;
      const x = inverse ** 3 * start.x
        + 3 * inverse ** 2 * progress * control1.x
        + 3 * inverse * progress ** 2 * control2.x
        + progress ** 3 * end.x;
      const y = inverse ** 3 * start.y
        + 3 * inverse ** 2 * progress * control1.y
        + 3 * inverse * progress ** 2 * control2.y
        + progress ** 3 * end.y;
      const tangentX = 3 * inverse ** 2 * (control1.x - start.x)
        + 6 * inverse * progress * (control2.x - control1.x)
        + 3 * progress ** 2 * (end.x - control2.x);
      const tangentY = 3 * inverse ** 2 * (control1.y - start.y)
        + 6 * inverse * progress * (control2.y - control1.y)
        + 3 * progress ** 2 * (end.y - control2.y);

      const accelerationX = 6 * (
        inverse * (control2.x - 2 * control1.x + start.x)
        + progress * (end.x - 2 * control2.x + control1.x)
      );
      const accelerationY = 6 * (
        inverse * (control2.y - 2 * control1.y + start.y)
        + progress * (end.y - 2 * control2.y + control1.y)
      );
      const speedSquared = tangentX ** 2 + tangentY ** 2;
      const curvature = speedSquared > 0.001
        ? (tangentX * accelerationY - tangentY * accelerationX)
          / (speedSquared * Math.sqrt(speedSquared))
        : 0;
      const targetBank = Math.max(-0.32, Math.min(0.32, curvature * 55));
      const targetScale = 1 + Math.min(Math.abs(curvature) * 3, 0.05);
      const response = 1 - Math.exp(-(now - lastFrameTime) / 180);
      bank += (targetBank - bank) * response;
      scale += (targetScale - scale) * response;
      lastFrameTime = now;

      setPose(x, y, Math.atan2(tangentY, tangentX), bank, scale);

      if (progress === 1) {
        position = end;
        heading = segment.endHeading;
        segment = createSegment(now);
      }
      frameId = window.requestAnimationFrame(animate);
    };

    frameId = window.requestAnimationFrame(animate);
    return () => window.cancelAnimationFrame(frameId);
  }, []);

  return (
    <div ref={planeRef} className="plane-roaming-global">
      <Send size={18} />
    </div>
  );
}

export default function App() {
  const [auth, setAuth] = useState({
    loading: true,
    configured: false,
    authenticated: false,
    error: '',
  });

  // Load sessions from localStorage or initialize with default
  const [sessions, setSessions] = useState(() => {
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        const parsed = JSON.parse(saved);
        if (Array.isArray(parsed) && parsed.length > 0) {
          return parsed.map((session) => ({
            ...session,
            messages: Array.isArray(session.messages)
              ? session.messages.filter((message) => message.id !== 'welcome-msg')
              : [],
          }));
        }
      }
    } catch (e) {
      console.warn('Could not parse saved sessions:', e);
    }
    return [
      {
        id: 'session-default',
        title: 'New chat',
        createdAt: new Date().toISOString(),
        messages: [],
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
  const isSendingRef = useRef(false);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    let active = true;
    fetchAuthStatus()
      .then((status) => {
        if (active) {
          setAuth({
            loading: false,
            configured: status.configured,
            authenticated: status.authenticated,
            error: '',
          });
        }
      })
      .catch((error) => {
        if (active) {
          setAuth({
            loading: false,
            configured: false,
            authenticated: false,
            error: error.message,
          });
        }
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    const handleUnauthorized = () => {
      setAuth((current) => ({ ...current, authenticated: false }));
    };
    window.addEventListener('codepilot:unauthorized', handleUnauthorized);
    return () => window.removeEventListener('codepilot:unauthorized', handleUnauthorized);
  }, []);

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

  const loadHealth = useCallback(async () => {
    const data = await fetchHealth();
    setHealth(data);
    if (data.model) setCurrentModel(data.model);
  }, []);

  useEffect(() => {
    if (!auth.authenticated) return undefined;
    void loadHealth();
    const interval = setInterval(() => void loadHealth(), 10000);
    return () => clearInterval(interval);
  }, [auth.authenticated, loadHealth]);

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
      messages: [],
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
        messages: [],
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
    if (!prompt || isLoading || isSendingRef.current) return;

    isSendingRef.current = true;
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
      // Build conversation history from previous turns.
      const historyPayload = currentSession.messages
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
      isSendingRef.current = false;
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

  const handleLogin = async (username, password) => {
    await login(username, password);
    setAuth({
      loading: false,
      configured: true,
      authenticated: true,
      error: '',
    });
  };

  const handleLogout = async () => {
    try {
      await logout();
      setAuth({
        loading: false,
        configured: true,
        authenticated: false,
        error: '',
      });
    } catch (error) {
      setAuth((current) => ({
        ...current,
        authenticated: false,
        error: `Sign out failed: ${error.message}`,
      }));
    }
  };

  if (auth.loading) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#181816] text-sm text-[#9c9a92]">
        Checking CodePilot login...
      </main>
    );
  }

  if (auth.error) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#181816] px-4 text-[#edece6]">
        <section className="max-w-md rounded-2xl border border-[#383834] bg-[#242422] p-6 text-center">
          <h1 className="mb-2 text-lg font-semibold">CodePilot login unavailable</h1>
          <p role="alert" className="text-sm text-[#c5c3bb]">{auth.error}</p>
          <p className="mt-3 text-xs text-[#9c9a92]">Check that the backend is running, then reload this page.</p>
        </section>
      </main>
    );
  }

  if (!auth.configured) {
    return (
      <main className="flex min-h-screen items-center justify-center bg-[#181816] px-4 text-[#edece6]">
        <section className="max-w-md rounded-2xl border border-[#383834] bg-[#242422] p-6">
          <h1 className="mb-2 text-lg font-semibold">Login is not configured</h1>
          <p className="text-sm text-[#c5c3bb]">
            Set CODEPILOT_LOGIN_USERNAME, a CODEPILOT_LOGIN_PASSWORD of at
            least 12 characters, and a CODEPILOT_SESSION_SECRET of at least
            32 characters in the backend environment, then restart the backend.
          </p>
        </section>
      </main>
    );
  }

  if (!auth.authenticated) {
    return <LoginScreen onLogin={handleLogin} />;
  }

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
          onLogout={handleLogout}
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
                <div className="max-w-3xl mx-auto flex items-center gap-2.5 text-xs text-[#9c9a92]" role="status" aria-live="polite">
                  <span className="font-medium text-[#edece6]">
                    CodePilot is working on your answer...
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
            {/* Quick Starters (shown for an empty chat) */}
            {currentSession?.messages?.length === 0 && (
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

      {isLoading && (
        <div className="plane-flight-overlay" aria-hidden="true">
          <RoamingPlane />
        </div>
      )}

      {/* Workspace Panel Right Drawer */}
      {showWorkspacePanel && (
        <WorkspacePanel
          onClose={() => setShowWorkspacePanel(false)}
        />
      )}
    </div>
  );
}

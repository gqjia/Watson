import { useState, useRef, useEffect } from "react";
import { Send, User, Bot, Loader2, RefreshCw, Terminal, ChevronDown, ChevronRight, Activity, BookOpen, Globe, Menu, Plus, MessageSquare, X, Target, Brain, Trash2, Edit2, Check } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  details?: {
    critic?: string;
    mentor?: string;
    draft?: string;
    search?: string;
  };
}

interface Thread {
  id: string;
  title: string;
  updated_at: string;
}

interface UserProfile {
  learning_goals: string;
  self_description: string;
  knowledge: Record<string, string>;
}

const DetailPanel = ({ title, content, icon: Icon, colorClass }: { title: string, content: string, icon: any, colorClass: string }) => {
  const [isOpen, setIsOpen] = useState(false);
  
  if (!content) return null;

  return (
    <div className="mt-4 border border-slate-200 dark:border-slate-700 rounded-lg overflow-hidden">
      <button 
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between p-3 bg-slate-50 dark:bg-slate-800 hover:bg-slate-100 dark:hover:bg-slate-750 transition-colors"
      >
        <div className="flex items-center gap-2">
          <Icon size={16} className={colorClass} />
          <span className="text-sm font-medium text-slate-700 dark:text-slate-300">{title}</span>
        </div>
        {isOpen ? <ChevronDown size={16} className="text-slate-400" /> : <ChevronRight size={16} className="text-slate-400" />}
      </button>
      
      {isOpen && (
        <div className="p-3 bg-white dark:bg-slate-900 border-t border-slate-200 dark:border-slate-700">
           <div className="prose prose-sm max-w-none dark:prose-invert">
              <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
           </div>
        </div>
      )}
    </div>
  );
};

const EditableSection = ({ 
    title, 
    content, 
    icon: Icon, 
    onSave, 
    isMarkdown = true 
}: { 
    title: string, 
    content: string, 
    icon: any, 
    onSave: (newContent: string) => Promise<void>,
    isMarkdown?: boolean
}) => {
    const [isEditing, setIsEditing] = useState(false);
    const [value, setValue] = useState(content);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        setValue(content);
    }, [content]);

    const handleSave = async () => {
        if (value === content) {
            setIsEditing(false);
            return;
        }
        setIsSaving(true);
        try {
            await onSave(value);
            setIsEditing(false);
        } catch (e) {
            console.error("Failed to save", e);
            alert("Failed to save changes.");
        } finally {
            setIsSaving(false);
        }
    };

    return (
        <div className="border border-slate-200 dark:border-slate-700 rounded-xl overflow-hidden shadow-sm bg-white dark:bg-slate-800">
            <div className="bg-slate-50 dark:bg-slate-700/50 px-4 py-3 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center">
                <h4 className="text-sm font-bold text-slate-700 dark:text-slate-200 flex items-center gap-2">
                    <Icon size={16} />
                    {title}
                </h4>
                {!isEditing ? (
                    <button 
                        onClick={() => setIsEditing(true)}
                        className="p-1.5 text-slate-400 hover:text-indigo-600 hover:bg-indigo-50 dark:hover:bg-indigo-900/20 rounded-lg transition-colors"
                        title="Edit"
                    >
                        <Edit2 size={14} />
                    </button>
                ) : (
                    <div className="flex gap-1">
                        <button 
                            onClick={handleSave}
                            disabled={isSaving}
                            className="p-1.5 text-emerald-600 hover:bg-emerald-50 dark:hover:bg-emerald-900/20 rounded-lg transition-colors"
                            title="Save"
                        >
                            {isSaving ? <Loader2 size={14} className="animate-spin" /> : <Check size={14} />}
                        </button>
                        <button 
                            onClick={() => {
                                setIsEditing(false);
                                setValue(content);
                            }}
                            disabled={isSaving}
                            className="p-1.5 text-slate-400 hover:text-slate-600 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                            title="Cancel"
                        >
                            <X size={14} />
                        </button>
                    </div>
                )}
            </div>
            <div className="p-4">
                {isEditing ? (
                    <textarea 
                        value={value}
                        onChange={(e) => setValue(e.target.value)}
                        className="w-full h-48 p-3 text-sm bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-700 rounded-lg focus:ring-2 focus:ring-indigo-500 focus:border-transparent outline-none resize-none font-mono"
                    />
                ) : (
                    <div className="prose prose-sm max-w-none dark:prose-invert">
                        {isMarkdown ? (
                            <ReactMarkdown remarkPlugins={[remarkGfm]}>{content}</ReactMarkdown>
                        ) : (
                            <p className="whitespace-pre-wrap">{content}</p>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

const ChatMessage = ({ message }: { message: Message }) => {
  const isUser = message.role === "user";

  return (
    <div className={`flex w-full mb-6 ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`flex max-w-[85%] ${isUser ? "flex-row-reverse" : "flex-col"} gap-3`}>
        <div className={`flex ${isUser ? "flex-row-reverse" : "flex-row"} gap-3`}>
        {/* Avatar */}
        <div
          className={`flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center shadow-sm ${
            isUser 
              ? "bg-indigo-600 text-white" 
              : "bg-emerald-600 text-white"
          }`}
        >
          {isUser ? <User size={20} /> : <Bot size={20} />}
        </div>

        {/* Message Bubble */}
        <div
          className={`flex flex-col p-4 rounded-2xl shadow-sm border ${
            isUser
              ? "bg-indigo-600 text-white border-indigo-500 rounded-tr-none"
              : "bg-white dark:bg-gray-800 text-gray-800 dark:text-gray-100 border-gray-100 dark:border-gray-700 rounded-tl-none"
          }`}
        >
          <div className={`prose prose-sm max-w-none ${isUser ? "prose-invert" : "dark:prose-invert"}`}>
            {isUser ? (
              <p className="whitespace-pre-wrap m-0">{message.content}</p>
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, inline, className, children, ...props }: any) {
                    const match = /language-(\w+)/.exec(className || "");
                    return !inline && match ? (
                      <div className="rounded-md overflow-hidden my-2">
                        <div className="bg-gray-900 px-3 py-1 text-xs text-gray-400 border-b border-gray-700 flex items-center">
                          <Terminal size={12} className="mr-2" />
                          {match[1]}
                        </div>
                        <SyntaxHighlighter
                          style={vscDarkPlus}
                          language={match[1]}
                          PreTag="div"
                          customStyle={{ margin: 0, borderRadius: 0 }}
                          {...props}
                        >
                          {String(children).replace(/\n$/, "")}
                        </SyntaxHighlighter>
                      </div>
                    ) : (
                      <code className={`${className} bg-gray-100 dark:bg-gray-700 px-1 py-0.5 rounded text-sm font-mono text-red-500 dark:text-red-400`} {...props}>
                        {children}
                      </code>
                    );
                  },
                  p: ({ children }) => <p className="mb-2 last:mb-0 leading-relaxed">{children}</p>,
                  ul: ({ children }) => <ul className="list-disc pl-4 mb-2 space-y-1">{children}</ul>,
                  ol: ({ children }) => <ol className="list-decimal pl-4 mb-2 space-y-1">{children}</ol>,
                  li: ({ children }) => <li className="mb-1">{children}</li>,
                  h1: ({ children }) => <h1 className="text-xl font-bold mb-3 mt-4 border-b pb-2">{children}</h1>,
                  h2: ({ children }) => <h2 className="text-lg font-bold mb-2 mt-3">{children}</h2>,
                  h3: ({ children }) => <h3 className="text-md font-bold mb-2 mt-2">{children}</h3>,
                  blockquote: ({ children }) => (
                    <blockquote className="border-l-4 border-gray-300 dark:border-gray-600 pl-4 italic text-gray-600 dark:text-gray-400 my-2">
                      {children}
                    </blockquote>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            )}
          </div>
        </div>
        </div>

        {/* Agent Details (Critic & Mentor) */}
        {!isUser && message.details && (
           <div className="pl-14 w-full space-y-2">
              {message.details.search && (
                <DetailPanel 
                  title="Web Search Results" 
                  content={message.details.search} 
                  icon={Globe}
                  colorClass="text-sky-500"
                />
              )}
              {message.details.draft && (
                <DetailPanel 
                  title="Initial Draft (Coach)" 
                  content={message.details.draft} 
                  icon={Terminal}
                  colorClass="text-gray-500"
                />
              )}
              {message.details.critic && (
                <DetailPanel 
                  title="Technical Analysis (Critic)" 
                  content={message.details.critic} 
                  icon={Activity}
                  colorClass="text-amber-500"
                />
              )}
              {message.details.mentor && (
                <DetailPanel 
                  title="Learning Plan (Mentor)" 
                  content={message.details.mentor} 
                  icon={BookOpen}
                  colorClass="text-blue-500"
                />
              )}
           </div>
        )}
      </div>
    </div>
  );
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [threadId, setThreadId] = useState("");
  const [threads, setThreads] = useState<Thread[]>([]);
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const [isProfileOpen, setIsProfileOpen] = useState(true); // Default open for bold change
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  const fetchThreads = async () => {
      try {
          const res = await fetch("http://localhost:8000/chat/threads");
          const data = await res.json();
          if (data && Array.isArray(data.threads)) {
              setThreads(data.threads);
          }
      } catch (e) {
          console.error("Failed to fetch threads", e);
      }
  };

  const fetchProfile = async () => {
    try {
        const res = await fetch("http://localhost:8000/chat/profile");
        const data = await res.json();
        setUserProfile(data);
    } catch (e) {
        console.error("Failed to fetch profile", e);
    }
  };

  const clearProfile = async () => {
    if (!confirm("Are you sure you want to clear your knowledge profile? This action cannot be undone.")) return;
    
    try {
        await fetch("http://localhost:8000/chat/profile", { method: "DELETE" });
        await fetchProfile();
    } catch (e) {
        console.error("Failed to clear profile", e);
    }
  };

  const loadThreadHistory = async (id: string) => {
      setIsLoading(true);
      try {
          const res = await fetch(`http://localhost:8000/chat/history/${id}`);
          const data = await res.json();
          setMessages(data.messages);
      } catch (e) {
          console.error("Failed to load history", e);
      } finally {
          setIsLoading(false);
      }
  };

  useEffect(() => {
    fetchThreads();
    fetchProfile();
    
    // Initialize or retrieve thread_id from localStorage
    let storedThreadId = localStorage.getItem("watson_thread_id");
    if (!storedThreadId) {
        storedThreadId = crypto.randomUUID();
        localStorage.setItem("watson_thread_id", storedThreadId);
    }
    setThreadId(storedThreadId);
    loadThreadHistory(storedThreadId);
  }, []);

  const deleteThread = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!confirm("Are you sure you want to delete this chat history?")) return;

    try {
        const res = await fetch(`http://localhost:8000/chat/threads/${id}`, { method: "DELETE" });
        if (res.ok) {
            // Remove from local state
            setThreads(prev => prev.filter(t => t.id !== id));
            // If deleting current thread, start a new one
            if (id === threadId) {
                startNewChat();
            }
        }
    } catch (e) {
        console.error("Failed to delete thread", e);
    }
  };

  const clearAllThreads = async () => {
    if (!confirm("Are you sure you want to delete ALL chat history? This action cannot be undone.")) return;

    try {
        const res = await fetch("http://localhost:8000/chat/threads", { method: "DELETE" });
        if (res.ok) {
            setThreads([]);
            startNewChat();
        }
    } catch (e) {
        console.error("Failed to delete all threads", e);
    }
  };

  const handleUpdateGoals = async (newGoals: string) => {
    await fetch("http://localhost:8000/chat/profile/goals", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goals: newGoals })
    });
    // Optimistic update or refetch
    setUserProfile(prev => prev ? { ...prev, learning_goals: newGoals } : null);
  };

  const handleUpdateDescription = async (newDescription: string) => {
    await fetch("http://localhost:8000/chat/profile/description", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: newDescription })
    });
    // Optimistic update
    setUserProfile(prev => prev ? { ...prev, self_description: newDescription } : null);
  };

  const handleUpdateKnowledge = async (category: string, newContent: string) => {
    await fetch("http://localhost:8000/chat/profile/knowledge", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ category, content: newContent })
    });
    // Optimistic update
    setUserProfile(prev => {
        if (!prev) return null;
        return {
            ...prev,
            knowledge: {
                ...prev.knowledge,
                [category]: newContent
            }
        };
    });
  };

  const handleThreadSelect = (id: string) => {
      setThreadId(id);
      localStorage.setItem("watson_thread_id", id);
      loadThreadHistory(id);
      setIsSidebarOpen(false);
  };

  const startNewChat = () => {
      const newId = crypto.randomUUID();
      setThreadId(newId);
      localStorage.setItem("watson_thread_id", newId);
      setMessages([]);
      setIsSidebarOpen(false);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  const handleSubmit = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage: Message = { role: "user", content: input };
    setMessages((prev) => [...prev, userMessage]);
    setInput("");
    if (inputRef.current) inputRef.current.style.height = "auto";
    setIsLoading(true);

    try {
      const response = await fetch("http://localhost:8000/chat/stream", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          messages: [...messages, userMessage],
          thread_id: threadId,
        }),
      });

      if (!response.body) throw new Error("No response body");
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
      let accumulatedContent = "";
      let accumulatedCritic = "";
      let accumulatedMentor = "";
      let accumulatedDraft = "";
      let accumulatedSearch = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
            // Refresh threads to get the updated title
            fetchThreads();
            // Refresh profile as mentor might have updated it
            fetchProfile();
            break;
        }

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") break;

            try {
              const parsed = JSON.parse(data);
              const node = parsed.node;
              const content = parsed.content;
              const type = parsed.type;

              if (type === "revision_start") {
                 // Add revision separator
                 if (node === "coach_draft") {
                     accumulatedDraft += "\n\n---\n**New Revision**\n---\n\n";
                 } else if (node === "critic") {
                     accumulatedCritic += "\n\n---\n**New Revision**\n---\n\n";
                 }
                 continue;
              }

              if (content) {
                // Update accumulators outside the state updater to avoid double-invocation issues in StrictMode
                if (node === "coach") {
                    accumulatedContent += content;
                } else if (node === "coach_draft") {
                    accumulatedDraft += content;
                } else if (node === "critic") {
                    accumulatedCritic += content;
                } else if (node === "mentor") {
                    accumulatedMentor += content;
                } else if (node === "search") {
                    accumulatedSearch += content;
                }

                setMessages((prev) => {
                  const newMessages = [...prev];
                  const lastMsgIndex = newMessages.length - 1;
                  
                  const lastMsg = { ...newMessages[lastMsgIndex] };
                  newMessages[lastMsgIndex] = lastMsg;
                  
                  if (lastMsg.role === "assistant") {
                    if (node === "coach") {
                        lastMsg.content = accumulatedContent;
                    } else if (node === "coach_draft") {
                        lastMsg.details = lastMsg.details ? { ...lastMsg.details } : {};
                        lastMsg.details.draft = accumulatedDraft;
                    } else if (node === "critic") {
                        lastMsg.details = lastMsg.details ? { ...lastMsg.details } : {};
                        lastMsg.details.critic = accumulatedCritic;
                    } else if (node === "mentor") {
                        lastMsg.details = lastMsg.details ? { ...lastMsg.details } : {};
                        lastMsg.details.mentor = accumulatedMentor;
                    } else if (node === "search") {
                        lastMsg.details = lastMsg.details ? { ...lastMsg.details } : {};
                        lastMsg.details.search = accumulatedSearch;
                    }
                  }
                  return newMessages;
                });
              }
            } catch (e) {
              console.error("Error parsing SSE data:", e);
            }
          }
        }
      }
    } catch (error) {
      console.error("Error sending message:", error);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
  };

  return (
    <div className="flex h-screen bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-sans overflow-hidden">
      {/* Mobile Sidebar Overlay */}
      {isSidebarOpen && (
        <div 
          className="fixed inset-0 bg-black/50 z-20 md:hidden"
          onClick={() => setIsSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside 
        className={`
          fixed md:static inset-y-0 left-0 z-30 w-64 bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 transform transition-transform duration-200 ease-in-out flex flex-col
          ${isSidebarOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
        `}
      >
        <div className="p-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
            <h2 className="font-bold text-lg flex items-center gap-2">
                <Bot className="w-6 h-6 text-indigo-600" />
                Watson
            </h2>
            <button 
                onClick={() => setIsSidebarOpen(false)}
                className="md:hidden p-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded"
            >
                <X size={20} />
            </button>
        </div>
        
        <div className="p-4">
            <button 
                onClick={startNewChat}
                className="w-full flex items-center justify-center gap-2 bg-indigo-600 hover:bg-indigo-700 text-white p-3 rounded-xl transition-colors font-medium"
            >
                <Plus size={18} />
                New Chat
            </button>
        </div>

        <div className="flex-1 overflow-y-auto px-2 py-2 space-y-1">
            <h3 className="px-2 text-xs font-semibold text-slate-400 uppercase tracking-wider mb-2">History</h3>
            {threads.map((thread) => (
                <button
                    key={thread.id}
                    onClick={() => handleThreadSelect(thread.id)}
                    className={`w-full text-left p-3 rounded-lg text-sm flex items-center gap-3 transition-colors group relative ${
                        thread.id === threadId 
                            ? "bg-slate-100 dark:bg-slate-700 text-indigo-600 dark:text-indigo-400 font-medium" 
                            : "hover:bg-slate-50 dark:hover:bg-slate-700/50 text-slate-600 dark:text-slate-300"
                    }`}
                >
                    <MessageSquare size={16} />
                    <span className="truncate flex-1 pr-6">
                        {thread.title}
                    </span>
                    <span 
                        onClick={(e) => deleteThread(thread.id, e)}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 text-slate-400 hover:text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded opacity-0 group-hover:opacity-100 transition-all"
                        title="Delete Chat"
                    >
                        <Trash2 size={14} />
                    </span>
                </button>
            ))}
        </div>
        
        <div className="p-4 border-t border-slate-200 dark:border-slate-700">
            {threads.length > 0 && (
                <button
                    onClick={clearAllThreads}
                    className="w-full flex items-center justify-center gap-2 p-2 text-xs font-medium text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors mb-2"
                >
                    <Trash2 size={14} />
                    Delete All History
                </button>
            )}
            <div className="text-xs text-slate-400 text-center">
                v1.0.0
            </div>
        </div>
      </aside>

      {/* Main Content */}
      <div className="flex-1 flex flex-col h-full min-w-0">
        {/* Header */}
        <header className="bg-white dark:bg-slate-800 shadow-sm border-b border-slate-200 dark:border-slate-700 p-4 sticky top-0 z-10 flex items-center justify-between shrink-0">
          <div className="flex items-center gap-3">
            <button 
                onClick={() => setIsSidebarOpen(true)}
                className="md:hidden p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg"
            >
                <Menu size={20} />
            </button>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">
                Watson
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">Your AI Technical Coach</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
              <button 
                onClick={() => setIsProfileOpen(!isProfileOpen)}
                className="p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-full transition-colors hidden md:block"
                title="Toggle Knowledge Profile"
              >
                <BookOpen size={20} className={isProfileOpen ? "text-indigo-600" : ""} />
              </button>
              <button 
                onClick={() => window.location.reload()}
                className="p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-full transition-colors"
                title="Reset Session"
              >
                <RefreshCw size={20} />
              </button>
          </div>
        </header>

        <div className="flex-1 flex overflow-hidden">
            {/* Messages */}
        <main className="flex-1 overflow-y-auto p-4 sm:p-6 scroll-smooth">
            <div className="max-w-5xl mx-auto xl:mx-0 xl:w-full xl:max-w-none px-4 sm:px-6">
              {messages.length === 0 && (
                    <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-6 animate-fade-in">
                      <div className="w-20 h-20 bg-indigo-100 dark:bg-indigo-900/30 rounded-full flex items-center justify-center mb-4">
                        <Bot className="w-10 h-10 text-indigo-600 dark:text-indigo-400" />
                      </div>
                      <h2 className="text-3xl font-bold text-slate-800 dark:text-slate-100">
                        Ready to learn?
                      </h2>
                      <p className="text-slate-600 dark:text-slate-400 max-w-md text-lg">
                        I can help you review algorithms, system design, or specific language concepts.
                      </p>
                      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg mt-8">
                        {[
                          "Review Python Memory Management",
                          "Explain ACID properties",
                          "Design a URL Shortener",
                          "Practice: Arrays & Strings"
                        ].map((suggestion) => (
                          <button
                            key={suggestion}
                            onClick={() => {
                              setInput(suggestion);
                            }}
                            className="p-3 text-sm text-left bg-white dark:bg-slate-800 border border-slate-200 dark:border-slate-700 rounded-xl hover:border-indigo-500 hover:shadow-md transition-all duration-200 text-slate-700 dark:text-slate-300"
                          >
                            {suggestion}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                  
                  {messages.map((msg, index) => (
                    <ChatMessage key={index} message={msg} />
                  ))}
                  
                  {isLoading && messages[messages.length - 1]?.role !== "assistant" && (
                    <div className="flex justify-start mb-6 animate-pulse">
                      <div className="flex items-center gap-3">
                          <div className="w-10 h-10 rounded-full bg-emerald-600 flex items-center justify-center">
                            <Bot size={20} className="text-white" />
                          </div>
                          <div className="bg-white dark:bg-slate-800 p-4 rounded-2xl rounded-tl-none border border-slate-100 dark:border-slate-700 shadow-sm">
                            <div className="flex gap-1">
                              <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "0ms" }} />
                              <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "150ms" }} />
                              <div className="w-2 h-2 bg-slate-400 rounded-full animate-bounce" style={{ animationDelay: "300ms" }} />
                            </div>
                          </div>
                      </div>
                    </div>
                  )}
                  <div ref={messagesEndRef} className="h-4" />
                </div>
            </main>

            {/* Right Sidebar - Knowledge Profile */}
            {isProfileOpen && userProfile && (
                <aside className="w-[600px] bg-white dark:bg-slate-800 border-l border-slate-200 dark:border-slate-700 overflow-y-auto hidden xl:flex flex-col animate-slide-in-right shrink-0">
                    <div className="p-6 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center">
                        <div>
                            <h3 className="font-bold text-xl flex items-center gap-2 text-slate-800 dark:text-slate-100">
                                <Brain className="w-5 h-5 text-purple-600" />
                                Knowledge Profile
                            </h3>
                            <p className="text-xs text-slate-500 mt-1">AI-generated assessment of your skills</p>
                        </div>
                        <button
                            onClick={clearProfile}
                            className="p-2 text-red-500 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors flex items-center gap-2 text-xs font-medium"
                            title="Clear Knowledge Profile"
                        >
                            <Trash2 size={16} />
                            Clear
                        </button>
                    </div>
                    
                    <div className="p-6 space-y-8">
                        {/* User Description */}
                        <div>
                            <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                                <User size={16} />
                                About Me
                            </h4>
                            <EditableSection
                                title="Self Description"
                                content={userProfile.self_description || "No description provided."}
                                icon={User}
                                onSave={handleUpdateDescription}
                                isMarkdown={false}
                            />
                        </div>

                        {/* Learning Goals */}
                        <div>
                            <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                                <Target size={16} />
                                Learning Goals
                            </h4>
                            <EditableSection
                                title="Current Goals"
                                content={userProfile.learning_goals}
                                icon={Target}
                                onSave={handleUpdateGoals}
                                isMarkdown={false}
                            />
                        </div>

                        {/* Knowledge Categories */}
                        <div>
                            <h4 className="text-sm font-semibold text-slate-400 uppercase tracking-wider mb-4 flex items-center gap-2">
                                <BookOpen size={16} />
                                Skill Breakdown
                            </h4>
                            <div className="space-y-4">
                                {Object.entries(userProfile.knowledge).length > 0 ? (
                                    Object.entries(userProfile.knowledge).map(([category, content]) => (
                                        <EditableSection
                                            key={category}
                                            title={category}
                                            content={content}
                                            icon={BookOpen}
                                            onSave={(newContent) => handleUpdateKnowledge(category, newContent)}
                                        />
                                    ))
                                ) : (
                                    <div className="text-center p-4 text-slate-400 text-sm italic border border-dashed border-slate-300 rounded-lg">
                                        No skills recorded yet. Start chatting!
                                    </div>
                                )}
                            </div>
                        </div>
                    </div>
                </aside>
            )}
        </div>

        {/* Footer Input */}
        <footer className="bg-white dark:bg-slate-800 p-4 border-t border-slate-200 dark:border-slate-700 shrink-0">
            <div className="max-w-5xl mx-auto xl:mx-0 xl:w-full xl:max-w-none px-4 sm:px-6">
              <div className="relative flex items-end gap-2 bg-slate-100 dark:bg-slate-900 p-2 rounded-2xl border border-transparent focus-within:border-indigo-500 focus-within:ring-1 focus-within:ring-indigo-500 transition-all">
                <textarea
                  ref={inputRef}
                  value={input}
                  onChange={handleInput}
                  onKeyDown={handleKeyDown}
                  placeholder="Type your answer..."
                  className="w-full bg-transparent border-none focus:ring-0 resize-none max-h-[200px] min-h-[44px] py-2.5 px-3 text-slate-800 dark:text-slate-100 placeholder:text-slate-400"
                  rows={1}
                  disabled={isLoading}
                />
                <button
                  onClick={() => handleSubmit()}
                  disabled={isLoading || !input.trim()}
                  className="p-2.5 mb-1 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex-shrink-0"
                >
                  {isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
                </button>
              </div>
              <p className="text-center text-xs text-slate-400 mt-2">
                AI can make mistakes. Please verify important technical details.
              </p>
            </div>
        </footer>
      </div>
    </div>
  );
}

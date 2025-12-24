import { useState, useEffect, useRef } from "react";
import { Send, Bot, Loader2, RefreshCw, Menu, BookOpen } from "lucide-react";
import { ChatMessage } from "../components/ChatMessage";
import { Sidebar } from "../components/Sidebar";
import { KnowledgePanel } from "../components/KnowledgePanel";
import { Logo } from "../components/Logo";
import { AppLayout } from "../components/layout/AppLayout";
import { useChat } from "../hooks/useChat";

export default function Home() {
  const {
    activeThreadId,
    threads,
    userProfile,
    activeConversation,
    inputRef,
    setInput,
    sendMessage,
    handleThreadSelect,
    startNewChat,
    deleteThread,
    clearAllThreads,
    handleUpdateGoals,
    handleUpdateDescription,
    handleUpdateKnowledge,
    clearProfile
  } = useChat();

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll effect
  useEffect(() => {
    // Scroll to bottom when messages change
    // We use a small timeout to ensure DOM has updated
    const timeoutId = setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
    }, 100);
    return () => clearTimeout(timeoutId);
  }, [activeConversation.messages.length, activeConversation.isLoading]);

  // Responsive profile panel
  useEffect(() => {
    // Disabled auto-open on large screens based on user feedback
    // The panel should only open on demand
    const handleResize = () => {
        if (window.innerWidth < 1280) {
            setIsProfileOpen(false);
        }
    };
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  const handleInput = (e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = "auto";
    e.target.style.height = `${Math.min(e.target.scrollHeight, 200)}px`;
  };

  // --- Components for Layout ---

  const Header = (
    <header className="bg-white dark:bg-slate-800 shadow-sm border-b border-slate-200 dark:border-slate-700 p-4 flex items-center justify-between">
      <div className="flex items-center gap-3">
        <button 
            onClick={() => setIsSidebarOpen(true)}
            className="md:hidden p-2 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg"
        >
            <Menu size={20} />
        </button>
        <div className="md:hidden">
          <Logo size="small" />
        </div>
        <div className="hidden md:block text-sm font-semibold text-slate-700 dark:text-slate-200">
           {threads.find(t => t.id === activeThreadId)?.title || "New Chat"}
        </div>
      </div>
      <div className="flex items-center gap-2">
          <button 
            onClick={() => setIsProfileOpen(!isProfileOpen)}
            className="p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-full transition-colors"
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
  );

  const WelcomeScreen = (
    <div className="flex flex-col items-center justify-center min-h-[50vh] text-center space-y-6 animate-fade-in">
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
  );

  const ChatArea = (
    <>
        {activeConversation.messages.length === 0 ? WelcomeScreen : (
            <div className="space-y-6">
                {activeConversation.messages.map((msg, index) => (
                    <ChatMessage key={index} message={msg} />
                ))}
            </div>
        )}

        {activeConversation.isLoading && activeConversation.messages[activeConversation.messages.length - 1]?.role !== "assistant" && (
            <div className="flex justify-start mb-6 mt-6 animate-pulse">
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
    </>
  );

  const InputArea = (
    <>
        <div className="relative flex items-end gap-2 bg-white dark:bg-slate-800 p-2 rounded-2xl border border-slate-200 dark:border-slate-700 shadow-sm focus-within:border-indigo-500 focus-within:ring-1 focus-within:ring-indigo-500 transition-all">
            <textarea
                ref={inputRef}
                value={activeConversation.input}
                onChange={handleInput}
                onKeyDown={handleKeyDown}
                placeholder="Type your answer..."
                className="w-full bg-transparent border-none focus:ring-0 resize-none max-h-[200px] min-h-[44px] py-2.5 px-3 text-slate-800 dark:text-slate-100 placeholder:text-slate-400"
                rows={1}
                disabled={activeConversation.isLoading}
            />
            <button
                onClick={() => sendMessage()}
                disabled={activeConversation.isLoading || !activeConversation.input.trim()}
                className="p-2.5 mb-1 bg-indigo-600 text-white rounded-xl hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors flex-shrink-0"
            >
                {activeConversation.isLoading ? <Loader2 className="w-5 h-5 animate-spin" /> : <Send className="w-5 h-5" />}
            </button>
        </div>
        <p className="text-center text-xs text-slate-400 mt-2 opacity-70">
            AI can make mistakes. Please verify important technical details.
        </p>
    </>
  );

  return (
    <AppLayout
        isSidebarOpen={isSidebarOpen}
        setIsSidebarOpen={setIsSidebarOpen}
        sidebar={
            <Sidebar 
                isOpen={isSidebarOpen}
                setIsOpen={setIsSidebarOpen}
                threads={threads}
                currentThreadId={activeThreadId}
                onSelectThread={handleThreadSelect}
                onDeleteThread={deleteThread}
                onClearAll={clearAllThreads}
                onNewChat={startNewChat}
            />
        }
        header={Header}
        chatArea={ChatArea}
        inputArea={InputArea}
        rightPanel={
            <KnowledgePanel 
                isOpen={isProfileOpen}
                setIsOpen={setIsProfileOpen}
                userProfile={userProfile}
                onClearProfile={clearProfile}
                onUpdateDescription={handleUpdateDescription}
                onUpdateGoals={handleUpdateGoals}
                onUpdateKnowledge={handleUpdateKnowledge}
            />
        }
    />
  );
}

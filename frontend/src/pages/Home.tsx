import { useState, useRef, useEffect } from "react";
import { Send, User, Bot, Loader2, RefreshCw, Terminal } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";

interface Message {
  role: "user" | "assistant" | "system";
  content: string;
}

const ChatMessage = ({ message }: { message: Message }) => {
  const isUser = message.role === "user";

  return (
    <div className={`flex w-full mb-6 ${isUser ? "justify-end" : "justify-start"}`}>
      <div className={`flex max-w-[85%] md:max-w-[75%] ${isUser ? "flex-row-reverse" : "flex-row"} gap-3`}>
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
    </div>
  );
};

export default function Home() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

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
        }),
      });

      if (!response.body) throw new Error("No response body");

      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      setMessages((prev) => [...prev, { role: "assistant", content: "" }]);
      let accumulatedContent = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value, { stream: true });
        const lines = chunk.split("\n\n");

        for (const line of lines) {
          if (line.startsWith("data: ")) {
            const data = line.slice(6);
            if (data === "[DONE]") break;

            try {
              const parsed = JSON.parse(data);
              if (parsed.content) {
                accumulatedContent += parsed.content;
                setMessages((prev) => {
                  const newMessages = [...prev];
                  const lastMsg = newMessages[newMessages.length - 1];
                  if (lastMsg.role === "assistant") {
                    lastMsg.content = accumulatedContent;
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
    <div className="flex flex-col h-screen bg-slate-50 dark:bg-slate-900 text-slate-900 dark:text-slate-100 font-sans">
      {/* Header */}
      <header className="bg-white dark:bg-slate-800 shadow-sm border-b border-slate-200 dark:border-slate-700 p-4 sticky top-0 z-10">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="bg-indigo-600 p-2 rounded-lg">
              <Bot className="w-6 h-6 text-white" />
            </div>
            <div>
              <h1 className="text-xl font-bold bg-gradient-to-r from-indigo-600 to-violet-600 bg-clip-text text-transparent">
                Interview Watson
              </h1>
              <p className="text-xs text-slate-500 dark:text-slate-400">Your AI Technical Coach</p>
            </div>
          </div>
          <button 
            onClick={() => window.location.reload()}
            className="p-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-full transition-colors"
            title="Reset Session"
          >
            <RefreshCw size={20} />
          </button>
        </div>
      </header>

      {/* Main Chat Area */}
      <main className="flex-1 overflow-y-auto p-4 sm:p-6 scroll-smooth">
        <div className="max-w-3xl mx-auto">
          {messages.length === 0 && (
            <div className="flex flex-col items-center justify-center min-h-[60vh] text-center space-y-6 animate-fade-in">
              <div className="w-20 h-20 bg-indigo-100 dark:bg-indigo-900/30 rounded-full flex items-center justify-center mb-4">
                <Bot className="w-10 h-10 text-indigo-600 dark:text-indigo-400" />
              </div>
              <h2 className="text-3xl font-bold text-slate-800 dark:text-slate-100">
                Ready for your interview?
              </h2>
              <p className="text-slate-600 dark:text-slate-400 max-w-md text-lg">
                I can help you review algorithms, system design, or specific language concepts.
              </p>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 w-full max-w-lg mt-8">
                {[
                  "Review Python Memory Management",
                  "Explain ACID properties",
                  "Design a URL Shortener",
                  "Mock Interview: Arrays & Strings"
                ].map((suggestion) => (
                  <button
                    key={suggestion}
                    onClick={() => {
                      setInput(suggestion);
                      // Ideally we would submit directly, but setting input is safer for now
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

      {/* Input Area */}
      <footer className="bg-white dark:bg-slate-800 p-4 border-t border-slate-200 dark:border-slate-700">
        <div className="max-w-3xl mx-auto">
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
  );
}

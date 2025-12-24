import { User, Bot, Terminal, Globe, Activity, BookOpen } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";
import { Prism as SyntaxHighlighter } from "react-syntax-highlighter";
import { vscDarkPlus } from "react-syntax-highlighter/dist/esm/styles/prism";
import { Message } from "../types";
import { DetailPanel } from "./DetailPanel";

export const ChatMessage = ({ message }: { message: Message }) => {
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
                remarkPlugins={[remarkGfm, remarkMath]}
                rehypePlugins={[rehypeKatex]}
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

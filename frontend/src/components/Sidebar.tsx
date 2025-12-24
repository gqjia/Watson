import { Plus, MessageSquare, Trash2, X } from "lucide-react";
import { Thread } from "../types";
import { Logo } from "./Logo";

interface SidebarProps {
    isOpen: boolean;
    setIsOpen: (open: boolean) => void;
    threads: Thread[];
    currentThreadId: string;
    onSelectThread: (id: string) => void;
    onDeleteThread: (id: string, e: React.MouseEvent) => void;
    onClearAll: () => void;
    onNewChat: () => void;
}

export const Sidebar = ({ 
    isOpen, 
    setIsOpen, 
    threads, 
    currentThreadId, 
    onSelectThread, 
    onDeleteThread, 
    onClearAll,
    onNewChat
}: SidebarProps) => {
    return (
      <aside 
        className={`
          fixed md:static inset-y-0 left-0 z-30 w-64 h-full bg-white dark:bg-slate-800 border-r border-slate-200 dark:border-slate-700 transform transition-transform duration-200 ease-in-out flex flex-col
          ${isOpen ? "translate-x-0" : "-translate-x-full md:translate-x-0"}
        `}
      >
        <div className="p-4 border-b border-slate-200 dark:border-slate-700 flex items-center justify-between">
            <Logo size="normal" />
            <button 
                onClick={() => setIsOpen(false)}
                className="md:hidden p-1 hover:bg-slate-100 dark:hover:bg-slate-700 rounded"
            >
                <X size={20} />
            </button>
        </div>
        
        <div className="p-4">
            <button 
                onClick={onNewChat}
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
                    onClick={() => onSelectThread(thread.id)}
                    className={`w-full text-left p-3 rounded-lg text-sm flex items-center gap-3 transition-colors group relative ${
                        thread.id === currentThreadId 
                            ? "bg-slate-100 dark:bg-slate-700 text-indigo-600 dark:text-indigo-400 font-medium" 
                            : "hover:bg-slate-50 dark:hover:bg-slate-700/50 text-slate-600 dark:text-slate-300"
                    }`}
                >
                    <MessageSquare size={16} />
                    <span className="truncate flex-1 pr-6">
                        {thread.title}
                    </span>
                    <span 
                        onClick={(e) => onDeleteThread(thread.id, e)}
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
                    onClick={onClearAll}
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
    );
};

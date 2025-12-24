import { useState } from "react";
import { ChevronDown, ChevronRight } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

export const DetailPanel = ({ title, content, icon: Icon, colorClass }: { title: string, content: string, icon: any, colorClass: string }) => {
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
              <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}>{content}</ReactMarkdown>
           </div>
        </div>
      )}
    </div>
  );
};

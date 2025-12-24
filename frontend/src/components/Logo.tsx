import { Brain, Sparkles } from "lucide-react";

export const Logo = ({ className = "", size = "normal" }: { className?: string, size?: "small" | "normal" | "large" }) => {
  const iconSize = size === "small" ? 18 : size === "large" ? 32 : 24;
  const textSize = size === "small" ? "text-lg" : size === "large" ? "text-3xl" : "text-xl";
  const containerSize = size === "small" ? "w-7 h-7" : size === "large" ? "w-12 h-12" : "w-9 h-9";

  return (
    <div className={`flex items-center gap-2.5 ${className} select-none`}>
      <div className="relative flex items-center justify-center">
        <div className={`absolute inset-0 bg-indigo-500 blur-md opacity-20 rounded-xl ${containerSize}`}></div>
        <div className={`relative bg-gradient-to-br from-indigo-600 to-violet-600 text-white flex items-center justify-center rounded-lg shadow-sm ${containerSize}`}>
           <Brain size={iconSize} className="relative z-10" />
           <Sparkles size={Math.floor(iconSize / 2)} className="absolute -top-1 -right-1 text-amber-300 fill-amber-300 animate-pulse" style={{ animationDuration: '3s' }} />
        </div>
      </div>
      <span className={`${textSize} font-bold bg-clip-text text-transparent bg-gradient-to-r from-slate-800 to-slate-600 dark:from-white dark:to-slate-300 tracking-tight`}>
        Watson
      </span>
    </div>
  );
};

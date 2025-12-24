import { useState, useEffect } from "react";
import { Loader2, Edit2, Check, X } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import remarkMath from "remark-math";
import rehypeKatex from "rehype-katex";

export const EditableSection = ({ 
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
                            <ReactMarkdown remarkPlugins={[remarkGfm, remarkMath]} rehypePlugins={[rehypeKatex]}>{content}</ReactMarkdown>
                        ) : (
                            <p className="whitespace-pre-wrap">{content}</p>
                        )}
                    </div>
                )}
            </div>
        </div>
    );
};

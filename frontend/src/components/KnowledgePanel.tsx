import { Brain, User, Target, BookOpen, Trash2, X } from "lucide-react";
import { UserProfile } from "../types";
import { EditableSection } from "./EditableSection";

interface KnowledgePanelProps {
    isOpen: boolean;
    setIsOpen: (open: boolean) => void;
    userProfile: UserProfile | null;
    onClearProfile: () => void;
    onUpdateDescription: (desc: string) => Promise<void>;
    onUpdateGoals: (goals: string) => Promise<void>;
    onUpdateKnowledge: (category: string, content: string) => Promise<void>;
}

export const KnowledgePanel = ({
    isOpen,
    setIsOpen,
    userProfile,
    onClearProfile,
    onUpdateDescription,
    onUpdateGoals,
    onUpdateKnowledge
}: KnowledgePanelProps) => {
    if (!isOpen || !userProfile) return null;

    return (
        <>
            {/* Backdrop for screens smaller than xl */}
            <div 
                className="fixed inset-0 bg-black/20 z-20 xl:hidden animate-fade-in"
                onClick={() => setIsOpen(false)}
            />
            
            <aside className="
                fixed inset-y-0 right-0 z-30 w-full sm:w-[400px] xl:w-[450px] 
                bg-white dark:bg-slate-800 border-l border-slate-200 dark:border-slate-700 
                overflow-y-auto flex flex-col animate-slide-in-right shrink-0 shadow-xl xl:shadow-none xl:static
            ">
            <div className="p-6 border-b border-slate-200 dark:border-slate-700 flex justify-between items-center">
                <div>
                    <h3 className="font-bold text-xl flex items-center gap-2 text-slate-800 dark:text-slate-100">
                        <Brain className="w-5 h-5 text-purple-600" />
                        Knowledge Profile
                    </h3>
                    <p className="text-xs text-slate-500 mt-1">AI-generated assessment of your skills</p>
                </div>
                <button
                    onClick={() => setIsOpen(false)}
                    className="xl:hidden p-2 mr-2 text-slate-500 hover:bg-slate-100 dark:hover:bg-slate-700 rounded-lg transition-colors"
                >
                    <X size={20} />
                </button>
                <button
                    onClick={onClearProfile}
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
                        onSave={onUpdateDescription}
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
                        onSave={onUpdateGoals}
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
                                    onSave={(newContent) => onUpdateKnowledge(category, newContent)}
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
        </>
    );
};

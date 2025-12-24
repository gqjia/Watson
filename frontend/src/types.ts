export interface Message {
  role: "user" | "assistant" | "system";
  content: string;
  details?: {
    critic?: string;
    mentor?: string;
    draft?: string;
    search?: string;
  };
}

export interface Thread {
  id: string;
  title: string;
  updated_at: string;
}

export interface UserProfile {
  learning_goals: string;
  self_description: string;
  knowledge: Record<string, string>;
}

import { useState, useRef, useEffect, useCallback } from 'react';
import { Message, Thread, UserProfile } from '../types';
import { API_BASE_URL } from '../lib/constants';

interface ConversationState {
  messages: Message[];
  isLoading: boolean;
  input: string;
  isLoaded: boolean;
}

export function useChat() {
  const [conversations, setConversations] = useState<Record<string, ConversationState>>({});
  const [activeThreadId, setActiveThreadId] = useState("");
  const [threads, setThreads] = useState<Thread[]>([]);
  const [userProfile, setUserProfile] = useState<UserProfile | null>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // Derived state
  const activeConversation = conversations[activeThreadId] || {
      messages: [],
      isLoading: false,
      input: "",
      isLoaded: false
  };

  const updateConversation = useCallback((id: string, updates: Partial<ConversationState>) => {
      setConversations(prev => ({
          ...prev,
          [id]: {
              ...(prev[id] || { messages: [], isLoading: false, input: "", isLoaded: false }),
              ...updates
          }
      }));
  }, []);

  const fetchThreads = useCallback(async () => {
      try {
          const res = await fetch(`${API_BASE_URL}/chat/threads`);
          const data = await res.json();
          if (data && Array.isArray(data.threads)) {
              setThreads(data.threads);
          }
      } catch (e) {
          console.error("Failed to fetch threads", e);
      }
  }, []);

  const fetchProfile = useCallback(async () => {
    try {
        const res = await fetch(`${API_BASE_URL}/chat/profile`);
        const data = await res.json();
        setUserProfile(data);
    } catch (e) {
        console.error("Failed to fetch profile", e);
    }
  }, []);

  const loadThreadHistory = useCallback(async (id: string) => {
      if (!id) return;
      // If already loaded or loading, skip to avoid loops, but check if we have messages
      setConversations(prev => {
        if (prev[id]?.isLoaded) return prev;
        return {
             ...prev,
             [id]: { ...(prev[id] || { messages: [], input: "" }), isLoading: true, isLoaded: false }
        };
      });

      try {
          const res = await fetch(`${API_BASE_URL}/chat/history/${id}`);
          const data = await res.json();
          updateConversation(id, { 
              messages: data.messages, 
              isLoading: false,
              isLoaded: true 
          });
      } catch (e) {
          console.error("Failed to load history", e);
          updateConversation(id, { isLoading: false });
      }
  }, [updateConversation]);

  // Initial load
  useEffect(() => {
    fetchThreads();
    fetchProfile();
    
    let storedThreadId = localStorage.getItem("watson_thread_id");
    if (!storedThreadId) {
        storedThreadId = crypto.randomUUID();
        localStorage.setItem("watson_thread_id", storedThreadId);
    }
    setActiveThreadId(storedThreadId);
    loadThreadHistory(storedThreadId);
  }, [fetchThreads, fetchProfile, loadThreadHistory]);

  const handleThreadSelect = (id: string) => {
      setActiveThreadId(id);
      localStorage.setItem("watson_thread_id", id);
      loadThreadHistory(id);
  };

  const startNewChat = () => {
      const newId = crypto.randomUUID();
      setActiveThreadId(newId);
      localStorage.setItem("watson_thread_id", newId);
      updateConversation(newId, { messages: [], isLoading: false, input: "", isLoaded: true });
  };

  const deleteThread = async (id: string) => {
    try {
        const res = await fetch(`${API_BASE_URL}/chat/threads/${id}`, { method: "DELETE" });
        if (res.ok) {
            setThreads(prev => prev.filter(t => t.id !== id));
            setConversations(prev => {
                const next = { ...prev };
                delete next[id];
                return next;
            });
            if (id === activeThreadId) {
                startNewChat();
            }
        }
    } catch (e) {
        console.error("Failed to delete thread", e);
    }
  };

  const clearAllThreads = async () => {
    try {
        const res = await fetch(`${API_BASE_URL}/chat/threads`, { method: "DELETE" });
        if (res.ok) {
            setThreads([]);
            setConversations({});
            startNewChat();
        }
    } catch (e) {
        console.error("Failed to delete all threads", e);
    }
  };

  const sendMessage = async (e?: React.FormEvent) => {
    if (e) e.preventDefault();
    const currentId = activeThreadId;
    const currentInput = conversations[currentId]?.input || "";

    if (!currentInput.trim() || conversations[currentId]?.isLoading) return;

    const userMessage: Message = { role: "user", content: currentInput };
    
    // Optimistically add thread
    setThreads(prev => {
        if (prev.some(t => t.id === currentId)) return prev;
        return [{
            id: currentId,
            title: currentInput.slice(0, 30) + (currentInput.length > 30 ? "..." : ""),
            updated_at: new Date().toISOString()
        }, ...prev];
    });

    updateConversation(currentId, {
        messages: [...(conversations[currentId]?.messages || []), userMessage],
        input: "",
        isLoading: true
    });

    if (inputRef.current) inputRef.current.style.height = "auto";

    try {
      const currentMessages = conversations[currentId]?.messages || [];

      const response = await fetch(`${API_BASE_URL}/chat/stream`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: [...currentMessages, userMessage],
          thread_id: currentId,
        }),
      });

      if (!response.body) throw new Error("No response body");
      
      const reader = response.body.getReader();
      const decoder = new TextDecoder();
      
      // Add empty assistant message
      setConversations(prev => {
        const prevConv = prev[currentId];
        return {
            ...prev,
            [currentId]: {
                ...prevConv,
                messages: [...prevConv.messages, { role: "assistant", content: "" }]
            }
        };
      });

      let accumulatedContent = "";
      let accumulatedCritic = "";
      let accumulatedMentor = "";
      let accumulatedDraft = "";
      let accumulatedSearch = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) {
            fetchThreads();
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
                 if (node === "coach_draft") accumulatedDraft += "\n\n---\n**New Revision**\n---\n\n";
                 else if (node === "critic") accumulatedCritic += "\n\n---\n**New Revision**\n---\n\n";
                 continue;
              }

              if (content) {
                if (node === "coach") accumulatedContent += content;
                else if (node === "coach_draft") accumulatedDraft += content;
                else if (node === "critic") accumulatedCritic += content;
                else if (node === "mentor") accumulatedMentor += content;
                else if (node === "search") accumulatedSearch += content;

                setConversations(prev => {
                  const prevConv = prev[currentId];
                  if (!prevConv) return prev;

                  const newMessages = [...prevConv.messages];
                  const lastMsgIndex = newMessages.length - 1;
                  const lastMsg = { ...newMessages[lastMsgIndex] };
                  newMessages[lastMsgIndex] = lastMsg;
                  
                  if (lastMsg.role === "assistant") {
                    if (node === "coach") lastMsg.content = accumulatedContent;
                    else if (node === "coach_draft") {
                        lastMsg.details = { ...lastMsg.details, draft: accumulatedDraft };
                    } else if (node === "critic") {
                        lastMsg.details = { ...lastMsg.details, critic: accumulatedCritic };
                    } else if (node === "mentor") {
                        lastMsg.details = { ...lastMsg.details, mentor: accumulatedMentor };
                    } else if (node === "search") {
                        lastMsg.details = { ...lastMsg.details, search: accumulatedSearch };
                    }
                  }
                  
                  return { ...prev, [currentId]: { ...prevConv, messages: newMessages } };
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
      updateConversation(currentId, { isLoading: false });
    }
  };

  const setInput = (val: string) => updateConversation(activeThreadId, { input: val });

  const handleUpdateGoals = async (newGoals: string) => {
    await fetch(`${API_BASE_URL}/chat/profile/goals`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ goals: newGoals })
    });
    setUserProfile(prev => prev ? { ...prev, learning_goals: newGoals } : null);
  };

  const handleUpdateDescription = async (newDescription: string) => {
    await fetch(`${API_BASE_URL}/chat/profile/description`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ description: newDescription })
    });
    setUserProfile(prev => prev ? { ...prev, self_description: newDescription } : null);
  };

  const handleUpdateKnowledge = async (category: string, newContent: string) => {
    await fetch(`${API_BASE_URL}/chat/profile/knowledge`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ category, content: newContent })
    });
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

  const clearProfile = async () => {
    if (!confirm("Are you sure you want to clear your knowledge profile? This action cannot be undone.")) return;
    try {
        await fetch(`${API_BASE_URL}/chat/profile`, { method: "DELETE" });
        fetchProfile();
    } catch (e) {
        console.error("Failed to clear profile", e);
    }
  };

  return {
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
    setUserProfile,
    fetchProfile,
    handleUpdateGoals,
    handleUpdateDescription,
    handleUpdateKnowledge,
    clearProfile
  };
}

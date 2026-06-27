import { useState, useCallback, useRef, useEffect } from 'react';

export function useChat(sessionId) {
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  // Auto-scroll logic
  const messagesEndRef = useRef(null);
  
  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const sendMessage = useCallback(async (text) => {
    if (!text.trim() || !sessionId || isLoading) return;

    // Add user message to UI immediately
    const userMsg = { id: Date.now(), role: 'user', content: text };
    setMessages(prev => [...prev, userMsg]);
    setIsLoading(true);
    setError(null);

    try {
      const res = await fetch('http://localhost:8000/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          session_id: sessionId,
          question: text
        })
      });

      if (!res.ok) {
        throw new Error(`Server returned ${res.status}`);
      }

      const data = await res.json();
      
      const botMsg = {
        id: Date.now() + 1,
        role: 'assistant',
        content: data.answer,
        citations: data.citations || [],
        tool_used: data.tool_used,
      };

      setMessages(prev => [...prev, botMsg]);
    } catch (err) {
      console.error("Chat error:", err);
      setError("Failed to connect to the AI agent. Make sure the backend is running.");
      setMessages(prev => [...prev, { 
        id: Date.now() + 1, 
        role: 'system', 
        isError: true,
        content: "I'm sorry, I couldn't process your request right now. Please try again."
      }]);
    } finally {
      setIsLoading(false);
    }
  }, [sessionId, isLoading]);

  return {
    messages,
    isLoading,
    error,
    sendMessage,
    messagesEndRef
  };
}

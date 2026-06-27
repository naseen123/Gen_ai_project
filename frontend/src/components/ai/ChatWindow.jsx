import { useState, useRef, useEffect } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Send, Bot, RefreshCw } from 'lucide-react';
import { useChat } from '../../hooks/useChat';
import ChatBubble from './ChatBubble';
import TypingIndicator from './TypingIndicator';
import SuggestionCards from './SuggestionCards';

export default function ChatWindow({ sessionId }) {
  const { messages, isLoading, error, sendMessage, messagesEndRef } = useChat(sessionId);
  const [inputValue, setInputValue] = useState('');
  const inputRef = useRef(null);

  // Auto-focus input when opened
  useEffect(() => {
    inputRef.current?.focus();
  }, []);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;
    sendMessage(inputValue);
    setInputValue('');
  };

  const handleSuggestionClick = (suggestion) => {
    sendMessage(suggestion);
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.95, transformOrigin: 'bottom right' }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      exit={{ opacity: 0, y: 20, scale: 0.95 }}
      transition={{ duration: 0.2 }}
      className="fixed bottom-24 right-4 md:right-6 w-[calc(100vw-32px)] md:w-[380px] h-[600px] max-h-[calc(100vh-120px)] flex flex-col glass rounded-2xl shadow-2xl overflow-hidden z-40 border border-border"
    >
      {/* Header */}
      <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-surface/50">
        <div className="flex items-center gap-2">
          <div className="w-8 h-8 rounded-lg bg-primary/20 flex items-center justify-center">
            <Bot className="w-5 h-5 text-primary" />
          </div>
          <div>
            <h3 className="font-heading font-semibold text-accent text-sm">TeamLens AI</h3>
            <p className="text-[10px] text-success flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-success"></span> Online
            </p>
          </div>
        </div>
        {/* Close handled by parent toggle, but could add options here */}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4 scroll-smooth">
        {messages.length === 0 ? (
          <div className="h-full flex flex-col justify-end">
            <div className="text-center mb-6">
              <div className="w-16 h-16 rounded-full bg-primary/10 flex items-center justify-center mx-auto mb-3">
                <Bot className="w-8 h-8 text-primary" />
              </div>
              <p className="text-sm text-gray-400">Ask me anything about this chat!</p>
            </div>
            <SuggestionCards onSelect={handleSuggestionClick} />
          </div>
        ) : (
          <>
            {messages.map((msg) => (
              <ChatBubble key={msg.id} message={msg} />
            ))}
            {isLoading && <TypingIndicator />}
            {error && (
              <div className="text-center text-xs text-danger bg-danger/10 py-2 rounded-lg">
                {error}
              </div>
            )}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="p-3 bg-surface/80 border-t border-border">
        <form onSubmit={handleSubmit} className="relative flex items-center">
          <input
            ref={inputRef}
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            placeholder="Ask a question..."
            disabled={isLoading}
            className="w-full bg-bg border border-border rounded-xl pl-4 pr-12 py-3 text-sm text-accent focus:outline-none focus:border-primary transition-colors disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading}
            className="absolute right-2 p-1.5 bg-primary text-white rounded-lg hover:bg-indigo-500 disabled:opacity-50 disabled:hover:bg-primary transition-colors"
          >
            {isLoading ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Send className="w-4 h-4" />}
          </button>
        </form>
        <p className="text-[10px] text-center text-gray-500 mt-2">
          AI can make mistakes. Check the citations.
        </p>
      </div>
    </motion.div>
  );
}

import { useState, useEffect } from 'react';
import { Bot, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import ChatWindow from './ChatWindow';

export default function FloatingAssistant({ sessionId, isReady }) {
  const [isOpen, setIsOpen] = useState(false);
  const [hasUnread, setHasUnread] = useState(false);

  // Show an unread badge briefly when it becomes ready to encourage clicks
  useEffect(() => {
    if (isReady && !isOpen) {
      setHasUnread(true);
      const timer = setTimeout(() => setHasUnread(false), 5000);
      return () => clearTimeout(timer);
    }
  }, [isReady, isOpen]);

  // Don't render until we have a parsed chat (dashboard view)
  if (!isReady) return null;

  return (
    <>
      {/* Floating Button */}
      <motion.div
        className="fixed bottom-6 right-6 z-50 flex flex-col items-end"
        initial={{ scale: 0, opacity: 0 }}
        animate={{ scale: 1, opacity: 1 }}
        transition={{ type: "spring", stiffness: 260, damping: 20, delay: 1 }}
      >
        <AnimatePresence>
          {hasUnread && !isOpen && (
            <motion.div
              initial={{ opacity: 0, y: 10, scale: 0.8 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, scale: 0.8, transition: { duration: 0.2 } }}
              className="mb-3 bg-surface border border-primary/50 text-xs px-3 py-2 rounded-xl shadow-lg glow-primary text-accent whitespace-nowrap"
            >
              Ask me about this chat! ✨
              <div className="absolute -bottom-1.5 right-6 w-3 h-3 bg-surface border-b border-r border-primary/50 rotate-45"></div>
            </motion.div>
          )}
        </AnimatePresence>

        <button
          onClick={() => {
            setIsOpen(!isOpen);
            setHasUnread(false);
          }}
          className={`relative flex items-center justify-center w-14 h-14 rounded-full shadow-2xl transition-all duration-300 ${isOpen
              ? 'bg-surface border border-border text-gray-400 hover:text-white'
              : 'bg-primary text-white hover:bg-indigo-500 glow-primary hover:scale-105'
            }`}
        >
          {isOpen ? <X className="w-6 h-6" /> : <Bot className="w-7 h-7" />}

          {/* Notification dot */}
          {!isOpen && hasUnread && (
            <span className="absolute top-0 right-0 w-3.5 h-3.5 bg-danger border-2 border-bg rounded-full"></span>
          )}
        </button>
      </motion.div>

      {/* Chat Window overlay */}
      <AnimatePresence>
        {isOpen && (
          <ChatWindow sessionId={sessionId} onClose={() => setIsOpen(false)} />
        )}
      </AnimatePresence>
    </>
  );
}

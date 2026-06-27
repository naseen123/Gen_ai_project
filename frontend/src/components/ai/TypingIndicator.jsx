import { motion, AnimatePresence } from 'framer-motion';
export default function TypingIndicator() {
  return (
    <div className="flex gap-3 max-w-[80%]">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-surface border border-border flex items-center justify-center mt-1">
        <span className="w-4 h-4 rounded-full bg-primary/20 flex items-center justify-center">
          <span className="w-1.5 h-1.5 rounded-full bg-primary animate-pulse"></span>
        </span>
      </div>
      
      <div className="bg-surface border border-border px-4 py-3 rounded-2xl rounded-tl-sm flex gap-1.5 items-center h-10 shadow-sm">
        <motion.span 
          animate={{ scale: [1, 1.2, 1], opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 1, repeat: Infinity, delay: 0 }}
          className="w-1.5 h-1.5 bg-gray-400 rounded-full"
        />
        <motion.span 
          animate={{ scale: [1, 1.2, 1], opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 1, repeat: Infinity, delay: 0.2 }}
          className="w-1.5 h-1.5 bg-gray-400 rounded-full"
        />
        <motion.span 
          animate={{ scale: [1, 1.2, 1], opacity: [0.4, 1, 0.4] }}
          transition={{ duration: 1, repeat: Infinity, delay: 0.4 }}
          className="w-1.5 h-1.5 bg-gray-400 rounded-full"
        />
      </div>
    </div>
  );
}


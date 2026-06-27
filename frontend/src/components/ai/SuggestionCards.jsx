import { motion, AnimatePresence } from 'framer-motion';
import { MessageSquare } from 'lucide-react';

const SUGGESTIONS = [
  "Who contributed the most?",
  "Who handled frontend?",
  "Who handled backend?",
  "Who was most responsive?",
  "Which tasks are pending?",
  "Summarize this project.",
  "Compare Rahul and Vishnu.",
  "Who promised but didn't deliver?",
  "Find discussions about authentication.",
  "Find all deployment discussions."
];

// Shuffle array
const getRandomSuggestions = (count) => {
  const shuffled = [...SUGGESTIONS].sort(() => 0.5 - Math.random());
  return shuffled.slice(0, count);
};

export default function SuggestionCards({ onSelect }) {
  // Get 6 random suggestions on mount
  const currentSuggestions = getRandomSuggestions(6);

  return (
    <div className="grid grid-cols-2 gap-2 mt-4">
      {currentSuggestions.map((text, index) => (
        <motion.button
          key={index}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ delay: index * 0.05 }}
          onClick={() => onSelect(text)}
          className="text-left px-3 py-2 bg-surface hover:bg-border border border-border hover:border-primary/50 rounded-xl text-xs text-gray-300 transition-all duration-200 flex items-start gap-2 group"
        >
          <MessageSquare className="w-3.5 h-3.5 text-primary/70 mt-0.5 group-hover:text-primary transition-colors flex-shrink-0" />
          <span className="leading-snug">{text}</span>
        </motion.button>
      ))}
    </div>
  );
}


import { useState } from 'react';
import { ChevronDown, ChevronUp, User } from 'lucide-react';
import { AnimatePresence } from 'framer-motion';

export default function CitationCard({ citation }) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Parse ISO date to readable format
  let timeStr = citation.timestamp;
  try {
    const d = new Date(citation.timestamp);
    if (!isNaN(d.getTime())) {
      timeStr = d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
    }
  } catch {
    // Keep original string if invalid date
  }

  return (
    <div className="bg-bg border border-border rounded-lg overflow-hidden text-xs">
      <button 
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center justify-between px-3 py-2 hover:bg-surface transition-colors text-left"
      >
        <div className="flex items-center gap-2 truncate pr-2">
          <span className="w-1 h-3 bg-primary rounded-full"></span>
          <User className="w-3 h-3 text-gray-400" />
          <span className="font-semibold text-gray-300 truncate max-w-[100px]">{citation.sender}</span>
          <span className="text-gray-500">•</span>
          <span className="text-gray-500 truncate">{timeStr}</span>
        </div>
        {isExpanded ? <ChevronUp className="w-3.5 h-3.5 text-gray-500 flex-shrink-0" /> : <ChevronDown className="w-3.5 h-3.5 text-gray-500 flex-shrink-0" />}
      </button>

      <AnimatePresence>
        {isExpanded && (
          <motion.div 
            initial={{ height: 0, opacity: 0 }}
            animate={{ height: 'auto', opacity: 1 }}
            exit={{ height: 0, opacity: 0 }}
            className="border-t border-border/50 bg-surface/50"
          >
            <div className="p-3 text-gray-300 whitespace-pre-wrap leading-relaxed">
              {citation.message}
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
}

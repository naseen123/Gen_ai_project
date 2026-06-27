import { motion, AnimatePresence } from 'framer-motion';
import { Bot, User } from 'lucide-react';
import CitationCard from './CitationCard';

// Simple markdown parser for basic formatting
const parseMarkdown = (text) => {
  if (!text) return '';
  let html = text
    // Bold
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // Bullet points
    .replace(/^\s*-\s+(.*)/gm, '<li>$1</li>')
    // Line breaks
    .replace(/\n/g, '<br />');

  // Wrap lists
  if (html.includes('<li>')) {
    html = html.replace(/(<li>.*<\/li>)/s, '<ul class="list-disc pl-4 my-2">$1</ul>');
  }

  return html;
};

export default function ChatBubble({ message }) {
  const isUser = message.role === 'user';
  const isSystem = message.role === 'system';

  if (isSystem) {
    return (
      <div className="flex justify-center my-4">
        <div className={`px-3 py-1 rounded-full text-xs ${message.isError ? 'bg-danger/20 text-danger' : 'bg-surface text-gray-400'}`}>
          {message.content}
        </div>
      </div>
    );
  }

  return (
    <motion.div 
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={`flex gap-3 max-w-[90%] ${isUser ? 'ml-auto flex-row-reverse' : ''}`}
    >
      {/* Avatar */}
      <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center mt-1 ${
        isUser ? 'bg-primary/20 text-primary' : 'bg-surface border border-border text-gray-400'
      }`}>
        {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
      </div>

      {/* Message Content */}
      <div className={`flex flex-col ${isUser ? 'items-end' : 'items-start'}`}>
        <div className={`px-4 py-2.5 rounded-2xl text-sm leading-relaxed shadow-sm ${
          isUser 
            ? 'bg-primary text-white rounded-tr-sm' 
            : 'bg-surface border border-border text-gray-200 rounded-tl-sm'
        }`}>
          {isUser ? (
            message.content
          ) : (
            <div 
              className="prose prose-invert prose-p:my-1 prose-ul:my-1 text-sm max-w-none"
              dangerouslySetInnerHTML={{ __html: parseMarkdown(message.content) }} 
            />
          )}
        </div>

        {/* Tool Used Badge */}
        {!isUser && message.tool_used && message.tool_used !== 'semantic_search' && (
          <div className="mt-1 text-[10px] text-gray-500 font-mono px-1">
            used: {message.tool_used}
          </div>
        )}

        {/* Citations */}
        {!isUser && message.citations && message.citations.length > 0 && (
          <div className="mt-2 space-y-2 w-full">
            <p className="text-xs font-semibold text-gray-400 ml-1">Sources ({message.citations.length})</p>
            {message.citations.map((cite, i) => (
              <CitationCard key={i} citation={cite} />
            ))}
          </div>
        )}
      </div>
    </motion.div>
  );
}


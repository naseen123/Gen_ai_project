const COLORS = [
  '#5B5BF0', '#a78bfa', '#22c55e', '#eab308', '#ef4444',
  '#06b6d4', '#f97316', '#ec4899', '#84cc16', '#14b8a6'
]

export default function WordCloud({ words = [] }) {
  if (!words || words.length === 0) {
    return (
      <div className="glass p-5 rounded-2xl">
        <h3 className="font-heading font-semibold text-accent mb-3">Top Words</h3>
        <p className="text-gray-500 text-sm italic">No word data available</p>
      </div>
    )
  }

  // Assign font sizes based on rank
  const maxSize = 2.2
  const minSize = 0.9

  return (
    <div className="glass p-5 rounded-2xl animate-fade-in">
      <h3 className="font-heading font-semibold text-accent mb-4">Top Words</h3>
      <div className="flex flex-wrap gap-3 items-center justify-center min-h-[100px] py-2">
        {words.map((word, i) => {
          const size = maxSize - (i / Math.max(words.length - 1, 1)) * (maxSize - minSize)
          return (
            <span
              key={word}
              className="px-3 py-1 rounded-full font-semibold transition-transform hover:scale-110 cursor-default"
              style={{
                fontSize: `${size}rem`,
                color: COLORS[i % COLORS.length],
                background: `${COLORS[i % COLORS.length]}18`,
                border: `1px solid ${COLORS[i % COLORS.length]}44`,
              }}
            >
              {word}
            </span>
          )
        })}
      </div>
    </div>
  )
}

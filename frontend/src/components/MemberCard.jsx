import { Crown } from 'lucide-react'

function getScoreClass(score) {
  if (score >= 7) return 'badge-green'
  if (score >= 4) return 'badge-yellow'
  return 'badge-red'
}

function getScoreColor(score) {
  if (score >= 7) return '#22c55e'
  if (score >= 4) return '#eab308'
  return '#ef4444'
}

export default function MemberCard({ member, rank, onClick, selected }) {
  const score = member.overall_score ?? 0
  const scoreClass = getScoreClass(score)
  const scoreColor = getScoreColor(score)
  const isTop = rank === 1

  return (
    <div
      onClick={() => onClick && onClick(member)}
      className={`member-card glass p-4 rounded-2xl cursor-pointer transition-all duration-200
        ${selected ? 'border-primary glow-primary border' : 'border border-transparent'}
        ${isTop ? 'ring-1 ring-warning/40' : ''}
      `}
    >
      <div className="flex items-center gap-3">
        {/* Rank */}
        <div className="flex-shrink-0 w-8 text-center">
          {isTop ? (
            <Crown className="w-5 h-5 text-warning mx-auto" />
          ) : (
            <span className="text-sm font-bold text-gray-500">#{rank}</span>
          )}
        </div>

        {/* Avatar */}
        <div
          className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0"
          style={{ background: `linear-gradient(135deg, ${scoreColor}66, ${scoreColor}33)`, border: `2px solid ${scoreColor}66` }}
        >
          {member.name?.charAt(0)?.toUpperCase() || '?'}
        </div>

        {/* Name & summary */}
        <div className="flex-1 min-w-0">
          <p className="font-semibold text-accent truncate font-heading">{member.name}</p>
          <p className="text-xs text-gray-400 truncate">{member.summary?.split('.')[0] || 'Team member'}</p>
        </div>

        {/* Score badge */}
        <div className={`px-3 py-1 rounded-full text-sm font-bold flex-shrink-0 ${scoreClass}`}>
          {score.toFixed(1)}
        </div>
      </div>

      {/* Progress bar */}
      <div className="mt-3 bg-surface rounded-full h-1.5 overflow-hidden">
        <div
          className="h-full rounded-full transition-all duration-1000"
          style={{ width: `${(score / 10) * 100}%`, background: `linear-gradient(90deg, ${scoreColor}, ${scoreColor}99)` }}
        />
      </div>
    </div>
  )
}

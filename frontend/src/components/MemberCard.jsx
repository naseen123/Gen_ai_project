import { Crown, Ghost } from 'lucide-react'

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

/**
 * Derives a role label from a member's AI-produced score breakdown.
 * Priority order: Leader → Executor → Communicator → Ghost → Contributor
 */
export function deriveRole(member) {
  const s = member?.scores || {}
  const freq = s.message_frequency ?? 0
  const init = s.initiative ?? 0
  const own = s.task_ownership ?? 0
  const ft = s.follow_through ?? 0
  const resp = s.responsiveness ?? 0

  if (freq <= 3) return { label: 'Ghost', color: '#6b7280', bg: 'rgba(107,114,128,0.15)', border: 'rgba(107,114,128,0.3)' }
  if (init >= 7 && own >= 7) return { label: 'Leader', color: '#f59e0b', bg: 'rgba(245,158,11,0.15)', border: 'rgba(245,158,11,0.3)' }
  if (ft >= 7 && own >= 6) return { label: 'Executor', color: '#6366f1', bg: 'rgba(99,102,241,0.15)', border: 'rgba(99,102,241,0.3)' }
  if (resp >= 7 && freq >= 6) return { label: 'Communicator', color: '#22d3ee', bg: 'rgba(34,211,238,0.15)', border: 'rgba(34,211,238,0.3)' }
  return { label: 'Contributor', color: '#a78bfa', bg: 'rgba(167,139,250,0.15)', border: 'rgba(167,139,250,0.3)' }
}

export default function MemberCard({ member, rank, onClick, selected, messageCount }) {
  const score = member.overall_score ?? 0
  const scoreClass = getScoreClass(score)
  const scoreColor = getScoreColor(score)
  const isTop = rank === 1
  const role = deriveRole(member)
  const isGhost = role.label === 'Ghost'

  return (
    <div
      onClick={() => onClick && onClick(member)}
      className={`member-card glass p-4 rounded-2xl cursor-pointer transition-all duration-200
        ${selected ? 'border-primary glow-primary border' : 'border border-transparent'}
        ${isTop ? 'ring-1 ring-warning/40' : ''}
        ${isGhost ? 'opacity-75' : ''}
      `}
    >
      <div className="flex items-center gap-3">
        {/* Rank */}
        <div className="flex-shrink-0 w-8 text-center">
          {isTop ? (
            <Crown className="w-5 h-5 text-warning mx-auto" />
          ) : isGhost ? (
            <span className="text-lg">👻</span>
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
          <div className="flex items-center gap-2 flex-wrap">
            <p className="font-semibold text-accent truncate font-heading">{member.name}</p>
            {/* Role badge */}
            <span
              className="px-2 py-0.5 rounded-full text-xs font-semibold flex-shrink-0"
              style={{ color: role.color, background: role.bg, border: `1px solid ${role.border}` }}
            >
              {role.label}
            </span>
          </div>
          <div className="flex items-center gap-3 mt-0.5">
            <p className="text-xs text-gray-400 truncate">{member.summary?.split('.')[0] || 'Team member'}</p>
            {messageCount !== undefined && (
              <span className="text-xs text-gray-500 flex-shrink-0">💬 {messageCount}</span>
            )}
          </div>
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

import { useState } from 'react'
import { deriveRole } from './MemberCard'
import {
  RadarChart as RechartsRadar,
  PolarGrid,
  PolarAngleAxis,
  Radar,
  ResponsiveContainer,
  Tooltip,
  Legend,
} from 'recharts'

const SCORE_KEYS = [
  { key: 'message_frequency', label: 'Frequency' },
  { key: 'initiative',        label: 'Initiative' },
  { key: 'task_ownership',   label: 'Ownership' },
  { key: 'follow_through',   label: 'Follow-Through' },
  { key: 'responsiveness',   label: 'Responsive' },
]

function buildRadarData(memberA, memberB) {
  return SCORE_KEYS.map(({ key, label }) => ({
    axis: label,
    [memberA?.name ?? 'A']: memberA?.scores?.[key] ?? 0,
    [memberB?.name ?? 'B']: memberB?.scores?.[key] ?? 0,
  }))
}

function DiffRow({ label, a, b }) {
  const diff = (a ?? 0) - (b ?? 0)
  const color = diff > 0 ? '#22c55e' : diff < 0 ? '#ef4444' : '#9ca3af'
  const sign  = diff > 0 ? '+' : ''
  return (
    <tr className="border-b border-border/40 hover:bg-surface/50">
      <td className="py-2 px-3 text-gray-400 text-sm">{label}</td>
      <td className="py-2 px-3 text-center font-semibold text-accent text-sm">{(a ?? 0).toFixed(1)}</td>
      <td className="py-2 px-3 text-center font-semibold text-accent text-sm">{(b ?? 0).toFixed(1)}</td>
      <td className="py-2 px-3 text-center text-sm font-bold" style={{ color }}>
        {sign}{diff.toFixed(1)}
      </td>
    </tr>
  )
}

export default function ComparePanel({ members, messageCounts }) {
  const [nameA, setNameA] = useState(members[0]?.name ?? '')
  const [nameB, setNameB] = useState(members[1]?.name ?? members[0]?.name ?? '')

  const memberA = members.find(m => m.name === nameA) || members[0]
  const memberB = members.find(m => m.name === nameB) || members[1] || members[0]

  const radarData = buildRadarData(memberA, memberB)
  const roleA = deriveRole(memberA)
  const roleB = deriveRole(memberB)

  const selectStyle =
    'bg-surface border border-border text-accent rounded-xl px-4 py-2 text-sm focus:outline-none focus:border-primary'

  return (
    <div className="animate-fade-in space-y-6">
      {/* Member selectors */}
      <div className="glass p-5 rounded-2xl">
        <h2 className="font-heading text-xl font-bold gradient-text mb-4">Member Comparison</h2>
        <div className="flex flex-wrap items-center gap-4">
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-primary flex-shrink-0" />
            <select value={nameA} onChange={e => setNameA(e.target.value)} className={selectStyle}>
              {members.map(m => <option key={m.name} value={m.name}>{m.name}</option>)}
            </select>
          </div>
          <span className="text-gray-500 font-bold">vs</span>
          <div className="flex items-center gap-2">
            <span className="w-3 h-3 rounded-full bg-purple-400 flex-shrink-0" />
            <select value={nameB} onChange={e => setNameB(e.target.value)} className={selectStyle}>
              {members.map(m => <option key={m.name} value={m.name}>{m.name}</option>)}
            </select>
          </div>
        </div>
      </div>

      {/* Quick stats side-by-side */}
      <div className="grid grid-cols-2 gap-4">
        {[{ member: memberA, role: roleA, color: '#5B5BF0' }, { member: memberB, role: roleB, color: '#a78bfa' }].map(({ member, role, color }) => (
          <div key={member?.name} className="glass p-5 rounded-2xl border" style={{ borderColor: `${color}55` }}>
            <div className="flex items-center gap-3 mb-3">
              <div
                className="w-10 h-10 rounded-full flex items-center justify-center text-white font-bold text-sm flex-shrink-0"
                style={{ background: `linear-gradient(135deg, ${color}66, ${color}33)`, border: `2px solid ${color}55` }}
              >
                {member?.name?.charAt(0)?.toUpperCase() || '?'}
              </div>
              <div>
                <p className="font-semibold text-accent font-heading">{member?.name}</p>
                <span
                  className="px-2 py-0.5 rounded-full text-xs font-semibold"
                  style={{ color: role.color, background: role.bg, border: `1px solid ${role.border}` }}
                >
                  {role.label}
                </span>
              </div>
            </div>
            <div className="flex justify-between text-sm">
              <div className="text-center">
                <p className="text-2xl font-bold" style={{ color }}>{(member?.overall_score ?? 0).toFixed(1)}</p>
                <p className="text-xs text-gray-500">Overall</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-accent">{messageCounts?.[member?.name] ?? '—'}</p>
                <p className="text-xs text-gray-500">Messages</p>
              </div>
              <div className="text-center">
                <p className="text-2xl font-bold text-accent">{Math.round((member?.promise_delivery_ratio ?? 0) * 100)}%</p>
                <p className="text-xs text-gray-500">Delivery</p>
              </div>
            </div>
          </div>
        ))}
      </div>

      {/* Radar chart */}
      <div className="glass p-5 rounded-2xl">
        <h3 className="font-heading font-semibold text-accent mb-4">Skill Comparison Radar</h3>
        <ResponsiveContainer width="100%" height={320}>
          <RechartsRadar data={radarData} outerRadius="70%">
            <PolarGrid stroke="#2A2550" />
            <PolarAngleAxis dataKey="axis" tick={{ fill: '#9ca3af', fontSize: 12 }} />
            <Tooltip
              contentStyle={{ background: '#13102A', border: '1px solid #2A2550', borderRadius: 8 }}
              labelStyle={{ color: '#F5F2EA' }}
            />
            <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 12 }} />
            <Radar
              name={memberA?.name}
              dataKey={memberA?.name}
              stroke="#5B5BF0"
              fill="#5B5BF0"
              fillOpacity={0.25}
              dot={{ r: 3, fill: '#5B5BF0' }}
            />
            <Radar
              name={memberB?.name}
              dataKey={memberB?.name}
              stroke="#a78bfa"
              fill="#a78bfa"
              fillOpacity={0.25}
              dot={{ r: 3, fill: '#a78bfa' }}
            />
          </RechartsRadar>
        </ResponsiveContainer>
      </div>

      {/* Score diff table */}
      <div className="glass p-5 rounded-2xl">
        <h3 className="font-heading font-semibold text-accent mb-4">Score Breakdown</h3>
        <div className="overflow-x-auto">
          <table className="w-full text-sm">
            <thead>
              <tr className="border-b border-border">
                <th className="text-left py-2 px-3 text-gray-400 font-medium">Metric</th>
                <th className="text-center py-2 px-3 text-primary font-medium">{memberA?.name}</th>
                <th className="text-center py-2 px-3 text-purple-400 font-medium">{memberB?.name}</th>
                <th className="text-center py-2 px-3 text-gray-400 font-medium">Δ Diff</th>
              </tr>
            </thead>
            <tbody>
              {SCORE_KEYS.map(({ key, label }) => (
                <DiffRow
                  key={key}
                  label={label}
                  a={memberA?.scores?.[key]}
                  b={memberB?.scores?.[key]}
                />
              ))}
              <DiffRow
                label="Overall Score"
                a={memberA?.overall_score}
                b={memberB?.overall_score}
              />
              <DiffRow
                label="Delivery Rate (%)"
                a={(memberA?.promise_delivery_ratio ?? 0) * 100}
                b={(memberB?.promise_delivery_ratio ?? 0) * 100}
              />
            </tbody>
          </table>
        </div>
      </div>
    </div>
  )
}

import {
  Radar, RadarChart as ReRadarChart, PolarGrid, PolarAngleAxis,
  PolarRadiusAxis, ResponsiveContainer, Tooltip
} from 'recharts'

const METRICS = [
  { key: 'message_frequency', label: 'Frequency' },
  { key: 'initiative', label: 'Initiative' },
  { key: 'task_ownership', label: 'Ownership' },
  { key: 'follow_through', label: 'Follow-Through' },
  { key: 'responsiveness', label: 'Responsiveness' },
]

export default function RadarChart({ member }) {
  const scores = member?.scores || {}
  const data = METRICS.map(m => ({
    subject: m.label,
    value: scores[m.key] ?? 0,
    fullMark: 10,
  }))

  return (
    <div className="glass p-5 rounded-2xl animate-fade-in">
      <h3 className="font-heading font-semibold text-accent mb-4">Contribution Dimensions</h3>
      <ResponsiveContainer width="100%" height={280}>
        <ReRadarChart data={data}>
          <PolarGrid stroke="#2A2550" />
          <PolarAngleAxis dataKey="subject" tick={{ fill: '#9ca3af', fontSize: 12 }} />
          <PolarRadiusAxis angle={90} domain={[0, 10]} tick={false} axisLine={false} />
          <Radar
            name={member?.name}
            dataKey="value"
            stroke="#5B5BF0"
            fill="#5B5BF0"
            fillOpacity={0.3}
            strokeWidth={2}
          />
          <Tooltip
            contentStyle={{ background: '#13102A', border: '1px solid #2A2550', borderRadius: 8, color: '#F5F2EA' }}
            formatter={(v) => [v.toFixed(1), 'Score']}
          />
        </ReRadarChart>
      </ResponsiveContainer>
    </div>
  )
}

import { useMemo } from 'react'
import {
  LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip,
  Legend, ResponsiveContainer
} from 'recharts'

const COLORS = ['#5B5BF0', '#22c55e', '#eab308', '#ef4444', '#06b6d4', '#f97316', '#ec4899', '#a78bfa']

function getWeekLabel(dateStr) {
  const d = new Date(dateStr)
  const year = d.getFullYear()
  const startOfYear = new Date(year, 0, 1)
  const week = Math.ceil(((d - startOfYear) / 86400000 + startOfYear.getDay() + 1) / 7)
  return `W${week} ${year}`
}

export default function TimelineChart({ parsedData, members }) {
  const data = useMemo(() => {
    const buckets = {}
    parsedData.forEach(msg => {
      const week = getWeekLabel(msg.timestamp)
      if (!buckets[week]) buckets[week] = { week }
      buckets[week][msg.name] = (buckets[week][msg.name] || 0) + 1
    })
    return Object.values(buckets).sort((a, b) => a.week.localeCompare(b.week))
  }, [parsedData])

  const memberNames = members.map(m => m.name)

  return (
    <div className="glass p-5 rounded-2xl animate-fade-in">
      <h3 className="font-heading font-semibold text-accent mb-4">Contribution Over Time (Weekly)</h3>
      <ResponsiveContainer width="100%" height={300}>
        <LineChart data={data} margin={{ top: 5, right: 20, left: 0, bottom: 5 }}>
          <CartesianGrid strokeDasharray="3 3" stroke="#2A2550" />
          <XAxis dataKey="week" tick={{ fill: '#9ca3af', fontSize: 11 }} />
          <YAxis tick={{ fill: '#9ca3af', fontSize: 11 }} />
          <Tooltip
            contentStyle={{ background: '#13102A', border: '1px solid #2A2550', borderRadius: 8, color: '#F5F2EA' }}
          />
          <Legend wrapperStyle={{ color: '#9ca3af', fontSize: 12 }} />
          {memberNames.map((name, i) => (
            <Line
              key={name}
              type="monotone"
              dataKey={name}
              stroke={COLORS[i % COLORS.length]}
              strokeWidth={2}
              dot={false}
              activeDot={{ r: 4 }}
            />
          ))}
        </LineChart>
      </ResponsiveContainer>
    </div>
  )
}

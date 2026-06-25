import { useMemo } from 'react'

const DAYS = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
const HOURS = Array.from({ length: 24 }, (_, i) => i)

export default function ActivityHeatmap({ parsedData }) {
  const grid = useMemo(() => {
    const counts = {}
    let maxCount = 0
    parsedData.forEach(msg => {
      const d = new Date(msg.timestamp)
      const day = d.getDay()
      const hour = d.getHours()
      const key = `${day}-${hour}`
      counts[key] = (counts[key] || 0) + 1
      if (counts[key] > maxCount) maxCount = counts[key]
    })
    return { counts, maxCount }
  }, [parsedData])

  const getColor = (day, hour) => {
    const count = grid.counts[`${day}-${hour}`] || 0
    if (count === 0) return 'rgba(42,37,80,0.4)'
    const intensity = count / Math.max(grid.maxCount, 1)
    const alpha = 0.2 + intensity * 0.8
    return `rgba(91, 91, 240, ${alpha})`
  }

  const getTitle = (day, hour) => {
    const count = grid.counts[`${day}-${hour}`] || 0
    return `${DAYS[day]} ${hour}:00 — ${count} messages`
  }

  return (
    <div className="glass p-5 rounded-2xl animate-fade-in overflow-x-auto">
      <h3 className="font-heading font-semibold text-accent mb-4">Activity Heatmap (Day × Hour)</h3>

      <div className="min-w-[600px]">
        {/* Hour labels */}
        <div className="flex mb-1 ml-10">
          {HOURS.filter(h => h % 3 === 0).map(h => (
            <div key={h} className="text-gray-500 text-xs" style={{ width: `${(3 / 24) * 100}%`, textAlign: 'center' }}>
              {h}:00
            </div>
          ))}
        </div>

        {/* Grid rows */}
        {DAYS.map((day, di) => (
          <div key={day} className="flex items-center mb-1">
            <span className="text-gray-500 text-xs w-10 flex-shrink-0">{day}</span>
            <div className="flex gap-0.5 flex-1">
              {HOURS.map(h => (
                <div
                  key={h}
                  title={getTitle(di, h)}
                  className="flex-1 h-6 rounded-sm cursor-pointer hover:ring-1 hover:ring-primary/60 transition-all"
                  style={{ background: getColor(di, h) }}
                />
              ))}
            </div>
          </div>
        ))}

        {/* Legend */}
        <div className="flex items-center gap-2 mt-3 justify-end">
          <span className="text-xs text-gray-500">Less</span>
          {[0.1, 0.3, 0.5, 0.7, 0.9].map(i => (
            <div key={i} className="w-4 h-4 rounded-sm" style={{ background: `rgba(91,91,240,${0.2 + i * 0.8})` }} />
          ))}
          <span className="text-xs text-gray-500">More</span>
        </div>
      </div>
    </div>
  )
}

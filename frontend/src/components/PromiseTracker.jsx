import { CheckCircle, Clock } from 'lucide-react'

export default function PromiseTracker({ member }) {
  const promises = member?.promises || []
  const deliveries = member?.deliveries || []
  const ratio = member?.promise_delivery_ratio ?? 0

  return (
    <div className="glass p-5 rounded-2xl animate-fade-in">
      <div className="flex items-center justify-between mb-4">
        <h3 className="font-heading font-semibold text-accent">Promise vs Delivery</h3>
        <span className={`px-3 py-1 rounded-full text-xs font-bold ${ratio >= 0.7 ? 'badge-green' : ratio >= 0.4 ? 'badge-yellow' : 'badge-red'}`}>
          {Math.round(ratio * 100)}% delivery rate
        </span>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Promises */}
        <div>
          <div className="flex items-center gap-2 mb-2 text-warning text-sm font-semibold">
            <Clock className="w-4 h-4" />
            Promises ({promises.length})
          </div>
          <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {promises.length > 0 ? promises.map((p, i) => (
              <div key={i} className="text-xs text-gray-300 bg-surface p-2 rounded-lg border border-border">
                {p}
              </div>
            )) : (
              <p className="text-xs text-gray-500 italic">No promises found</p>
            )}
          </div>
        </div>

        {/* Deliveries */}
        <div>
          <div className="flex items-center gap-2 mb-2 text-success text-sm font-semibold">
            <CheckCircle className="w-4 h-4" />
            Deliveries ({deliveries.length})
          </div>
          <div className="space-y-2 max-h-48 overflow-y-auto pr-1">
            {deliveries.length > 0 ? deliveries.map((d, i) => (
              <div key={i} className="text-xs text-gray-300 bg-surface p-2 rounded-lg border border-border">
                {d}
              </div>
            )) : (
              <p className="text-xs text-gray-500 italic">No deliveries recorded</p>
            )}
          </div>
        </div>
      </div>
    </div>
  )
}

// src/components/OutcomeBar.jsx
// Segmented strip showing how test cases split across outcomes.
export const OUTCOME_COLORS = {
    passed: '#5ec28f',
    failed: '#ee6b6e',
    other: '#e3b04b',
    not_run: '#4a5668',
}

export default function OutcomeBar({ segments }) {
    const total = segments.reduce((sum, s) => sum + s.value, 0)
    if (total === 0) return null

    return (
        <div>
            <div
                className="flex h-2.5 gap-0.5 overflow-hidden rounded-full"
                role="img"
                aria-label={segments.map((s) => `${s.label}: ${s.value}`).join(', ')}
            >
                {segments
                    .filter((s) => s.value > 0)
                    .map((s) => (
                        <div
                            key={s.label}
                            title={`${s.label}: ${s.value}`}
                            style={{ width: `${(s.value / total) * 100}%`, background: s.color }}
                            className="min-w-[3px] transition-[width] duration-500"
                        />
                    ))}
            </div>
            <ul className="mt-3 flex flex-wrap gap-x-5 gap-y-1.5 text-xs">
                {segments.map((s) => (
                    <li key={s.label} className="flex items-center gap-1.5 muted">
                        <span className="h-2 w-2 rounded-sm" style={{ background: s.color }} />
                        {s.label}
                        <span className="font-medium text-[color:var(--text)]">{s.value}</span>
                    </li>
                ))}
            </ul>
        </div>
    )
}
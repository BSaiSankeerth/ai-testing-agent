import { useCallback, useEffect, useState } from 'react'
import { errorMessage, getStats, listSessions } from '../api'
import { Link } from 'react-router-dom'
import OutcomeBar, { OUTCOME_COLORS } from '../components/OutcomeBar.jsx'

const TONE = {
    completed: 'tone-green',
    completed_with_gaps: 'tone-amber',
    running: 'tone-blue live',
    pending: 'tone-slate',
    failed: 'tone-red',
}

function useCountUp(target, ms = 700) {
    const [n, setN] = useState(0)
    useEffect(() => {
        const to = Number(target) || 0
        let raf
        let start
        const tick = (t) => {
            start = start ?? t
            const p = Math.min((t - start) / ms, 1)
            setN(Math.round(to * (1 - Math.pow(1 - p, 3))))
            if (p < 1) raf = requestAnimationFrame(tick)
        }
        raf = requestAnimationFrame(tick)
        return () => cancelAnimationFrame(raf)
    }, [target, ms])
    return n
}

function Figure({ label, value, color = 'var(--text)', delay = 0 }) {
    const n = useCountUp(value)
    return (
        <div className="settle bg-[var(--surface)] px-5 py-4" style={{ animationDelay: `${delay}ms` }}>
            <div className="text-[13px] muted">{label}</div>
            <div className="mt-1.5 text-3xl font-semibold tabular-nums" style={{ color }}>
                {n}
            </div>
        </div>
    )
}

function formatDate(value) {
    return value ? new Date(value).toLocaleString() : '-'
}

export default function Dashboard() {
    const [stats, setStats] = useState(null)
    const [sessions, setSessions] = useState([])
    const [error, setError] = useState(null)
    const [loading, setLoading] = useState(true)

    const load = useCallback(() => {
        setLoading(true)
        Promise.all([getStats(), listSessions()])
            .then(([s, list]) => {
                setStats(s)
                setSessions(list)
                setError(null)
            })
            .catch((err) => setError(errorMessage(err)))
            .finally(() => setLoading(false))
    }, [])

    useEffect(() => {
        load()
    }, [load])

    const other = stats ? stats.inconclusive + stats.blocked + stats.error : 0
    const total = stats ? stats.passed + stats.failed + other + stats.not_run : 0
    const passRate = total ? Math.round((stats.passed / total) * 100) : 0

    return (
        <div>
            <div className="mb-8 flex items-end justify-between gap-4">
                <div>
                    <h1 className="text-2xl font-semibold">Dashboard</h1>
                    <p className="mt-1 text-sm muted">Results across every testing session.</p>
                </div>
                <button onClick={load} disabled={loading} className="btn btn-ghost btn-sm">
                    <svg
                        viewBox="0 0 24 24"
                        className={`h-4 w-4 ${loading ? 'animate-spin' : ''}`}
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="2"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    >
                        <path d="M21 12a9 9 0 1 1-3-6.7" />
                        <path d="M21 3v6h-6" />
                    </svg>
                    {loading ? 'Refreshing' : 'Refresh'}
                </button>
            </div>

            {error && <div className="alert-error mb-6">{error}</div>}

            {stats && (
                <section className="panel mb-8 overflow-hidden">
                    <div className="grid grid-cols-2 gap-px bg-[var(--line)] md:grid-cols-3 lg:grid-cols-6">
                        <Figure label="Sessions" value={stats.sessions} delay={0} />
                        <Figure label="Test cases" value={stats.test_cases} delay={50} />
                        <Figure label="Passed" value={stats.passed} color="#5ec28f" delay={100} />
                        <Figure label="Failed" value={stats.failed} color="#ee6b6e" delay={150} />
                        <Figure label="Inconclusive / blocked / error" value={other} color="#e3b04b" delay={200} />
                        <Figure label="Not run" value={stats.not_run} color="var(--muted)" delay={250} />
                    </div>

                    {total > 0 && (
                        <div className="border-t px-5 py-4 hairline">
                            <div className="mb-3 flex items-baseline justify-between">
                                <span className="text-sm muted">Overall outcome</span>
                                <span className="text-sm">
                                    <span className="font-semibold tabular-nums">{passRate}%</span>{' '}
                                    <span className="muted">of test cases passed</span>
                                </span>
                            </div>
                            <OutcomeBar
                                segments={[
                                    { label: 'Passed', value: stats.passed, color: OUTCOME_COLORS.passed },
                                    { label: 'Failed', value: stats.failed, color: OUTCOME_COLORS.failed },
                                    { label: 'Inconclusive / blocked / error', value: other, color: OUTCOME_COLORS.other },
                                    { label: 'Not run', value: stats.not_run, color: OUTCOME_COLORS.not_run },
                                ]}
                            />
                        </div>
                    )}
                </section>
            )}

            <h2 className="mb-3 text-lg font-semibold">Recent testing activity</h2>
            <div className="panel overflow-x-auto">
                <table className="w-full text-left text-sm">
                    <thead>
                        <tr className="border-b text-[13px] muted hairline">
                            <th className="px-4 py-3 font-medium">ID</th>
                            <th className="px-4 py-3 font-medium">Target</th>
                            <th className="px-4 py-3 font-medium">Status</th>
                            <th className="px-4 py-3 font-medium">Started</th>
                            <th className="px-4 py-3 font-medium">Completed</th>
                        </tr>
                    </thead>
                    <tbody>
                        {loading &&
                            sessions.length === 0 &&
                            [0, 1, 2].map((i) => (
                                <tr key={i} className="border-b hairline">
                                    {[0, 1, 2, 3, 4].map((j) => (
                                        <td key={j} className="px-4 py-3.5">
                                            <div className="skeleton h-4 w-24" />
                                        </td>
                                    ))}
                                </tr>
                            ))}
                        {sessions.length === 0 && !loading && (
                            <tr>
                                <td colSpan="5" className="px-4 py-12 text-center">
                                    <div className="font-medium">No sessions yet</div>
                                    <div className="mt-1 text-sm muted">
                                        Start a testing session and its results will show up here.
                                    </div>
                                </td>
                            </tr>
                        )}
                        {sessions.map((s) => (
                            <tr
                                key={s.id}
                                className="border-b transition-colors last:border-0 hairline hover:bg-[var(--raised)]"
                            >
                                <td className="px-4 py-3 mono font-medium">
                                    <Link to={`/sessions/${s.id}`} className="link">
                                        #{s.id}
                                    </Link>
                                </td>
                                <td className="max-w-[18rem] truncate px-4 py-3 mono text-[13px] muted" title={s.target_url}>
                                    {s.target_url}
                                </td>
                                <td className="px-4 py-3">
                                    <span className={`badge ${TONE[s.status] || 'tone-slate'}`}>
                                        {s.status.replaceAll('_', ' ')}
                                    </span>
                                </td>
                                <td className="whitespace-nowrap px-4 py-3 muted">{formatDate(s.started_at)}</td>
                                <td className="whitespace-nowrap px-4 py-3 muted">{formatDate(s.completed_at)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
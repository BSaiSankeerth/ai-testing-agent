import { useCallback, useEffect, useState } from 'react'
import { errorMessage, getStats, listSessions } from '../api'

const BADGE = {
    completed: 'bg-green-100 text-green-800',
    completed_with_gaps: 'bg-amber-100 text-amber-800',
    running: 'bg-blue-100 text-blue-800',
    pending: 'bg-slate-100 text-slate-700',
    failed: 'bg-red-100 text-red-800',
}

function Card({ label, value, tone = 'text-slate-900' }) {
    return (
        <div className="rounded-lg border bg-white p-4 shadow-sm">
            <div className="text-sm text-slate-500">{label}</div>
            <div className={`mt-1 text-3xl font-semibold ${tone}`}>{value}</div>
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

    return (
        <div>
            <div className="mb-6 flex items-center justify-between">
                <h1 className="text-2xl font-bold">Dashboard</h1>
                <button
                    onClick={load}
                    className="rounded-md border bg-white px-3 py-1.5 text-sm hover:bg-slate-100"
                >
                    {loading ? 'Loading...' : 'Refresh'}
                </button>
            </div>

            {error && (
                <div className="mb-6 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                    {error}
                </div>
            )}

            {stats && (
                <div className="mb-8 grid grid-cols-2 gap-4 md:grid-cols-3 lg:grid-cols-6">
                    <Card label="Sessions" value={stats.sessions} />
                    <Card label="Test cases" value={stats.test_cases} />
                    <Card label="Passed" value={stats.passed} tone="text-green-600" />
                    <Card label="Failed" value={stats.failed} tone="text-red-600" />
                    <Card
                        label="Inconclusive / blocked / error"
                        value={stats.inconclusive + stats.blocked + stats.error}
                        tone="text-amber-600"
                    />
                    <Card label="Not run" value={stats.not_run} tone="text-slate-500" />
                </div>
            )}

            <h2 className="mb-3 text-lg font-semibold">Recent testing activity</h2>
            <div className="overflow-x-auto rounded-lg border bg-white shadow-sm">
                <table className="w-full text-left text-sm">
                    <thead className="border-b bg-slate-50 text-slate-500">
                        <tr>
                            <th className="px-4 py-2">ID</th>
                            <th className="px-4 py-2">Target</th>
                            <th className="px-4 py-2">Status</th>
                            <th className="px-4 py-2">Started</th>
                            <th className="px-4 py-2">Completed</th>
                        </tr>
                    </thead>
                    <tbody>
                        {sessions.length === 0 && !loading && (
                            <tr>
                                <td colSpan="5" className="px-4 py-6 text-center text-slate-500">
                                    No sessions yet.
                                </td>
                            </tr>
                        )}
                        {sessions.map((s) => (
                            <tr key={s.id} className="border-b last:border-0">
                                <td className="px-4 py-2 font-medium">#{s.id}</td>
                                <td className="px-4 py-2">{s.target_url}</td>
                                <td className="px-4 py-2">
                                    <span
                                        className={`rounded-full px-2 py-0.5 text-xs font-medium ${BADGE[s.status] || 'bg-slate-100 text-slate-700'
                                            }`}
                                    >
                                        {s.status}
                                    </span>
                                </td>
                                <td className="px-4 py-2">{formatDate(s.started_at)}</td>
                                <td className="px-4 py-2">{formatDate(s.completed_at)}</td>
                            </tr>
                        ))}
                    </tbody>
                </table>
            </div>
        </div>
    )
}
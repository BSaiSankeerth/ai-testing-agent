import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { errorMessage, getSession } from '../api'
import EvidencePanel from '../components/EvidencePanel'

const BADGE = {
    completed: 'bg-green-100 text-green-800',
    completed_with_gaps: 'bg-amber-100 text-amber-800',
    running: 'bg-blue-100 text-blue-800',
    pending: 'bg-slate-100 text-slate-700',
    failed: 'bg-red-100 text-red-800',
    passed: 'bg-green-100 text-green-800',
    inconclusive: 'bg-amber-100 text-amber-800',
    blocked: 'bg-amber-100 text-amber-800',
    error: 'bg-orange-100 text-orange-800',
    not_run: 'bg-slate-100 text-slate-600',
}

const SEVERITY = {
    critical: 'bg-red-600 text-white',
    high: 'bg-red-100 text-red-800',
    medium: 'bg-amber-100 text-amber-800',
    low: 'bg-slate-100 text-slate-700',
}

function Badge({ text, map = BADGE }) {
    return (
        <span
            className={`rounded-full px-2 py-0.5 text-xs font-medium ${map[text] || 'bg-slate-100 text-slate-700'
                }`}
        >
            {text}
        </span>
    )
}

const formatDate = (v) => (v ? new Date(v).toLocaleString() : '-')

export default function SessionDetail() {
    const { id } = useParams()
    const [session, setSession] = useState(null)
    const [error, setError] = useState(null)
    const [openResult, setOpenResult] = useState(null)

    useEffect(() => {
        let timer = null
        let cancelled = false

        const load = () => {
            getSession(id)
                .then((data) => {
                    if (cancelled) return
                    setSession(data)
                    setError(null)
                    if (data.status === 'pending' || data.status === 'running') {
                        timer = setTimeout(load, 3000)
                    }
                })
                .catch((err) => {
                    if (!cancelled) setError(errorMessage(err))
                })
        }

        load()
        return () => {
            cancelled = true
            if (timer) clearTimeout(timer)
        }
    }, [id])

    if (error) {
        return (
            <div className="rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                {error}
            </div>
        )
    }
    if (!session) return <p className="text-slate-500">Loading...</p>

    const results = session.test_cases.flatMap((c) => c.results)
    const count = (s) => results.filter((r) => r.status === s).length
    const bugs = session.test_cases.flatMap((c) =>
        c.results.flatMap((r) => r.bug_reports.map((b) => ({ ...b, caseTitle: c.title }))),
    )
    const active = session.status === 'pending' || session.status === 'running'

    return (
        <div>
            <Link to="/" className="text-sm text-blue-600 hover:underline">
                &larr; Dashboard
            </Link>

            <div className="mb-6 mt-2 flex flex-wrap items-center gap-3">
                <h1 className="text-2xl font-bold">Session #{session.id}</h1>
                <Badge text={session.status} />
            </div>

            <div className="mb-6 rounded-lg border bg-white p-4 text-sm shadow-sm">
                <div><span className="text-slate-500">Target:</span> {session.target_url}</div>
                <div className="mt-1"><span className="text-slate-500">Instructions:</span> {session.instructions}</div>
                <div className="mt-1 text-slate-500">
                    Started {formatDate(session.started_at)} &middot; Completed {formatDate(session.completed_at)}
                </div>
            </div>

            {active && (
                <div className="mb-6 rounded-md border border-blue-200 bg-blue-50 p-3 text-sm text-blue-800">
                    Testing in progress. Planning, exploring, generating and running test cases. This page
                    refreshes automatically; results appear when the run finishes.
                </div>
            )}

            {session.status === 'failed' && session.test_cases.length === 0 && (
                <div className="mb-6 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                    The run failed before any test cases were saved. Check the backend terminal for the reason.
                </div>
            )}

            {session.test_cases.length > 0 && (
                <>
                    <div className="mb-8 grid grid-cols-2 gap-3 md:grid-cols-6">
                        {[
                            ['Total', results.length],
                            ['Passed', count('passed')],
                            ['Failed', count('failed')],
                            ['Inconclusive', count('inconclusive')],
                            ['Blocked / error', count('blocked') + count('error')],
                            ['Not run', count('not_run')],
                        ].map(([label, value]) => (
                            <div key={label} className="rounded-lg border bg-white p-3 shadow-sm">
                                <div className="text-xs text-slate-500">{label}</div>
                                <div className="text-2xl font-semibold">{value}</div>
                            </div>
                        ))}
                    </div>

                    <h2 className="mb-3 text-lg font-semibold">Test cases</h2>
                    <div className="mb-8 space-y-3">
                        {session.test_cases.map((c) => {
                            const r = c.results[0]
                            return (
                                <div key={c.id} className="rounded-lg border bg-white p-4 shadow-sm">
                                    <div className="flex flex-wrap items-center gap-2">
                                        <span className="font-medium">{c.title}</span>
                                        {r && <Badge text={r.status} />}
                                        <span className="text-xs text-slate-500">
                                            {c.category} &middot; {c.priority}
                                            {r?.duration_ms != null && ` · ${r.duration_ms} ms`}
                                        </span>
                                    </div>
                                    <div className="mt-2 text-sm text-slate-600">
                                        <span className="text-slate-500">Expected:</span> {c.expected_result}
                                    </div>
                                    {r?.actual_result && (
                                        <div className="mt-1 text-sm text-slate-600">
                                            <span className="text-slate-500">Analysis:</span> {r.actual_result}
                                        </div>
                                    )}
                                    {r?.error_details && (
                                        <div className="mt-1 text-sm text-amber-700">
                                            <span className="text-slate-500">Details:</span> {r.error_details}
                                        </div>
                                    )}
                                    {r && c.steps.length > 0 && (
                                        <button
                                            onClick={() => setOpenResult(openResult === r.id ? null : r.id)}
                                            className="mt-2 text-sm text-blue-600 hover:underline"
                                        >
                                            {openResult === r.id ? 'Hide evidence' : 'View evidence'}
                                        </button>
                                    )}
                                    {r && openResult === r.id && <EvidencePanel resultId={r.id} />}
                                </div>
                            )
                        })}
                    </div>

                    <h2 className="mb-3 text-lg font-semibold">Bug reports ({bugs.length})</h2>
                    {bugs.length === 0 ? (
                        <p className="text-sm text-slate-500">No defects were reported in this session.</p>
                    ) : (
                        <div className="space-y-3">
                            {bugs.map((b) => (
                                <div key={b.id} className="rounded-lg border border-red-200 bg-white p-4 shadow-sm">
                                    <div className="flex flex-wrap items-center gap-2">
                                        <span className="font-medium">{b.title}</span>
                                        <Badge text={b.severity} map={SEVERITY} />
                                        <span className="text-xs text-slate-500">priority: {b.priority}</span>
                                    </div>
                                    <div className="mt-1 text-xs text-slate-500">Related test: {b.caseTitle}</div>
                                    <p className="mt-2 text-sm">{b.description}</p>
                                    <div className="mt-2 text-sm font-medium">Steps to reproduce</div>
                                    <ol className="list-decimal pl-5 text-sm text-slate-700">
                                        {b.steps_to_reproduce.map((s, i) => (
                                            <li key={i}>{s}</li>
                                        ))}
                                    </ol>
                                    <div className="mt-2 text-sm"><span className="text-slate-500">Expected:</span> {b.expected_result}</div>
                                    <div className="text-sm"><span className="text-slate-500">Actual:</span> {b.actual_result}</div>
                                </div>
                            ))}
                        </div>
                    )}
                </>
            )}
        </div>
    )
}
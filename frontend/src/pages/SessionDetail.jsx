import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { errorMessage, getSession } from '../api'
import EvidencePanel from '../components/EvidencePanel'
import OutcomeBar, { OUTCOME_COLORS } from '../components/OutcomeBar.jsx'

const TONE = {
    completed: 'tone-green',
    completed_with_gaps: 'tone-amber',
    running: 'tone-blue live',
    pending: 'tone-slate',
    failed: 'tone-red',
    passed: 'tone-green',
    inconclusive: 'tone-amber',
    blocked: 'tone-amber',
    error: 'tone-orange',
    not_run: 'tone-slate',
}

const SEVERITY = {
    critical: 'tone-crit',
    high: 'tone-red',
    medium: 'tone-amber',
    low: 'tone-slate',
}

const EDGE = {
    passed: '#5ec28f',
    failed: '#ee6b6e',
    inconclusive: '#e3b04b',
    blocked: '#e3b04b',
    error: '#e88c5a',
    not_run: '#4a5668',
}

const STAGES = ['planning', 'exploring', 'generating', 'executing', 'reporting']

function Badge({ text, map = TONE }) {
    return <span className={`badge ${map[text] || 'tone-slate'}`}>{text.replaceAll('_', ' ')}</span>
}

const formatDate = (v) => (v ? new Date(v).toLocaleString() : '-')

function Row({ label, children, tone }) {
    return (
        <div className="grid grid-cols-[5.5rem_1fr] gap-3 text-sm">
            <dt className="muted">{label}</dt>
            <dd className={tone || ''}>{children}</dd>
        </div>
    )
}

function Stepper({ stage }) {
    const current = STAGES.indexOf(stage)
    return (
        <ol className="flex items-center">
            {STAGES.map((st, i) => {
                const done = i < current
                const now = i === current
                return (
                    <li key={st} className="flex flex-1 items-center gap-2 last:flex-none">
                        <span
                            className={`grid h-6 w-6 shrink-0 place-items-center rounded-full border text-[11px] font-semibold ${done
                                ? 'border-transparent bg-[var(--accent)] text-[var(--accent-ink)]'
                                : now
                                    ? 'border-[var(--accent)] bg-[rgba(121,184,217,0.15)] text-[var(--accent)]'
                                    : 'border-[var(--line-strong)] faint'
                                }`}
                        >
                            {done ? (
                                <svg viewBox="0 0 24 24" className="h-3.5 w-3.5" fill="none" stroke="currentColor" strokeWidth="3.5" strokeLinecap="round" strokeLinejoin="round">
                                    <path d="M5 12.5l4.5 4.5L19 7.5" />
                                </svg>
                            ) : now ? (
                                <span className="badge live tone-blue !border-0 !bg-transparent !p-0 before:!h-1.5 before:!w-1.5" />
                            ) : (
                                i + 1
                            )}
                        </span>
                        <span className={`text-xs ${now ? 'font-medium' : 'muted'} ${now ? '' : 'hidden sm:inline'}`}>
                            {st}
                        </span>
                        {i < STAGES.length - 1 && (
                            <span className={`mx-1 h-px flex-1 ${done ? 'bg-[var(--accent)]' : 'bg-[var(--line-strong)]'}`} />
                        )}
                    </li>
                )
            })}
        </ol>
    )
}

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

    if (error) return <div className="alert-error">{error}</div>
    if (!session) {
        return (
            <div className="space-y-4">
                <div className="skeleton h-7 w-48" />
                <div className="skeleton h-28 w-full" />
            </div>
        )
    }

    const results = session.test_cases.flatMap((c) => c.results)
    const count = (s) => results.filter((r) => r.status === s).length
    const bugs = session.test_cases.flatMap((c) =>
        c.results.flatMap((r) => r.bug_reports.map((b) => ({ ...b, caseTitle: c.title }))),
    )
    const active = session.status === 'pending' || session.status === 'running'
    const otherCount = count('inconclusive') + count('blocked') + count('error')

    return (
        <div>
            <Link to="/" className="inline-flex items-center gap-1 text-sm muted hover:text-[color:var(--text)]">
                <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                    <path d="M15 6l-6 6 6 6" />
                </svg>
                Dashboard
            </Link>

            <div className="mb-6 mt-3 flex flex-wrap items-center gap-3">
                <h1 className="text-2xl font-semibold">
                    Session <span className="mono text-[0.9em] muted">#{session.id}</span>
                </h1>
                <Badge text={session.status} />
            </div>

            <dl className="panel mb-6 space-y-2.5 p-5">
                <Row label="Target">
                    <span className="mono text-[13px]">{session.target_url}</span>
                </Row>
                <Row label="Instructions">{session.instructions}</Row>
                <Row label="Started">{formatDate(session.started_at)}</Row>
                <Row label="Completed">{formatDate(session.completed_at)}</Row>
            </dl>

            {active && (
                <section className="panel mb-6 border-[rgba(121,184,217,0.35)] p-5">
                    <Stepper stage={session.progress?.stage} />

                    <div className="mt-5 text-sm">
                        {session.progress?.current_case ? (
                            <div>
                                <span className="muted">
                                    Running test case {session.progress.case_index} of {session.progress.case_total}
                                </span>
                                <div className="mt-0.5 font-medium">{session.progress.current_case}</div>
                            </div>
                        ) : (
                            <div className="muted">
                                {session.progress?.stage === 'exploring' && session.progress?.pages_explored
                                    ? `Explored ${session.progress.pages_explored} pages.`
                                    : 'Working...'}
                            </div>
                        )}
                    </div>

                    {session.progress?.finished?.length > 0 && (
                        <ul className="mt-4 space-y-2 border-t pt-4 text-sm hairline">
                            {session.progress.finished.map((f, i) => (
                                <li key={i} className="flex items-center gap-3">
                                    <Badge text={f.verdict} />
                                    <span>{f.title}</span>
                                </li>
                            ))}
                        </ul>
                    )}
                </section>
            )}

            {session.status === 'failed' && session.test_cases.length === 0 && (
                <div className="alert-error mb-6">
                    The run failed before any test cases were saved. Check the backend terminal for the reason.
                </div>
            )}

            {session.test_cases.length > 0 && (
                <>
                    <section className="panel mb-8 overflow-hidden">
                        <div className="grid grid-cols-2 gap-px bg-[var(--line)] md:grid-cols-6">
                            {[
                                ['Total', results.length, 'var(--text)'],
                                ['Passed', count('passed'), '#5ec28f'],
                                ['Failed', count('failed'), '#ee6b6e'],
                                ['Inconclusive', count('inconclusive'), '#e3b04b'],
                                ['Blocked / error', count('blocked') + count('error'), '#e88c5a'],
                                ['Not run', count('not_run'), 'var(--muted)'],
                            ].map(([label, value, color]) => (
                                <div key={label} className="bg-[var(--surface)] px-4 py-3">
                                    <div className="text-xs muted">{label}</div>
                                    <div className="mt-0.5 text-2xl font-semibold tabular-nums" style={{ color }}>
                                        {value}
                                    </div>
                                </div>
                            ))}
                        </div>
                        <div className="border-t px-4 py-4 hairline">
                            <OutcomeBar
                                segments={[
                                    { label: 'Passed', value: count('passed'), color: OUTCOME_COLORS.passed },
                                    { label: 'Failed', value: count('failed'), color: OUTCOME_COLORS.failed },
                                    { label: 'Inconclusive / blocked / error', value: otherCount, color: OUTCOME_COLORS.other },
                                    { label: 'Not run', value: count('not_run'), color: OUTCOME_COLORS.not_run },
                                ]}
                            />
                        </div>
                    </section>

                    <h2 className="mb-3 text-lg font-semibold">Test cases</h2>
                    <div className="mb-10 space-y-3">
                        {session.test_cases.map((c) => {
                            const r = c.results[0]
                            return (
                                <article key={c.id} className="panel relative p-4 pl-5">
                                    <span
                                        className="absolute inset-y-3 left-0 w-[3px] rounded-r"
                                        style={{ background: EDGE[r?.status] || EDGE.not_run }}
                                    />
                                    <div className="flex flex-wrap items-center gap-2">
                                        <h3 className="font-medium">{c.title}</h3>
                                        {r && <Badge text={r.status} />}
                                        <span className="chip">{c.category}</span>
                                        <span className="chip">{c.priority}</span>
                                        {r?.duration_ms != null && (
                                            <span className="mono text-xs faint">{r.duration_ms} ms</span>
                                        )}
                                    </div>

                                    <dl className="mt-3 space-y-1.5">
                                        <Row label="Expected">{c.expected_result}</Row>
                                        {r?.actual_result && <Row label="Analysis">{r.actual_result}</Row>}
                                        {r?.error_details && (
                                            <Row label="Details" tone="text-[#e3b04b]">
                                                {r.error_details}
                                            </Row>
                                        )}
                                    </dl>

                                    {r && c.steps.length > 0 && (
                                        <button
                                            onClick={() => setOpenResult(openResult === r.id ? null : r.id)}
                                            aria-expanded={openResult === r.id}
                                            className="btn btn-ghost btn-sm mt-3"
                                        >
                                            <svg
                                                viewBox="0 0 24 24"
                                                className={`h-3.5 w-3.5 transition-transform ${openResult === r.id ? 'rotate-90' : ''}`}
                                                fill="none"
                                                stroke="currentColor"
                                                strokeWidth="2.5"
                                                strokeLinecap="round"
                                                strokeLinejoin="round"
                                            >
                                                <path d="M9 6l6 6-6 6" />
                                            </svg>
                                            {openResult === r.id ? 'Hide evidence' : 'View evidence'}
                                        </button>
                                    )}
                                    {r && openResult === r.id && (
                                        <div className="mt-3">
                                            <EvidencePanel resultId={r.id} />
                                        </div>
                                    )}
                                </article>
                            )
                        })}
                    </div>

                    <h2 className="mb-3 text-lg font-semibold">
                        Bug reports <span className="muted">({bugs.length})</span>
                    </h2>
                    {bugs.length === 0 ? (
                        <p className="text-sm muted">No defects were reported in this session.</p>
                    ) : (
                        <div className="space-y-3">
                            {bugs.map((b) => (
                                <article key={b.id} className="panel border-[rgba(238,107,110,0.3)] p-5">
                                    <div className="flex flex-wrap items-center gap-2">
                                        <h3 className="font-medium">{b.title}</h3>
                                        <Badge text={b.severity} map={SEVERITY} />
                                        <span className="chip">priority: {b.priority}</span>
                                    </div>
                                    <div className="mt-1 text-xs muted">Related test: {b.caseTitle}</div>
                                    <p className="mt-3 text-sm leading-relaxed">{b.description}</p>

                                    <div className="mt-4 text-sm font-medium">Steps to reproduce</div>
                                    <ol className="mt-2 space-y-1.5 text-sm">
                                        {b.steps_to_reproduce.map((s, i) => (
                                            <li key={i} className="grid grid-cols-[1.5rem_1fr] gap-2">
                                                <span className="mono text-xs faint pt-0.5">{i + 1}.</span>
                                                <span className="text-[color:var(--text)]">{s}</span>
                                            </li>
                                        ))}
                                    </ol>

                                    <div className="mt-4 grid gap-3 text-sm md:grid-cols-2">
                                        <div className="rounded-lg border border-[rgba(94,194,143,0.25)] bg-[rgba(94,194,143,0.06)] p-3">
                                            <div className="mb-1 text-xs text-[#5ec28f]">Expected</div>
                                            {b.expected_result}
                                        </div>
                                        <div className="rounded-lg border border-[rgba(238,107,110,0.28)] bg-[rgba(238,107,110,0.07)] p-3">
                                            <div className="mb-1 text-xs text-[#ee6b6e]">Actual</div>
                                            {b.actual_result}
                                        </div>
                                    </div>
                                </article>
                            ))}
                        </div>
                    )}
                </>
            )}
        </div>
    )
}
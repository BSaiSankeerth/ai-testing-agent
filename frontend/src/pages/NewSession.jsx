import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createSession, errorMessage } from '../api'

const EXAMPLE =
    'Test the registration and login functionality. Verify valid registration, duplicate email registration, invalid email, empty fields, successful login, and incorrect password.'

const MAX = 2000
const MIN = 10

export default function NewSession() {
    const navigate = useNavigate()
    const [targetUrl, setTargetUrl] = useState('http://localhost:3000')
    const [instructions, setInstructions] = useState('')
    const [submitting, setSubmitting] = useState(false)
    const [error, setError] = useState(null)

    const length = instructions.trim().length
    const tooShort = length < MIN
    const nearLimit = length > MAX * 0.9
    const fill = Math.min(length / MAX, 1) * 100

    const submit = (e) => {
        e.preventDefault()
        setSubmitting(true)
        setError(null)
        createSession(targetUrl.trim(), instructions.trim())
            .then((session) => navigate(`/sessions/${session.id}`))
            .catch((err) => setError(errorMessage(err)))
            .finally(() => setSubmitting(false))
    }

    const onKeyDown = (e) => {
        if ((e.metaKey || e.ctrlKey) && e.key === 'Enter' && !tooShort && !submitting) {
            e.currentTarget.form.requestSubmit()
        }
    }

    return (
        <div className="max-w-2xl">
            <h1 className="text-2xl font-semibold">Create testing session</h1>
            <p className="mb-6 mt-1 text-sm muted">Point the agent at a site and tell it what to check.</p>

            {error && <div className="alert-error mb-4">{error}</div>}

            <form onSubmit={submit} className="panel space-y-6 p-6">
                <div>
                    <label htmlFor="url" className="label">Target website URL</label>
                    <div className="relative">
                        <svg
                            viewBox="0 0 24 24"
                            className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 faint"
                            fill="none"
                            stroke="currentColor"
                            strokeWidth="1.8"
                            strokeLinecap="round"
                            strokeLinejoin="round"
                        >
                            <circle cx="12" cy="12" r="9" />
                            <path d="M3 12h18M12 3c2.8 3 2.8 15 0 18M12 3c-2.8 3-2.8 15 0 18" />
                        </svg>
                        <input
                            id="url"
                            type="url"
                            required
                            value={targetUrl}
                            onChange={(e) => setTargetUrl(e.target.value)}
                            className="field mono pl-9 text-[13px]"
                        />
                    </div>
                    <p className="mt-1.5 text-xs faint">
                        Only approved targets are accepted. The server rejects anything else.
                    </p>
                </div>

                <div>
                    <div className="mb-1.5 flex items-center justify-between">
                        <label htmlFor="instructions" className="label !mb-0">Testing instructions</label>
                        <button type="button" onClick={() => setInstructions(EXAMPLE)} className="link text-xs">
                            Use example
                        </button>
                    </div>
                    <textarea
                        id="instructions"
                        rows="7"
                        maxLength={MAX}
                        value={instructions}
                        onChange={(e) => setInstructions(e.target.value)}
                        onKeyDown={onKeyDown}
                        placeholder="Describe what to test in plain language..."
                        className="field resize-y leading-relaxed"
                    />
                    <div className="mt-2 h-0.5 overflow-hidden rounded-full bg-[var(--line)]">
                        <div
                            className="h-full transition-[width] duration-200"
                            style={{
                                width: `${fill}%`,
                                background: nearLimit ? '#e3b04b' : tooShort ? 'var(--faint)' : 'var(--accent)',
                            }}
                        />
                    </div>
                    <div className="mt-1.5 flex justify-between text-xs faint">
                        <span>{tooShort ? `Write at least ${MIN} characters.` : 'Looks good.'}</span>
                        <span className={`tabular-nums ${nearLimit ? 'text-[#e3b04b]' : ''}`}>
                            {length}/{MAX}
                        </span>
                    </div>
                </div>

                <div className="flex gap-3 rounded-lg border bg-[var(--raised)] p-3.5 text-[13px] leading-relaxed muted hairline">
                    <svg
                        viewBox="0 0 24 24"
                        className="mt-0.5 h-4 w-4 shrink-0 text-[color:var(--accent)]"
                        fill="none"
                        stroke="currentColor"
                        strokeWidth="1.8"
                        strokeLinecap="round"
                        strokeLinejoin="round"
                    >
                        <circle cx="12" cy="12" r="9" />
                        <path d="M12 11v5M12 8h.01" />
                    </svg>
                    <span>
                        Test accounts are created automatically with synthetic data for each run. No credentials are
                        needed here.
                    </span>
                </div>

                <div className="flex items-center justify-between gap-4 border-t pt-5 hairline">
                    <span className="hidden text-xs faint sm:block">
                        <kbd>Ctrl</kbd> / <kbd>⌘</kbd> + <kbd>Enter</kbd> to start
                    </span>
                    <button type="submit" disabled={submitting || tooShort} className="btn btn-primary ml-auto px-5">
                        {submitting ? 'Starting...' : 'Start testing'}
                    </button>
                </div>
            </form>
        </div>
    )
}
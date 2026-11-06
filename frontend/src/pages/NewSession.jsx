import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { createSession, errorMessage } from '../api'

const EXAMPLE =
    'Test the registration and login functionality. Verify valid registration, duplicate email registration, invalid email, empty fields, successful login, and incorrect password.'

export default function NewSession() {
    const navigate = useNavigate()
    const [targetUrl, setTargetUrl] = useState('http://localhost:3000')
    const [instructions, setInstructions] = useState('')
    const [submitting, setSubmitting] = useState(false)
    const [error, setError] = useState(null)

    const tooShort = instructions.trim().length < 10

    const submit = (e) => {
        e.preventDefault()
        setSubmitting(true)
        setError(null)
        createSession(targetUrl.trim(), instructions.trim())
            .then((session) => navigate(`/sessions/${session.id}`))
            .catch((err) => setError(errorMessage(err)))
            .finally(() => setSubmitting(false))
    }

    return (
        <div className="max-w-2xl">
            <h1 className="mb-6 text-2xl font-bold">Create testing session</h1>

            {error && (
                <div className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                    {error}
                </div>
            )}

            <form onSubmit={submit} className="space-y-5 rounded-lg border bg-white p-6 shadow-sm">
                <div>
                    <label className="mb-1 block text-sm font-medium">Target website URL</label>
                    <input
                        type="url"
                        required
                        value={targetUrl}
                        onChange={(e) => setTargetUrl(e.target.value)}
                        className="w-full rounded-md border px-3 py-2 text-sm"
                    />
                    <p className="mt-1 text-xs text-slate-500">
                        Only approved targets are accepted. Others are rejected by the server.
                    </p>
                </div>

                <div>
                    <div className="mb-1 flex items-center justify-between">
                        <label className="block text-sm font-medium">Testing instructions</label>
                        <button
                            type="button"
                            onClick={() => setInstructions(EXAMPLE)}
                            className="text-xs text-blue-600 hover:underline"
                        >
                            Use example
                        </button>
                    </div>
                    <textarea
                        rows="6"
                        value={instructions}
                        onChange={(e) => setInstructions(e.target.value)}
                        placeholder="Describe what to test in plain language..."
                        className="w-full rounded-md border px-3 py-2 text-sm"
                    />
                    <p className="mt-1 text-xs text-slate-500">
                        {instructions.trim().length}/2000 characters (minimum 10)
                    </p>
                </div>

                <div className="rounded-md bg-slate-50 p-3 text-xs text-slate-600">
                    Test accounts are created automatically with synthetic data for each run.
                    No credentials are needed here.
                </div>

                <button
                    type="submit"
                    disabled={submitting || tooShort}
                    className="rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-40"
                >
                    {submitting ? 'Starting...' : 'Start testing'}
                </button>
            </form>
        </div>
    )
}
// 
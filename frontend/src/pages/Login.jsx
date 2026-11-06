import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { errorMessage, login, register, setToken } from '../api'

const SAMPLE_LOG = [
    ['tone-blue', 'Explored 14 pages on the target site'],
    ['tone-green', '12 of 14 test cases passed'],
    ['tone-red', '2 bug reports filed with steps to reproduce'],
]

export default function Login() {
    const navigate = useNavigate()
    const [mode, setMode] = useState('login')
    const [email, setEmail] = useState('')
    const [fullName, setFullName] = useState('')
    const [password, setPassword] = useState('')
    const [showPassword, setShowPassword] = useState(false)
    const [error, setError] = useState(null)
    const [busy, setBusy] = useState(false)

    const submit = async (e) => {
        e.preventDefault()
        setBusy(true)
        setError(null)
        try {
            if (mode === 'register') await register(email.trim(), fullName.trim(), password)
            const { access_token } = await login(email.trim(), password)
            setToken(access_token)
            navigate('/')
        } catch (err) {
            setError(errorMessage(err))
        } finally {
            setBusy(false)
        }
    }

    const isLogin = mode === 'login'

    return (
        <div className="panel mx-auto mt-10 grid max-w-4xl overflow-hidden md:grid-cols-[1.1fr_1fr]">
            <aside className="hidden flex-col justify-between border-r bg-[var(--raised)] p-8 hairline md:flex">
                <div>
                    <h2 className="max-w-xs text-2xl font-semibold leading-snug">
                        Describe what to test. Get back a bug report.
                    </h2>
                    <p className="mt-3 max-w-xs text-sm leading-relaxed muted">
                        Give the agent a URL and plain-language instructions. It explores the site, runs the checks and
                        keeps evidence for every result.
                    </p>
                </div>

                <ul className="mt-10 space-y-2.5 rounded-lg border bg-[var(--bg)] p-4 hairline">
                    {SAMPLE_LOG.map(([tone, line]) => (
                        <li key={line} className="flex items-center gap-2.5 text-[13px]">
                            <span className={`badge ${tone} !border-0 !bg-transparent !p-0`} aria-hidden="true" />
                            <span className="mono muted">{line}</span>
                        </li>
                    ))}
                </ul>
            </aside>

            <div className="p-6 sm:p-8">
                <h1 className="text-xl font-semibold">{isLogin ? 'Sign in' : 'Create account'}</h1>
                <p className="mb-6 mt-1 text-sm muted">
                    {isLogin ? 'Welcome back. Pick up where you left off.' : 'It takes under a minute.'}
                </p>

                {error && <div className="alert-error mb-4">{error}</div>}

                <form onSubmit={submit} className="space-y-4">
                    {!isLogin && (
                        <div>
                            <label htmlFor="name" className="label">Full name</label>
                            <input
                                id="name"
                                className="field"
                                autoComplete="name"
                                required
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                            />
                        </div>
                    )}

                    <div>
                        <label htmlFor="email" className="label">Email</label>
                        <input
                            id="email"
                            className="field"
                            type="email"
                            autoComplete="email"
                            required
                            value={email}
                            onChange={(e) => setEmail(e.target.value)}
                        />
                    </div>

                    <div>
                        <label htmlFor="password" className="label">Password</label>
                        <div className="relative">
                            <input
                                id="password"
                                className="field pr-16"
                                type={showPassword ? 'text' : 'password'}
                                autoComplete={isLogin ? 'current-password' : 'new-password'}
                                required
                                minLength={isLogin ? 1 : 8}
                                value={password}
                                onChange={(e) => setPassword(e.target.value)}
                            />
                            <button
                                type="button"
                                onClick={() => setShowPassword((v) => !v)}
                                className="absolute inset-y-0 right-2 my-auto h-7 rounded px-2 text-xs muted hover:text-[color:var(--text)]"
                                aria-pressed={showPassword}
                            >
                                {showPassword ? 'Hide' : 'Show'}
                            </button>
                        </div>
                        {!isLogin && <p className="mt-1.5 text-xs faint">At least 8 characters.</p>}
                    </div>

                    <button type="submit" disabled={busy} className="btn btn-primary w-full py-2.5">
                        {busy ? 'Please wait...' : isLogin ? 'Sign in' : 'Create account'}
                    </button>
                </form>

                <button
                    onClick={() => {
                        setMode(isLogin ? 'register' : 'login')
                        setError(null)
                    }}
                    className="link mt-5 text-sm"
                >
                    {isLogin ? 'No account? Create one' : 'Have an account? Sign in'}
                </button>
            </div>
        </div>
    )
}
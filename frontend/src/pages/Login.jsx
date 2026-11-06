import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { errorMessage, login, register, setToken } from '../api'

export default function Login() {
    const navigate = useNavigate()
    const [mode, setMode] = useState('login')
    const [email, setEmail] = useState('')
    const [fullName, setFullName] = useState('')
    const [password, setPassword] = useState('')
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

    const input = 'w-full rounded-md border px-3 py-2 text-sm'

    return (
        <div className="mx-auto mt-16 max-w-sm">
            <h1 className="mb-6 text-2xl font-bold">
                {mode === 'login' ? 'Sign in' : 'Create account'}
            </h1>
            {error && (
                <div className="mb-4 rounded-md border border-red-200 bg-red-50 p-3 text-sm text-red-700">
                    {error}
                </div>
            )}
            <form onSubmit={submit} className="space-y-4 rounded-lg border bg-white p-6 shadow-sm">
                {mode === 'register' && (
                    <input className={input} placeholder="Full name" required value={fullName}
                        onChange={(e) => setFullName(e.target.value)} />
                )}
                <input className={input} type="email" placeholder="Email" required value={email}
                    onChange={(e) => setEmail(e.target.value)} />
                <input className={input} type="password" placeholder="Password (min 8 characters)"
                    required minLength={mode === 'register' ? 8 : 1} value={password}
                    onChange={(e) => setPassword(e.target.value)} />
                <button type="submit" disabled={busy}
                    className="w-full rounded-md bg-slate-900 px-4 py-2 text-sm font-medium text-white hover:bg-slate-700 disabled:opacity-40">
                    {busy ? 'Please wait...' : mode === 'login' ? 'Sign in' : 'Register'}
                </button>
            </form>
            <button
                onClick={() => { setMode(mode === 'login' ? 'register' : 'login'); setError(null) }}
                className="mt-4 text-sm text-blue-600 hover:underline"
            >
                {mode === 'login' ? 'No account? Register' : 'Have an account? Sign in'}
            </button>
        </div>
    )
}
// 
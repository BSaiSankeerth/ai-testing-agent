import { useEffect, useState } from 'react'
import { Navigate, NavLink, Outlet, Route, Routes, useNavigate } from 'react-router-dom'
import { clearToken, getMe, getToken } from './api'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import NewSession from './pages/NewSession'
import SessionDetail from './pages/SessionDetail'

const linkClass = ({ isActive }) =>
  `rounded-md px-3 py-1.5 text-sm font-medium transition-colors ${isActive
    ? 'bg-[var(--raised)] text-[color:var(--text)] shadow-[inset_0_0_0_1px_var(--line-strong)]'
    : 'text-[color:var(--muted)] hover:bg-[var(--raised)] hover:text-[color:var(--text)]'
  }`

function BrandMark() {
  return (
    <span className="grid h-7 w-7 place-items-center rounded-lg bg-[var(--accent)] text-[var(--accent-ink)]">
      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
        <path d="M3 12h4l3-7 4 14 3-7h4" />
      </svg>
    </span>
  )
}

function Layout() {
  const navigate = useNavigate()
  const [user, setUser] = useState(null)

  useEffect(() => {
    getMe().then(setUser).catch(() => { })
  }, [])

  const logout = () => {
    clearToken()
    navigate('/login')
  }

  if (!getToken()) return <Navigate to="/login" replace />

  const initial = user?.full_name?.trim()?.[0]?.toUpperCase()

  return (
    <div className="min-h-screen bg-[var(--bg)] text-[color:var(--text)]">
      <header className="sticky top-0 z-20 border-b bg-[color-mix(in_srgb,var(--surface)_88%,transparent)] backdrop-blur hairline">
        <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-x-6 gap-y-2 px-6 py-3">
          <div className="flex items-center gap-2.5">
            <BrandMark />
            <span className="text-[15px] font-semibold tracking-tight">AI Testing Agent</span>
          </div>

          <nav className="flex gap-1">
            <NavLink to="/" end className={linkClass}>Dashboard</NavLink>
            <NavLink to="/new" className={linkClass}>New session</NavLink>
          </nav>

          <div className="ml-auto flex items-center gap-3 text-sm">
            {user?.full_name && (
              <div className="flex items-center gap-2">
                <span className="grid h-7 w-7 place-items-center rounded-full border bg-[var(--raised)] text-xs font-semibold hairline">
                  {initial}
                </span>
                <span className="hidden muted sm:inline">{user.full_name}</span>
              </div>
            )}
            <button onClick={logout} className="btn btn-ghost btn-sm">
              Log out
            </button>
          </div>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Outlet />
      </main>
    </div>
  )
}

export default function App() {
  return (
    <Routes>
      <Route
        path="/login"
        element={
          <div className="min-h-screen bg-[var(--bg)] px-4 py-6">
            <Login />
          </div>
        }
      />
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/new" element={<NewSession />} />
        <Route path="/sessions/:id" element={<SessionDetail />} />
      </Route>
    </Routes>
  )
}
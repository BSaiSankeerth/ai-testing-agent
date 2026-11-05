import { useEffect, useState } from 'react'
import { Navigate, NavLink, Outlet, Route, Routes, useNavigate } from 'react-router-dom'
import { clearToken, getMe, getToken } from './api'
import Dashboard from './pages/Dashboard'
import Login from './pages/Login'
import NewSession from './pages/NewSession'
import SessionDetail from './pages/SessionDetail'

const linkClass = ({ isActive }) =>
  `px-3 py-2 rounded-md text-sm font-medium ${isActive ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-200'
  }`

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

  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-3">
          <span className="text-lg font-semibold">AI Testing Agent</span>
          <nav className="flex gap-1">
            <NavLink to="/" end className={linkClass}>Dashboard</NavLink>
            <NavLink to="/new" className={linkClass}>New session</NavLink>
          </nav>
          <div className="ml-auto flex items-center gap-3 text-sm">
            <span className="text-slate-500">{user?.full_name}</span>
            <button onClick={logout} className="rounded-md border px-3 py-1.5 hover:bg-slate-100">
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
      <Route path="/login" element={<div className="min-h-screen bg-slate-50"><Login /></div>} />
      <Route element={<Layout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/new" element={<NewSession />} />
        <Route path="/sessions/:id" element={<SessionDetail />} />
      </Route>
    </Routes>
  )
}
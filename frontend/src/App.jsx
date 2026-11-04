import { NavLink, Route, Routes } from 'react-router-dom'
import Dashboard from './pages/Dashboard'

const linkClass = ({ isActive }) =>
  `px-3 py-2 rounded-md text-sm font-medium ${isActive ? 'bg-slate-900 text-white' : 'text-slate-600 hover:bg-slate-200'
  }`

export default function App() {
  return (
    <div className="min-h-screen bg-slate-50 text-slate-900">
      <header className="border-b bg-white">
        <div className="mx-auto flex max-w-6xl items-center gap-6 px-6 py-3">
          <span className="text-lg font-semibold">AI Testing Agent</span>
          <nav className="flex gap-1">
            <NavLink to="/" end className={linkClass}>
              Dashboard
            </NavLink>
          </nav>
        </div>
      </header>
      <main className="mx-auto max-w-6xl px-6 py-8">
        <Routes>
          <Route path="/" element={<Dashboard />} />
        </Routes>
      </main>
    </div>
  )
}
import { useEffect, useState } from 'react'
import axios from 'axios'

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8001'

function App() {
  const [loading, setLoading] = useState(true)
  const [health, setHealth] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    axios
      .get(`${API_URL}/api/health`)
      .then((response) => setHealth(response.data))
      .catch((err) => setError(err.message))
      .finally(() => setLoading(false))
  }, [])

  return (
    <div style={{ padding: '2rem', fontFamily: 'sans-serif' }}>
      <h1>AI Testing Agent Dashboard</h1>

      {loading && <p>Checking backend...</p>}

      {health && (
        <p style={{ color: 'green' }}>
          Backend connected: {health.app} ({health.environment})
        </p>
      )}

      {error && <p style={{ color: 'red' }}>Backend error: {error}</p>}
    </div>
  )
}

export default App
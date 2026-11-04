import axios from 'axios'

const client = axios.create({
    baseURL: `${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api`,
    timeout: 15000,
})

export function errorMessage(err) {
    if (err.response) {
        const detail = err.response.data?.detail
        if (typeof detail === 'string') return detail
        if (Array.isArray(detail)) return detail.map((d) => d.msg).join('; ')
        return `Request failed (${err.response.status})`
    }
    if (err.request) return 'Cannot reach the backend. Is it running on port 8001?'
    return err.message
}

export const getStats = () => client.get('/sessions/stats').then((r) => r.data)
export const listSessions = () => client.get('/sessions').then((r) => r.data)
export const getSession = (id) => client.get(`/sessions/${id}`).then((r) => r.data)
export const createSession = (targetUrl, instructions) =>
    client
        .post('/sessions', { target_url: targetUrl, instructions })
        .then((r) => r.data)
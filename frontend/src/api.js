import axios from 'axios'

const TOKEN_KEY = 'token'

export const getToken = () => localStorage.getItem(TOKEN_KEY)
export const setToken = (t) => localStorage.setItem(TOKEN_KEY, t)
export const clearToken = () => localStorage.removeItem(TOKEN_KEY)

const client = axios.create({
    baseURL: `${import.meta.env.VITE_API_URL || 'http://localhost:8001'}/api`,
    timeout: 15000,
})

client.interceptors.request.use((config) => {
    const token = getToken()
    if (token) config.headers.Authorization = `Bearer ${token}`
    return config
})

client.interceptors.response.use(
    (r) => r,
    (err) => {
        const isAuthCall = err.config?.url?.startsWith('/auth/login') || err.config?.url?.startsWith('/auth/register')
        if (err.response?.status === 401 && !isAuthCall) {
            clearToken()
            if (window.location.pathname !== '/login') window.location.assign('/login')
        }
        return Promise.reject(err)
    },
)

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

export const login = (email, password) =>
    client.post('/auth/login', { email, password }).then((r) => r.data)
export const register = (email, fullName, password) =>
    client
        .post('/auth/register', { email, full_name: fullName, password })
        .then((r) => r.data)
export const getMe = () => client.get('/auth/me').then((r) => r.data)

export const getStats = () => client.get('/sessions/stats').then((r) => r.data)
export const listSessions = () => client.get('/sessions').then((r) => r.data)
export const getSession = (id) => client.get(`/sessions/${id}`).then((r) => r.data)
export const createSession = (targetUrl, instructions) =>
    client
        .post('/sessions', { target_url: targetUrl, instructions })
        .then((r) => r.data)

export const getEvidence = (resultId) =>
    client.get(`/results/${resultId}/evidence`).then((r) => r.data)

export const getScreenshotUrl = (resultId) =>
    client
        .get(`/results/${resultId}/screenshot`, { responseType: 'blob' })
        .then((r) => URL.createObjectURL(r.data))
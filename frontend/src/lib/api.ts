import { supabase } from './supabase'

export const fetchApi = async (endpoint: string, options: RequestInit = {}) => {
  const baseUrl = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8000/api'
  const url = `${baseUrl}${endpoint}`

  const headers = new Headers(options.headers)
  
  if (!(options.body instanceof FormData) && !headers.has('Content-Type')) {
    headers.set('Content-Type', 'application/json')
  }

  // Auto-inject auth token if available
  if (!headers.has('Authorization')) {
    const { data: { session } } = await supabase.auth.getSession()
    if (session?.access_token) {
      headers.set('Authorization', `Bearer ${session.access_token}`)
    }
  }

  const response = await fetch(url, {
    ...options,
    headers,
  })

  if (!response.ok) {
    const errorBody = await response.text().catch(() => null)
    throw new Error(errorBody || `API Error: ${response.status} ${response.statusText}`)
  }

  return response.json()
}

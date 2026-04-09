import { createClient } from './supabase/client'

const BACKEND_URL = process.env.NEXT_PUBLIC_SOCKET_URL || 'http://localhost:5000'

export async function authenticatedFetch<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const supabase = createClient()
  const { data: { session } } = await supabase.auth.getSession()
  
  const token = session?.access_token
  
  const headers = new Headers(options.headers)
  if (token) {
    headers.set('Authorization', `Bearer ${token}`)
  }
  headers.set('Content-Type', 'application/json')
  
  const response = await fetch(`${BACKEND_URL}${endpoint}`, {
    ...options,
    headers,
  })
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.message || `API error: ${response.status} ${response.statusText}`)
  }
  
  const result = await response.json()
  return result.data as T
}

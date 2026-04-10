'use client'

import { useEffect, useRef, useState } from 'react'
import { useRouter } from 'next/navigation'

type SSEEvent = {
  type: string
  data: any
}

export function useSSE(hospitalId: string | null) {
  const [lastEvent, setLastEvent] = useState<SSEEvent | null>(null)
  const [isConnected, setIsConnected] = useState(false)
  const eventSourceRef = useRef<EventSource | null>(null)
  const router = useRouter()

  useEffect(() => {
    if (!hospitalId) return

    // Create SSE connection
    const url = `${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:5000'}/api/v1/realtime/stream?hospital_id=${hospitalId}`
    const eventSource = new EventSource(url)
    eventSourceRef.current = eventSource

    eventSource.onopen = () => {
      setIsConnected(true)
      console.log('>>> [SSE] Connected to hospital stream:', hospitalId)
    }

    eventSource.onerror = (err) => {
      setIsConnected(false)
      console.error('>>> [SSE] Connection error:', err)
      eventSource.close()
    }

    // Generic event handler
    const handleEvent = (type: string, data: string) => {
      try {
        const parsedData = JSON.parse(data)
        setLastEvent({ type, data: parsedData })
        
        // Handle global refresh if needed
        if (type === 'queue:update' && parsedData.refresh) {
          router.refresh()
        }
      } catch (e) {
        console.error('>>> [SSE] Failed to parse event data:', e)
      }
    }

    // Register specific event listeners
    eventSource.addEventListener('patient:new', (e) => handleEvent('patient:new', e.data))
    eventSource.addEventListener('queue:update', (e) => handleEvent('queue:update', e.data))
    eventSource.addEventListener('doctor:update', (e) => handleEvent('doctor:update', e.data))
    eventSource.addEventListener('critical:alert', (e) => handleEvent('critical:alert', e.data))
    eventSource.addEventListener('ping', (e) => console.log('>>> [SSE] Ping received'))

    return () => {
      console.log('>>> [SSE] Closing connection')
      eventSource.close()
    }
  }, [hospitalId, router])

  return { lastEvent, isConnected }
}

'use client'

import { useEffect } from 'react'
import { useSocket } from '@/hooks/use-socket'
import { toast } from 'sonner'
import { useRouter } from 'next/navigation'

export function SocketListener() {
  const { socket, isConnected } = useSocket()
  const router = useRouter()

  useEffect(() => {
    if (!socket) return

    // Listen for new patient alerts
    socket.on('patient:new', (data) => {
      console.log('Received patient:new', data)
      toast.success('New Patient Alert', {
        description: `${data.name} has just been registered.`,
        duration: 5000,
        action: {
          label: 'View Queue',
          onClick: () => router.push('/intake'), // Or to a specific dashboard
        },
      })
    })

    // Listen for queue updates
    socket.on('queue:update', () => {
      console.log('Received queue:update')
      // Refresh the current page data without a full reload
      router.refresh()
    })

    // Listen for doctor updates
    socket.on('doctor:update', (data) => {
      console.log('Received doctor:update', data)
      toast.info('Doctor Load Update', {
        description: `${data.name}'s load has changed.`,
      })
    })

    return () => {
      socket.off('patient:new')
      socket.off('queue:update')
      socket.off('doctor:update')
    }
  }, [socket, router])

  // This component doesn't render anything UI-wise, just handles side effects
  return null
}

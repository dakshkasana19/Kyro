'use client'

import { useEffect, useCallback } from 'react'
import { useSocket } from '@/hooks/use-socket'
import { toast } from 'sonner'
import { AlertCircle, Activity, UserPlus, Eye } from 'lucide-react'
import { useRouter } from 'next/navigation'

export function SocketListener() {
  const { socket } = useSocket()
  const router = useRouter()

  const playAlertSound = useCallback(() => {
    try {
      const audio = new Audio('https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3') // Medical chime
      audio.volume = 0.5
      audio.play().catch(e => console.warn('Audio playback blocked by browser policy:', e))
    } catch (e) {
      console.error('Failed to play alert sound:', e)
    }
  }, [])

  useEffect(() => {
    if (!socket) return

    // 1. Standard Admission Notification
    socket.on('patient:new', (data: { name: string, severity_level: number, patient_id: string }) => {
      // We skip toasts here if it's a critical patient to avoid double-toasting
      // (the critical:alert will handle the urgent UI)
      if (data.severity_level === 3) return

      toast('New Patient Registered', {
        description: `${data.name} has been triaged.`,
        duration: 5000,
        icon: <UserPlus className="w-5 h-5 text-blue-500" />,
        className: 'bg-white border-slate-100 font-medium',
        action: {
          label: 'View Queue',
          onClick: () => router.push('/dashboard/queue')
        }
      })
    })

    // 2. High-Severity Critical Alert
    socket.on('critical:alert', (data: { name: string, patient_id: string, message: string }) => {
      // Trigger Audio Chime
      playAlertSound()

      // Show Persistent, Urgent Toast
      toast.error('URGENT: CRITICAL ADMISSION', {
        description: `${data.name} requires immediate medical intervention.`,
        duration: Infinity, // Persistent until closed
        icon: <AlertCircle className="w-6 h-6 text-white animate-pulse" />,
        className: 'bg-rose-600 text-white border-rose-700 shadow-2xl shadow-rose-200 p-6',
        action: {
          label: (
            <div className="flex items-center gap-2 font-bold px-2">
              <Eye className="w-4 h-4" />
              VIEW VITALS
            </div>
          ),
          onClick: () => router.push('/dashboard/queue') // In Phase 4, this could link to detailed vitals overlay
        }
      })
    })

    socket.on('doctor:update', (data: any) => {
      console.log('Real-time staff update:', data.name)
    })

    return () => {
      socket.off('patient:new')
      socket.off('critical:alert')
      socket.off('doctor:update')
    }
  }, [socket, router, playAlertSound])

  return null
}

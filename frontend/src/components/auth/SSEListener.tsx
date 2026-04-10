'use client'

import { useEffect, useCallback } from 'react'
import { useSSE } from '@/hooks/useSSE'
import { toast } from 'sonner'
import { AlertCircle, UserPlus, Eye } from 'lucide-react'
import { useRouter } from 'next/navigation'

interface SSEListenerProps {
  hospitalId: string | null
}

export function SSEListener({ hospitalId }: SSEListenerProps) {
  const { lastEvent } = useSSE(hospitalId)
  const router = useRouter()

  const playAlertSound = useCallback(() => {
    try {
      const audio = new Audio('https://assets.mixkit.co/active_storage/sfx/2869/2869-preview.mp3') 
      audio.volume = 0.5
      audio.play().catch(e => console.warn('Audio playback blocked by browser policy:', e))
    } catch (e) {
      console.error('Failed to play alert sound:', e)
    }
  }, [])

  useEffect(() => {
    if (!lastEvent) return

    const { type, data } = lastEvent

    switch (type) {
      case 'patient:new':
        if (data.severity_level === 3) break // Handled by critical:alert
        
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
        break

      case 'critical:alert':
        playAlertSound()
        toast.error('URGENT: CRITICAL ADMISSION', {
          description: `${data.name} requires immediate medical intervention.`,
          duration: Infinity,
          icon: <AlertCircle className="w-6 h-6 text-white animate-pulse" />,
          className: 'bg-rose-600 text-white border-rose-700 shadow-2xl shadow-rose-200 p-6',
          action: {
            label: (
              <div className="flex items-center gap-2 font-bold px-2">
                <Eye className="w-4 h-4" />
                VIEW VITALS
              </div>
            ),
            onClick: () => router.push('/dashboard/queue')
          }
        })
        break

      case 'doctor:update':
        console.log('Real-time staff update:', data.name)
        break
        
      default:
        break
    }
  }, [lastEvent, router, playAlertSound])

  return null
}

'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Doctor } from '@/types/dashboard'
import { authenticatedFetch } from '@/utils/api-client'
import { useSocket } from '@/hooks/use-socket'
import { cn } from '@/lib/utils'
import { Activity, Stethoscope } from 'lucide-react'

export function DoctorPanel() {
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [loading, setLoading] = useState(true)
  const { socket } = useSocket()

  const fetchDoctors = async () => {
    try {
      const data = await authenticatedFetch<Doctor[]>('/api/doctors')
      setDoctors(data)
    } catch (error) {
      console.error('Failed to fetch doctors:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDoctors()
  }, [])

  useEffect(() => {
    if (!socket) return

    socket.on('doctor:update', () => {
      console.log('Doctor update received via socket')
      fetchDoctors()
    })

    return () => {
      socket.off('doctor:update')
    }
  }, [socket])

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-24 w-full rounded-2xl bg-slate-50" />
        ))}
      </div>
    )
  }

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Stethoscope className="w-5 h-5 text-blue-500" />
          On-Duty Staff
        </h3>
        <Badge variant="outline" className="text-blue-600 bg-blue-50 border-blue-100 font-bold rounded-lg py-1">
          {doctors.filter(d => d.is_available).length} Online
        </Badge>
      </div>

      <div className="grid gap-4">
        {doctors.map((doctor) => {
          const loadPercentage = (doctor.current_load / doctor.max_capacity) * 100
          const loadColor = loadPercentage > 80 ? 'bg-pink-500' : 'bg-blue-500'
          
          return (
            <Card key={doctor.id} className="border-slate-100 shadow-sm hover:shadow-md transition-shadow duration-200 overflow-hidden group">
              <CardContent className="p-4">
                <div className="flex items-start gap-4">
                  <Avatar className="w-12 h-12 border-2 border-slate-50 ring-2 ring-blue-50 shadow-sm">
                    <AvatarFallback className="bg-blue-600 text-white font-bold">
                      {doctor.name.split(' ').map(n => n[0]).join('')}
                    </AvatarFallback>
                  </Avatar>
                  
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <p className="font-bold text-slate-900 truncate pr-2">{doctor.name}</p>
                      <div className={`w-2 h-2 rounded-full ${doctor.is_available ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-slate-300'}`} />
                    </div>
                    <p className="text-xs text-slate-500 mb-3 uppercase tracking-wider font-semibold">{doctor.specialization}</p>
                    
                    <div className="space-y-2">
                      <div className="flex justify-between text-[10px] font-bold uppercase tracking-tight">
                        <span className="text-slate-400">Current Load</span>
                        <span className={loadPercentage > 80 ? 'text-pink-600' : 'text-blue-600'}>
                          {doctor.current_load} / {doctor.max_capacity}
                        </span>
                      </div>
                      <Progress value={loadPercentage} className={cn("h-1.5 bg-slate-100", loadColor)} />
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}

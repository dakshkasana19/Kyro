'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Avatar, AvatarFallback } from '@/components/ui/avatar'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { Doctor } from '@/types/dashboard'
import { authenticatedFetch } from '@/utils/api-client'
import { useSocket } from '@/hooks/use-socket'
import { cn } from '@/lib/utils'
import { Stethoscope, Edit2, Trash2, X } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { createClient } from '@/utils/supabase/client'
import { toast } from 'sonner'
import { DoctorForm } from './DoctorForm'

export function DoctorPanel() {
  const [doctors, setDoctors] = useState<Doctor[]>([])
  const [loading, setLoading] = useState(true)
  const [role, setRole] = useState<string | null>(null)
  const [editingDoctor, setEditingDoctor] = useState<Doctor | null>(null)
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
    const checkRole = async () => {
      const supabase = createClient()
      const { data: { user } } = await supabase.auth.getUser()
      setRole(user?.user_metadata?.role || null)
    }
    checkRole()
    fetchDoctors()
  }, [])

  useEffect(() => {
    if (!socket) return

    socket.on('doctor:update', () => {
      fetchDoctors()
    })

    return () => {
      socket.off('doctor:update')
    }
  }, [socket])

  const handleDelete = async (id: string, name: string) => {
    if (!confirm(`Are you sure you want to remove ${name} from the staff? This will unassign all their active patients.`)) return

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      const response = await fetch(`/api/doctors/${id}`, {
        method: 'DELETE',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`
        }
      })

      if (response.ok) {
        toast.success('Staff Member Removed', { description: `${name} has been deleted from the registry.` })
        fetchDoctors()
      } else {
        toast.error('Deletion failed')
      }
    } catch (error) {
      toast.error('Network Error')
    }
  }

  if (loading) {
    return (
      <div className="space-y-4">
        {[...Array(3)].map((_, i) => (
          <Skeleton key={i} className="h-24 w-full rounded-2xl bg-slate-50" />
        ))}
      </div>
    )
  }

  const isAdmin = role === 'Admin'

  return (
    <div className="space-y-4 relative">
      {/* Edit Modal Overlay */}
      {editingDoctor && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-lg shadow-2xl border-slate-100 bg-white">
            <div className="p-6 border-b border-slate-50 flex justify-between items-center bg-slate-50/50">
              <div>
                <h3 className="text-xl font-bold text-slate-900">Edit Practitioner</h3>
                <p className="text-sm text-slate-400">Updating profile for {editingDoctor.name}</p>
              </div>
              <Button variant="ghost" className="rounded-full w-10 h-10 p-0" onClick={() => setEditingDoctor(null)}>
                <X className="w-5 h-5 text-slate-400" />
              </Button>
            </div>
            <div className="p-8">
              <DoctorForm 
                doctor={editingDoctor} 
                onSuccess={() => {
                  setEditingDoctor(null)
                  fetchDoctors()
                }}
                onCancel={() => setEditingDoctor(null)}
              />
            </div>
          </Card>
        </div>
      )}

      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-bold text-slate-900 flex items-center gap-2">
          <Stethoscope className="w-5 h-5 text-blue-500" />
          On-Duty Staff
        </h3>
        <Badge variant="outline" className="text-blue-600 bg-blue-50 border-blue-100 font-bold rounded-lg py-1">
          {doctors.filter(d => d.is_available).length} Active
        </Badge>
      </div>

      <div className="grid gap-4">
        {doctors.map((doctor) => {
          const loadPercentage = (doctor.current_load / doctor.max_capacity) * 100
          const loadColor = loadPercentage > 80 ? 'bg-pink-500' : 'bg-blue-500'
          
          return (
            <Card key={doctor.id} className="border-slate-100 shadow-sm hover:shadow-md transition-all duration-200 overflow-hidden group bg-white">
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
                      <div className="flex items-center gap-2">
                        {isAdmin && (
                          <div className="flex items-center opacity-0 group-hover:opacity-100 transition-opacity">
                            <button 
                              onClick={() => setEditingDoctor(doctor)}
                              className="p-1.5 text-slate-400 hover:text-blue-600 transition-colors"
                            >
                              <Edit2 className="w-3.5 h-3.5" />
                            </button>
                            <button 
                              onClick={() => handleDelete(doctor.id, doctor.name)}
                              className="p-1.5 text-slate-400 hover:text-pink-600 transition-colors"
                            >
                              <Trash2 className="w-3.5 h-3.5" />
                            </button>
                          </div>
                        )}
                        <div className={`w-2 h-2 rounded-full ${doctor.is_available ? 'bg-emerald-500 shadow-[0_0_8px_rgba(16,185,129,0.5)]' : 'bg-slate-300'}`} />
                      </div>
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

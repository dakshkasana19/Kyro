'use client'

import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { authenticatedFetch } from '@/utils/api-client'
import { useSocket } from '@/hooks/use-socket'
import { formatDistanceToNow } from 'date-fns'
import Link from 'next/link'
import { 
  Stethoscope, 
  Users, 
  ChevronRight, 
  Clock, 
  Activity,
  Heart
} from 'lucide-react'

interface AssignedPatient {
  triage_id: string
  patient_id: string
  patient_name: string
  age: number
  gender: string
  severity_level: number
  severity_label: string
  confidence_score: number
  created_at: string
}

interface DashboardData {
  doctor: {
    name: string
    specialization: string
    current_load: number
    max_capacity: number
  }
  patients: AssignedPatient[]
}

export default function DoctorDashboard() {
  const [data, setData] = useState<DashboardData | null>(null)
  const [loading, setLoading] = useState(true)
  const { socket } = useSocket()

  const fetchData = async () => {
    try {
      const response = await authenticatedFetch<DashboardData>('/api/doctors/me/patients')
      setData(response)
    } catch (error) {
      console.error('Failed to fetch doctor dashboard:', error)
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchData()
  }, [])

  useEffect(() => {
    if (!socket) return

    // Re-fetch if the queue updates (e.g. they got a new assignment)
    socket.on('queue:update', fetchData)
    
    return () => {
      socket.off('queue:update')
    }
  }, [socket])

  if (loading) {
    return (
      <div className="space-y-8 animate-pulse">
        <div className="h-10 w-64 bg-slate-100 rounded-xl" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-48 bg-slate-50 rounded-2xl border border-slate-100" />
          ))}
        </div>
      </div>
    )
  }

  if (!data) return <div>Access denied or profile not found.</div>

  const getSeverityColor = (level: number) => {
    switch (level) {
      case 3: return 'bg-rose-100 text-rose-600 border-rose-200'
      case 2: return 'bg-amber-100 text-amber-600 border-amber-200'
      default: return 'bg-blue-100 text-blue-600 border-blue-200'
    }
  }

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-blue-600 font-bold uppercase tracking-widest text-[10px] mb-2">
            <div className="w-1.5 h-1.5 rounded-full bg-blue-600" />
            Clinical Portal
          </div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight">
            Welcome, <span className="text-blue-600">{data.doctor.name}</span>
          </h1>
          <p className="text-slate-500 font-medium">
            You have <span className="text-slate-900 font-bold">{data.patients.length} active patients</span> assigned.
          </p>
        </div>
        
        <div className="flex items-center gap-4 bg-white p-4 rounded-2xl border border-slate-100 shadow-sm">
          <div>
            <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-none mb-1">Current Load</p>
            <p className="text-lg font-black text-slate-900 leading-none">
              {data.doctor.current_load} <span className="text-slate-300 font-medium">/ {data.doctor.max_capacity}</span>
            </p>
          </div>
          <div className="w-10 h-10 bg-pink-50 rounded-xl flex items-center justify-center">
            <Activity className="w-5 h-5 text-pink-500" />
          </div>
        </div>
      </div>

      <div className="grid gap-6">
        <h2 className="text-xl font-bold text-slate-900 flex items-center gap-2">
          <Users className="w-5 h-5 text-blue-500" />
          Active Workload
        </h2>

        {data.patients.length === 0 ? (
          <div className="bg-white border-2 border-dashed border-slate-100 rounded-3xl p-20 text-center">
            <Heart className="w-12 h-12 text-slate-200 mx-auto mb-4" />
            <p className="font-bold text-slate-400">All cases resolved. Awaiting new assignments.</p>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {data.patients.map((patient) => (
              <Link key={patient.triage_id} href={`/doctor/patient/${patient.triage_id}`}>
                <Card className="border-slate-100 shadow-sm hover:shadow-xl hover:-translate-y-1 transition-all duration-300 group cursor-pointer bg-white h-full relative overflow-hidden">
                  <div className={`absolute top-0 right-0 w-24 h-24 -mr-8 -mt-8 rounded-full opacity-5 blur-xl ${patient.severity_level === 3 ? 'bg-rose-500' : 'bg-blue-500'}`} />
                  
                  <CardContent className="p-6">
                    <div className="flex justify-between items-start mb-6">
                      <div className="w-12 h-12 bg-slate-50 rounded-2xl flex items-center justify-center group-hover:bg-blue-600 group-hover:text-white transition-colors duration-300">
                        <Stethoscope className="w-6 h-6" />
                      </div>
                      <Badge className={`px-2 py-0.5 rounded-lg border shadow-none font-bold ${getSeverityColor(patient.severity_level)}`}>
                        {patient.severity_label}
                      </Badge>
                    </div>

                    <div className="space-y-0.5 mb-6">
                      <h4 className="text-lg font-black text-slate-900 truncate">{patient.patient_name}</h4>
                      <p className="text-sm font-medium text-slate-400">{patient.age}y • {patient.gender}</p>
                    </div>

                    <div className="flex items-center justify-between pt-4 border-t border-slate-50">
                      <div className="flex items-center gap-2 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                        <Clock className="w-3 h-3" />
                        {formatDistanceToNow(new Date(patient.created_at), { addSuffix: true })}
                      </div>
                      <div className="flex items-center gap-1 text-blue-600 font-bold text-sm">
                        View Analysis <ChevronRight className="w-4 h-4" />
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </Link>
            ))}
          </div>
        )}
      </div>
    </div>
  )
}

'use client'

import { useParams, useRouter } from 'next/navigation'
import { useEffect, useState } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Skeleton } from '@/components/ui/skeleton'
import { ShapChart } from '@/components/doctor/ShapChart'
import { authenticatedFetch } from '@/utils/api-client'
import { useSocket } from '@/hooks/use-socket'
import { toast } from 'sonner'
import { 
  ArrowLeft, 
  CheckCircle2, 
  Activity, 
  Thermometer, 
  Heart, 
  Wind, 
  Droplet,
  Trash2,
  Stethoscope
} from 'lucide-react'

interface PatientDetail {
  triage_id: string
  patient_id: string
  patient_name: string
  age: number
  gender: string
  severity_level: number
  severity_label: string
  confidence_score: number
  created_at: string
  vitals: {
    temperature: number
    heart_rate: number
    respiratory_rate: number
    systolic_bp: number
    diastolic_bp: number
    pain_scale: number
  }
  symptoms: string[]
  shap_summary: {
    feature_importance: Array<{ feature: string; shap_value: number }>
  }
}

export default function PatientDetailFull() {
  const { id } = useParams()
  const router = useRouter()
  const [patient, setPatient] = useState<PatientDetail | null>(null)
  const [loading, setLoading] = useState(true)
  const [resolving, setResolving] = useState(false)
  const { socket } = useSocket()

  useEffect(() => {
    const fetchPatient = async () => {
      try {
        const data = await authenticatedFetch<{patients: PatientDetail[]}>('/api/doctors/me/patients')
        const found = data.patients.find(p => p.triage_id === id)
        if (found) {
          setPatient(found)
        } else {
          toast.error('Patient not found')
          router.push('/doctor/dashboard')
        }
      } catch (error) {
        console.error('Fetch error:', error)
      } finally {
        setLoading(false)
      }
    }
    fetchPatient()
  }, [id, router])

  const handleResolve = async () => {
    setResolving(true)
    try {
      await authenticatedFetch(`/api/queue/resolve/${id}`, { method: 'POST' })
      toast.success('Case resolved successfully')
      router.push('/doctor/dashboard')
    } catch (error) {
      toast.error('Failed to resolve case')
      console.error(error)
    } finally {
      setResolving(false)
    }
  }

  if (loading) return <div className="p-8"><Skeleton className="h-screen w-full rounded-2xl" /></div>
  if (!patient) return null

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex items-center justify-between">
        <Button 
          variant="ghost" 
          onClick={() => router.back()} 
          className="group text-slate-400 hover:text-blue-600 font-bold gap-2 pl-0"
        >
          <ArrowLeft className="w-4 h-4 transition-transform group-hover:-translate-x-1" />
          Back to Dashboard
        </Button>
        
        <Button 
          onClick={handleResolve}
          disabled={resolving}
          className="bg-emerald-600 hover:bg-emerald-700 text-white font-black px-6 rounded-xl shadow-lg shadow-emerald-200 transition-all active:scale-[0.98]"
        >
          {resolving ? 'processing...' : (
            <>
              <CheckCircle2 className="w-4 h-4 mr-2" />
              Resolve & Mark Seen
            </>
          )}
        </Button>
      </div>

      {/* Profile Header */}
      <div className="bg-white p-8 rounded-3xl border border-slate-100 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden">
        <div className="absolute top-0 right-0 w-64 h-64 bg-blue-50 rounded-full -mr-32 -mt-32 opacity-50 blur-[80px]" />
        
        <div className="flex gap-6 items-center relative z-10">
          <div className="w-20 h-20 bg-blue-600 rounded-3xl flex items-center justify-center text-white shadow-xl shadow-blue-200">
            <Stethoscope className="w-10 h-10" />
          </div>
          <div>
            <h1 className="text-4xl font-black text-slate-900 tracking-tight mb-1">{patient.patient_name}</h1>
            <div className="flex items-center gap-4 text-slate-500 font-bold uppercase text-[11px] tracking-[0.2em]">
              <span>ID: {patient.patient_id.slice(0, 12)}</span>
              <span className="w-1 h-1 rounded-full bg-slate-300" />
              <span>{patient.age} Years Old</span>
              <span className="w-1 h-1 rounded-full bg-slate-300" />
              <span>{patient.gender}</span>
            </div>
          </div>
        </div>

        <div className="text-right relative z-10">
          <Badge className={`text-lg px-4 py-1.5 rounded-xl border-2 mb-2 font-black ${
            patient.severity_level === 3 ? 'bg-rose-50 text-rose-600 border-rose-100' : 'bg-blue-50 text-blue-600 border-blue-100'
          }`}>
            {patient.severity_label}
          </Badge>
          <p className="text-[10px] font-black text-slate-400 uppercase tracking-[0.15em]">AI Confidence Score: {(patient.confidence_score * 100).toFixed(1)}%</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        {/* Clinical Data Section */}
        <div className="lg:col-span-2 space-y-8">
          {/* Vitals Grid */}
          <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
            {[
              { label: 'Temp', val: `${patient.vitals.temperature}°C`, icon: Thermometer, color: 'text-amber-500', bg: 'bg-amber-50' },
              { label: 'Heart Rate', val: `${patient.vitals.heart_rate} bpm`, icon: Heart, color: 'text-rose-500', bg: 'bg-rose-50' },
              { label: 'Blood Pressure', val: `${patient.vitals.systolic_bp}/${patient.vitals.diastolic_bp}`, icon: Activity, color: 'text-blue-500', bg: 'bg-blue-50' },
              { label: 'Resp. Rate', val: `${patient.vitals.respiratory_rate}/m`, icon: Wind, color: 'text-indigo-500', bg: 'bg-indigo-50' },
              { label: 'Pain Scale', val: `${patient.vitals.pain_scale}/10`, icon: Droplet, color: 'text-pink-500', bg: 'bg-pink-50' },
            ].map((v, i) => (
              <div key={i} className="bg-white p-6 rounded-3xl border border-slate-50 shadow-sm hover:border-slate-100 transition-colors">
                <div className={`${v.bg} w-10 h-10 rounded-xl flex items-center justify-center mb-3`}>
                  <v.icon className={`w-5 h-5 ${v.color}`} />
                </div>
                <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest leading-none mb-1">{v.label}</p>
                <p className="text-xl font-black text-slate-900 leading-none">{v.val}</p>
              </div>
            ))}
          </div>

          {/* AI Explanation Chart */}
          <ShapChart data={patient.shap_summary.feature_importance} />
        </div>

        {/* Symptoms & Context */}
        <div className="space-y-8">
          <Card className="border-none bg-white shadow-sm overflow-hidden">
            <CardHeader className="bg-slate-50/50 border-b border-slate-50 py-4">
              <CardTitle className="text-sm font-black text-slate-900 uppercase tracking-wider">Reported Symptoms</CardTitle>
            </CardHeader>
            <CardContent className="pt-6">
              <div className="flex flex-wrap gap-2">
                {patient.symptoms.map((s, idx) => (
                  <Badge key={idx} variant="secondary" className="bg-slate-50 text-slate-600 border-none font-bold py-1.5 px-3 rounded-xl">
                    {s}
                  </Badge>
                ))}
              </div>
            </CardContent>
          </Card>

          <Card className="border-none bg-pink-50 shadow-sm">
            <CardHeader className="py-4">
              <CardTitle className="text-sm font-black text-pink-600 uppercase tracking-wider">Clinical Context</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <p className="text-sm text-pink-900/60 leading-relaxed font-medium italic">
                The AI identified "{patient.shap_summary.feature_importance[0]?.feature}" as the primary driver for this severity assessment. 
                Verify findings with physical examination before finalizing treatment plan.
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

'use client'

import { useState, useEffect } from 'react'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { 
  BrainCircuit, 
  Upload, 
  Download, 
  RefreshCcw, 
  CheckCircle2, 
  AlertCircle,
  FileSpreadsheet,
  History
} from 'lucide-react'
import { toast } from 'sonner'
import { createClient } from '@/utils/supabase/client'
import { useSocket } from '@/hooks/use-socket'

export default function SettingsPage() {
  const [file, setFile] = useState<File | null>(null)
  const [training, setTraining] = useState(false)
  const [role, setRole] = useState<string | null>(null)
  const { socket } = useSocket()

  useEffect(() => {
    const checkRole = async () => {
      const supabase = createClient()
      const { data: { user } } = await supabase.auth.getUser()
      setRole(user?.user_metadata?.role || null)
    }
    checkRole()
  }, [])

  // Listen for background training completion via WebSockets
  useEffect(() => {
    if (!socket) return

    socket.on('model:retrain_status', (data: { status: string, message?: string }) => {
      if (data.status === 'success') {
        setTraining(false)
        setFile(null)
        toast.success('Model Retrained Successfully', {
          description: data.message || 'The AI model has been hot-swapped and is now live.',
          duration: 6000
        })
      } else if (data.status === 'error') {
        setTraining(false)
        toast.error('Retraining Failed', {
          description: data.message || 'An error occurred during training.'
        })
      }
    })

    return () => {
      socket.off('model:retrain_status')
    }
  }, [socket])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0]
    if (selected && selected.name.endsWith('.csv')) {
      setFile(selected)
    } else {
      toast.error('Invalid File', { description: 'Please select a valid CSV file.' })
    }
  }

  const handleRetrain = async () => {
    if (!file) return

    setTraining(true)
    const formData = new FormData()
    formData.append('file', file)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      const response = await fetch('/api/v1/admin/retrain', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${session?.access_token}`
        },
        body: formData
      })

      const data = await response.json()

      if (response.ok) {
        toast.info('Training Started', {
          description: 'The dataset is being processed in the background.'
        })
      } else {
        setTraining(false)
        toast.error('Failed to Start', { description: data.message || 'Unknown error' })
      }
    } catch (error) {
      setTraining(false)
      toast.error('Network Error', { description: 'Could not connect to training server.' })
    }
  }

  const downloadTemplate = () => {
    // We'll just define the content here to keep it simple and direct
    const content = "age,gender,temperature,heart_rate,respiratory_rate,systolic_bp,diastolic_bp,pain_scale,immediate_triage,arrival_by_ems,asthma,cancer,ckd,copd,chf,cad,diabetes_type1,diabetes_type2,esrd,htn,obesity,osa,severity\n"
    const blob = new Blob([content], { type: 'text/csv' })
    const url = window.URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = 'training_template.csv'
    a.click()
  }

  if (role && role !== 'Admin') {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <div className="text-center space-y-4">
          <AlertCircle className="w-12 h-12 text-slate-300 mx-auto" />
          <h2 className="text-xl font-bold text-slate-900">Access Restricted</h2>
          <p className="text-slate-500">Only system administrators can modify model settings.</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-10 animate-in fade-in slide-in-from-bottom-4 duration-700">
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-blue-600 font-bold uppercase tracking-widest text-[10px] mb-2">
            <div className="w-1.5 h-1.5 rounded-full bg-blue-600" />
            System Administration
          </div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight">System <span className="text-blue-600">Configuration</span></h1>
          <p className="text-slate-500 font-medium">Manage hospital infrastructure, AI lifecycle, and staff loads.</p>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        <div className="space-y-8">
          {/* AI Model Life Cycle */}
          <Card className="border-slate-100 shadow-sm bg-white overflow-hidden overflow-hidden relative">
            {training && (
              <div className="absolute inset-0 bg-white/60 backdrop-blur-[2px] z-10 flex flex-col items-center justify-center space-y-4">
                <RefreshCcw className="w-10 h-10 text-blue-600 animate-spin" />
                <div className="text-center">
                  <p className="text-lg font-bold text-slate-900">Training in Progress</p>
                  <p className="text-sm text-slate-500">Wait for background completion...</p>
                </div>
              </div>
            )}
            <CardHeader className="bg-slate-50/50 border-b border-slate-50 py-6">
              <div className="flex items-center gap-4">
                <div className="w-12 h-12 bg-blue-600 rounded-2xl flex items-center justify-center shadow-lg shadow-blue-200">
                  <BrainCircuit className="text-white w-6 h-6" />
                </div>
                <div>
                  <CardTitle className="text-xl font-black text-slate-900">AI Model <span className="text-blue-600">Lifecycle</span></CardTitle>
                  <p className="text-xs text-slate-400 font-bold uppercase tracking-widest">Model Version: 1.2.4-stable</p>
                </div>
              </div>
            </CardHeader>
            <CardContent className="p-8 space-y-8">
              <div className="space-y-4">
                <h3 className="text-sm font-bold text-slate-900 uppercase tracking-widest flex items-center gap-2">
                  <Upload className="w-4 h-4 text-blue-600" />
                  Retrain Classifier
                </h3>
                <p className="text-sm text-slate-500 leading-relaxed">
                  Upload a clean clinical dataset (CSV) to update the XGBoost severity model. 
                  Kyro will backup the current model and hot-swap the new one instantly upon success.
                </p>
                
                <div className="p-6 border-2 border-dashed border-slate-100 rounded-2xl bg-slate-50/30 flex flex-col items-center justify-center space-y-4 transition-colors hover:border-blue-100 hover:bg-blue-50/10">
                  <FileSpreadsheet className="w-8 h-8 text-slate-300" />
                  <div className="text-center">
                    <p className="text-sm font-bold text-slate-700">{file ? file.name : 'Select training data CSV'}</p>
                    <p className="text-[10px] text-slate-400 uppercase tracking-widest mt-1">Maximum 50MB per file</p>
                  </div>
                  <Input 
                    type="file" 
                    accept=".csv" 
                    className="hidden" 
                    id="csv-upload" 
                    onChange={handleFileChange}
                    disabled={training}
                  />
                  <Button 
                    variant="outline" 
                    className="rounded-xl font-bold text-xs uppercase tracking-widest px-6"
                    onClick={() => document.getElementById('csv-upload')?.click()}
                    disabled={training}
                  >
                    Choose File
                  </Button>
                </div>

                <div className="flex items-center gap-4">
                  <Button 
                    className="flex-1 rounded-xl bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-200 h-12 font-bold transition-all disabled:opacity-50"
                    onClick={handleRetrain}
                    disabled={!file || training}
                  >
                    Start Training Pipeline
                  </Button>
                  <Button 
                    variant="ghost" 
                    className="rounded-xl font-bold text-slate-500 hover:text-blue-600 hover:bg-blue-50 h-12"
                    onClick={downloadTemplate}
                  >
                    <Download className="w-5 h-5" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>

        <div className="space-y-8">
          {/* System Maintenance */}
          <Card className="border-slate-100 shadow-sm bg-white overflow-hidden">
            <CardHeader className="py-6 border-b border-slate-50">
              <CardTitle className="text-lg font-bold text-slate-900 flex items-center gap-2">
                <RefreshCcw className="w-5 h-5 text-pink-600" />
                Staff Infrastructure
              </CardTitle>
            </CardHeader>
            <CardContent className="p-8 space-y-6">
              <div className="space-y-2">
                <p className="text-sm font-bold text-slate-700">Global Load Reset</p>
                <p className="text-sm text-slate-500 leading-relaxed">
                  In case of system desync, you can force all doctor loads to zero. This should only be used during off-peak hours.
                </p>
                <Button variant="outline" className="w-full rounded-xl text-pink-600 border-pink-100 hover:bg-pink-50 h-11 font-bold">
                  Force Reset Loads
                </Button>
              </div>
              
              <div className="pt-6 border-t border-slate-50 space-y-2">
                <p className="text-sm font-bold text-slate-700">Cache Maintenance</p>
                <p className="text-sm text-slate-500 leading-relaxed">
                  Clear the Redis cache for all triage predictions.
                </p>
                <Button variant="ghost" className="w-full rounded-xl text-slate-400 hover:text-slate-600 hover:bg-slate-50 h-11 font-bold">
                  Flush AI Cache
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Model Status Card */}
          <Card className="border-slate-100 shadow-sm bg-gradient-to-br from-slate-900 to-slate-800 text-white overflow-hidden">
            <CardContent className="p-8 space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <div className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse" />
                  <p className="text-xs font-bold uppercase tracking-widest text-slate-400">System Healthy</p>
                </div>
                <History className="w-5 h-5 text-slate-500" />
              </div>
              
              <div className="space-y-1">
                <h4 className="text-3xl font-black tracking-tighter">100% <span className="text-blue-400">Uptime</span></h4>
                <p className="text-xs font-bold text-slate-500 uppercase tracking-widest">Inference engine: ACTIVE</p>
              </div>
              
              <div className="flex items-center gap-4 pt-4">
                <div className="flex-1 p-4 bg-white/5 rounded-2xl border border-white/10">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Latency</p>
                  <p className="text-xl font-black">24ms</p>
                </div>
                <div className="flex-1 p-4 bg-white/5 rounded-2xl border border-white/10">
                  <p className="text-[10px] font-bold text-slate-400 uppercase tracking-widest mb-1">Throughput</p>
                  <p className="text-xl font-black">1.2k/hr</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  )
}

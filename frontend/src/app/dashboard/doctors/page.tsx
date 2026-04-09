'use client'

import { useState, useEffect } from 'react'
import { DoctorPanel } from '@/components/dashboard/DoctorPanel'
import { Button } from '@/components/ui/button'
import { DoctorForm } from '@/components/dashboard/DoctorForm'
import { Card } from '@/components/ui/card'
import { Plus, Users, X } from 'lucide-react'
import { createClient } from '@/utils/supabase/client'

export default function DoctorsPage() {
  const [showAddForm, setShowAddForm] = useState(false)
  const [role, setRole] = useState<string | null>(null)

  useEffect(() => {
    const checkRole = async () => {
      const supabase = createClient()
      const { data: { user } } = await supabase.auth.getUser()
      setRole(user?.user_metadata?.role || null)
    }
    checkRole()
  }, [])

  const isAdmin = role === 'Admin'

  return (
    <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-700">
      {/* Add Staff Modal Overlay */}
      {showAddForm && (
        <div className="fixed inset-0 bg-slate-900/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-lg shadow-2xl border-slate-100 bg-white">
            <div className="p-6 border-b border-slate-50 flex justify-between items-center bg-slate-50/50">
              <div>
                <h3 className="text-xl font-bold text-slate-900">Register New Staff</h3>
                <p className="text-sm text-slate-400">Add a practitioner to the hospital registry</p>
              </div>
              <Button variant="ghost" className="rounded-full w-10 h-10 p-0" onClick={() => setShowAddForm(false)}>
                <X className="w-5 h-5 text-slate-400" />
              </Button>
            </div>
            <div className="p-8">
              <DoctorForm 
                onSuccess={() => setShowAddForm(false)}
                onCancel={() => setShowAddForm(false)}
              />
            </div>
          </Card>
        </div>
      )}

      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-2 text-blue-600 font-bold uppercase tracking-widest text-[10px] mb-2">
            <div className="w-1.5 h-1.5 rounded-full bg-blue-600" />
            Medical Staff Registry
          </div>
          <h1 className="text-3xl font-black text-slate-900 tracking-tight">On-Duty <span className="text-blue-600">Staff</span></h1>
          <p className="text-slate-500 font-medium">Monitoring surgical load and staff availability.</p>
        </div>
        
        {isAdmin && (
          <Button 
            onClick={() => setShowAddForm(true)}
            className="rounded-xl bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-200 h-12 font-bold gap-2 px-6"
          >
            <Plus className="w-5 h-5" />
            Add Staff Member
          </Button>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <div className="lg:col-span-1">
          <DoctorPanel />
        </div>
        
        <div className="lg:col-span-2 space-y-6">
          <Card className="border-slate-100 shadow-sm p-8 bg-slate-50/30 border-2 border-dashed flex flex-col items-center justify-center text-center space-y-4">
            <Users className="w-12 h-12 text-slate-200" />
            <div>
              <h3 className="text-slate-900 font-bold">Registry Statistics</h3>
              <p className="text-sm text-slate-400 max-w-xs mx-auto">
                Detailed surgical logs and performance metrics will appear here in the next phase.
              </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  )
}

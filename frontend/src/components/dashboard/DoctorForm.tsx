'use client'

import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { 
  Select, 
  SelectContent, 
  SelectItem, 
  SelectTrigger, 
  SelectValue 
} from '@/components/ui/select'
import { Doctor } from '@/types/dashboard'
import { toast } from 'sonner'
import { createClient } from '@/utils/supabase/client'
import { Stethoscope, Users, Battery, ShieldCheck } from 'lucide-react'

interface DoctorFormProps {
  doctor?: Doctor
  onSuccess: () => void
  onCancel: () => void
}

const SPECIALIZATIONS = [
  "Emergency Medicine",
  "Trauma Surgery",
  "Cardiology",
  "Neurology",
  "Internal Medicine",
  "Orthopedics",
  "Pediatrics",
  "Radiology",
  "General Practice"
]

export function DoctorForm({ doctor, onSuccess, onCancel }: DoctorFormProps) {
  const [loading, setLoading] = useState(false)
  const isEditing = !!doctor

  const [formData, setFormData] = useState({
    name: doctor?.name || '',
    specialization: doctor?.specialization || '',
    max_capacity: doctor?.max_capacity || 10,
    is_available: doctor?.is_available ?? true
  })

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setLoading(true)

    try {
      const supabase = createClient()
      const { data: { session } } = await supabase.auth.getSession()

      const endpoint = isEditing ? `/api/doctors/${doctor.id}` : '/api/doctors'
      const method = isEditing ? 'PUT' : 'POST'

      const response = await fetch(endpoint, {
        method,
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${session?.access_token}`
        },
        body: JSON.stringify(formData)
      })

      const result = await response.json()

      if (response.ok) {
        toast.success(isEditing ? 'Staff updated' : 'Staff registered', {
          description: `${formData.name} is now ${isEditing ? 'updated' : 'active'} in the system.`
        })
        onSuccess()
      } else {
        toast.error('Operation failed', { description: result.message || 'Unknown error' })
      }
    } catch (error) {
      toast.error('Network Error', { description: 'Could not connect to the server.' })
    } finally {
      setLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-300">
      <div className="space-y-4">
        {/* Name Field */}
        <div className="space-y-2">
          <Label htmlFor="name" className="text-xs font-bold uppercase tracking-widest text-slate-400">Full Name</Label>
          <div className="relative">
            <Users className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input 
              id="name"
              placeholder="Dr. Jane Smith"
              className="pl-10 h-11 border-slate-100 focus:ring-blue-500/10 rounded-xl"
              value={formData.name}
              onChange={(e) => setFormData({...formData, name: e.target.value})}
              required
            />
          </div>
        </div>

        {/* Specialization Field */}
        <div className="space-y-2">
          <Label htmlFor="specialization" className="text-xs font-bold uppercase tracking-widest text-slate-400">Clinical Specialization</Label>
          <div className="relative">
            <Stethoscope className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 z-10" />
            <Select 
              value={formData.specialization} 
              onValueChange={(val) => setFormData({...formData, specialization: val || ''})}
            >
              <SelectTrigger className="pl-10 h-11 border-slate-100 rounded-xl">
                <SelectValue placeholder="Select Specialization" />
              </SelectTrigger>
              <SelectContent className="rounded-xl border-slate-100 shadow-xl">
                {SPECIALIZATIONS.map(spec => (
                  <SelectItem key={spec} value={spec} className="rounded-lg">{spec}</SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="grid grid-cols-2 gap-4">
          {/* Max Capacity */}
          <div className="space-y-2">
            <Label htmlFor="capacity" className="text-xs font-bold uppercase tracking-widest text-slate-400">Max Load</Label>
            <div className="relative">
              <Battery className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
              <Input 
                id="capacity"
                type="number"
                min="1"
                className="pl-10 h-11 border-slate-100 rounded-xl"
                value={formData.max_capacity}
                onChange={(e) => setFormData({...formData, max_capacity: parseInt(e.target.value)})}
                required
              />
            </div>
          </div>

          {/* Availability */}
          <div className="space-y-2">
            <Label className="text-xs font-bold uppercase tracking-widest text-slate-400">Status</Label>
            <div className="relative">
              <ShieldCheck className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 z-10" />
              <Select 
                value={formData.is_available ? 'true' : 'false'} 
                onValueChange={(val) => setFormData({...formData, is_available: val === 'true'})}
              >
                <SelectTrigger className="pl-10 h-11 border-slate-100 rounded-xl">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent className="rounded-xl border-slate-100 shadow-xl">
                  <SelectItem value="true" className="rounded-lg text-emerald-600 font-medium">On-Duty</SelectItem>
                  <SelectItem value="false" className="rounded-lg text-slate-400 font-medium">Off-Duty</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </div>
        </div>
      </div>

      <div className="flex gap-3 pt-4">
        <Button 
          type="button" 
          variant="outline" 
          className="flex-1 h-12 rounded-xl border-slate-100 font-bold text-slate-500"
          onClick={onCancel}
          disabled={loading}
        >
          Cancel
        </Button>
        <Button 
          type="submit" 
          className="flex-1 h-12 rounded-xl bg-blue-600 hover:bg-blue-700 shadow-lg shadow-blue-200 font-bold"
          disabled={loading}
        >
          {loading ? 'Processing...' : (isEditing ? 'Save Changes' : 'Register Staff')}
        </Button>
      </div>
    </form>
  )
}

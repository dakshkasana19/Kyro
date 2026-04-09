'use client'

import { DoctorPanel } from '@/components/dashboard/DoctorPanel'

export default function DoctorsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-black text-slate-900 tracking-tight">On-Duty <span className="text-blue-600">Staff</span></h1>
        <p className="text-slate-500 font-medium">Monitoring load and availability for the surgical team.</p>
      </div>
      <div className="max-w-md">
        <DoctorPanel />
      </div>
    </div>
  )
}

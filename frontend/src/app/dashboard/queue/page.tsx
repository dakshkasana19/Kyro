'use client'

import { QueueTable } from '@/components/dashboard/QueueTable'

export default function QueuePage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-black text-slate-900 tracking-tight">Triage <span className="text-pink-500">Queue</span></h1>
        <p className="text-slate-500 font-medium">Full priority list of patients awaiting attention.</p>
      </div>
      <QueueTable />
    </div>
  )
}

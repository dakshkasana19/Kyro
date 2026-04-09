'use client'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'

export default function SettingsPage() {
  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-3xl font-black text-slate-900 tracking-tight">System <span className="text-slate-400">Settings</span></h1>
        <p className="text-slate-500 font-medium">Manage hospital configurations and AI model thresholds.</p>
      </div>

      <div className="grid gap-6 max-w-2xl">
        <Card className="border-slate-100 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">AI Triage Thresholds</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-400">Configure the confidence scores required for automatic assignments.</p>
            <Button className="bg-blue-600 hover:bg-blue-700">Update Parameters</Button>
          </CardContent>
        </Card>

        <Card className="border-slate-100 shadow-sm">
          <CardHeader>
            <CardTitle className="text-lg">Staff Availability</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm text-slate-400">Toggle active status for all medical staff.</p>
            <Button variant="outline" className="text-pink-600 border-pink-100 hover:bg-pink-50">Force Reset Loads</Button>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

'use client'

import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  ResponsiveContainer, 
  Cell,
  ReferenceLine
} from 'recharts'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Info } from 'lucide-react'

interface ShapFeature {
  feature: string
  shap_value: number
}

interface ShapChartProps {
  data: ShapFeature[]
  title?: string
}

export function ShapChart({ data, title = 'Triage Decision Factors' }: ShapChartProps) {
  // Sort by absolute value and take top 10
  const sortedData = [...data]
    .sort((a, b) => Math.abs(b.shap_value) - Math.abs(a.shap_value))
    .slice(0, 10)
    .reverse() // Reverse for horizontal layout

  const CustomTooltip = ({ active, payload }: any) => {
    if (active && payload && payload.length) {
      const { feature, shap_value } = payload[0].payload
      return (
        <div className="bg-white p-3 border border-slate-100 shadow-xl rounded-xl">
          <p className="text-xs font-bold text-slate-500 uppercase tracking-wider mb-1">{feature}</p>
          <p className={`text-lg font-black ${shap_value > 0 ? 'text-pink-600' : 'text-blue-600'}`}>
            {shap_value > 0 ? '+' : ''}{shap_value.toFixed(4)}
          </p>
          <p className="text-[10px] text-slate-400 font-medium">
            {shap_value > 0 
              ? 'Pushed prediction towards higher severity' 
              : 'Pushed prediction towards lower severity'}
          </p>
        </div>
      )
    }
    return null
  }

  return (
    <Card className="border-slate-100 shadow-sm bg-white overflow-hidden">
      <CardHeader className="pb-2 border-b border-slate-50">
        <div className="flex items-center justify-between">
          <CardTitle className="text-sm font-bold text-slate-900 flex items-center gap-2">
            <Info className="w-4 h-4 text-blue-500" />
            {title}
          </CardTitle>
          <div className="flex items-center gap-3 text-[10px] font-bold uppercase tracking-tight">
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-pink-500" />
              <span className="text-slate-400">Increase Risk</span>
            </div>
            <div className="flex items-center gap-1">
              <div className="w-2 h-2 rounded-full bg-blue-500" />
              <span className="text-slate-400">Protective</span>
            </div>
          </div>
        </div>
      </CardHeader>
      <CardContent className="pt-6">
        <div className="h-[350px] w-full">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={sortedData}
              layout="vertical"
              margin={{ top: 5, right: 30, left: 40, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" horizontal={false} stroke="#f1f5f9" />
              <XAxis type="number" hide />
              <YAxis 
                dataKey="feature" 
                type="category" 
                width={120}
                tick={{ fontSize: 10, fontWeight: 700, fill: '#64748b' }}
                axisLine={false}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} cursor={{ fill: '#f8fafc' }} />
              <ReferenceLine x={0} stroke="#cbd5e1" />
              <Bar 
                dataKey="shap_value" 
                radius={[0, 4, 4, 0]} 
                barSize={20}
              >
                {sortedData.map((entry, index) => (
                  <Cell 
                    key={`cell-${index}`} 
                    fill={entry.shap_value > 0 ? '#ec4899' : '#3b82f6'} 
                  />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <p className="text-center text-[10px] font-bold text-slate-400 mt-4 uppercase tracking-widest leading-relaxed">
          AI Feature Importance (Top 10) • <span className="text-blue-600">SHAP Analysis</span>
        </p>
      </CardContent>
    </Card>
  )
}

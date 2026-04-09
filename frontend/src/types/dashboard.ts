export interface Patient {
  id: string
  name: string
  age: number
  gender: string
  symptoms: string[]
  vitals: {
    temperature: number
    heart_rate: number
    respiratory_rate: number
    systolic_bp: number
    diastolic_bp: number
    pain_scale: number
  }
  history?: Record<string, any>
  created_at: string
}

export interface Doctor {
  id: string
  name: string
  specialization: string
  max_capacity: number
  current_load: number
  is_available: boolean
}

export interface TriageQueueItem {
  patient_id: string
  patient_name: string
  severity_level: number
  severity_label: string
  confidence_score: number
  assigned_doctor: string | null
  created_at: string
}

export interface ApiResponse<T> {
  data: T
  message?: string
  status: number
}

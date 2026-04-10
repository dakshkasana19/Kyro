'use client'

import { useFormStatus } from 'react-dom'
import Link from 'next/link'
import { signup } from '@/app/auth/actions'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Loader2 } from 'lucide-react'

function SubmitButton() {
  const { pending } = useFormStatus()
  
  return (
    <Button 
      type="submit" 
      disabled={pending}
      className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold h-12 shadow-lg shadow-blue-500/20 transition-all active:scale-[0.98] rounded-xl"
    >
      {pending ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Creating Account...
        </>
      ) : 'Create Account'}
    </Button>
  )
}

interface SignupFormProps {
  error?: string
}

export function SignupForm({ error }: SignupFormProps) {
  return (
    <Card className="w-full max-w-md z-10 border-slate-100 bg-white shadow-xl">
      <CardHeader className="space-y-1 text-center font-bold">
        <CardTitle className="text-3xl font-black tracking-tight text-blue-600 uppercase">Staff Registration</CardTitle>
        <CardDescription className="text-slate-500 font-medium tracking-tight">
          Create your account to join Kyro Health.
        </CardDescription>
      </CardHeader>
      <form action={signup}>
        <CardContent className="space-y-4">
          {error && (
            <div className="p-3 rounded-xl bg-rose-50 border border-rose-100 text-rose-600 text-sm font-bold animate-in fade-in zoom-in-95">
              {error}
            </div>
          )}
          
          <div className="space-y-2">
            <Label htmlFor="email" className="text-slate-700 font-bold uppercase text-[11px] tracking-wider">Email Address</Label>
            <Input 
              id="email" 
              name="email" 
              type="email" 
              placeholder="doctor@kyro.health" 
              required 
              className="bg-slate-50 border-slate-200 text-slate-900 focus:ring-blue-500 rounded-xl"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="password" className="text-slate-700 font-bold uppercase text-[11px] tracking-wider">Password</Label>
            <Input 
              id="password" 
              name="password" 
              type="password" 
              required 
              className="bg-slate-50 border-slate-200 text-slate-900 focus:ring-blue-500 rounded-xl"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="role" className="text-slate-700 font-bold uppercase text-[11px] tracking-wider">Professional Role</Label>
            <Select name="role" required defaultValue="Nurse">
              <SelectTrigger className="bg-slate-50 border-slate-200 text-slate-900 rounded-xl">
                <SelectValue placeholder="Select your role" />
              </SelectTrigger>
              <SelectContent className="bg-white border-slate-100 text-slate-900 rounded-xl">
                <SelectItem value="Admin">Administrator</SelectItem>
                <SelectItem value="Doctor">Doctor / Surgeon</SelectItem>
                <SelectItem value="Nurse">Medical Nurse</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </CardContent>
        <CardFooter className="flex flex-col space-y-4 pt-4">
          <SubmitButton />
          <div className="text-center text-sm text-slate-500 font-medium">
            Already have an account?{' '}
            <Link href="/auth/login" className="text-blue-600 hover:underline font-bold transition-colors">
              Sign in
            </Link>
          </div>
        </CardFooter>
      </form>
    </Card>
  )
}

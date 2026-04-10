'use client'

import { useFormStatus } from 'react-dom'
import Link from 'next/link'
import { login } from '@/app/auth/actions'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'
import { Loader2 } from 'lucide-react'

function SubmitButton() {
  const { pending } = useFormStatus()
  
  return (
    <Button 
      type="submit" 
      disabled={pending}
      className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold h-12 shadow-lg shadow-blue-200 transition-all active:scale-[0.98] rounded-xl"
    >
      {pending ? (
        <>
          <Loader2 className="mr-2 h-4 w-4 animate-spin" />
          Authenticating...
        </>
      ) : 'Sign In'}
    </Button>
  )
}

interface LoginFormProps {
  message?: string
  error?: string
}

export function LoginForm({ message, error }: LoginFormProps) {
  return (
    <Card className="w-full max-w-md z-10 border-slate-100 bg-white shadow-xl">
      <CardHeader className="space-y-1 text-center font-bold">
        <CardTitle className="text-3xl font-black tracking-tight text-blue-600">Welcome Back</CardTitle>
        <CardDescription className="text-slate-500 font-medium tracking-tight">
          Enter your credentials to access Kyro Health.
        </CardDescription>
      </CardHeader>
      <form action={login}>
        <CardContent className="space-y-4">
          {message && (
            <div className="p-3 rounded-xl bg-blue-50 border border-blue-100 text-blue-600 text-sm font-bold animate-in fade-in zoom-in-95">
              {message}
            </div>
          )}
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
        </CardContent>
        <CardFooter className="flex flex-col space-y-4 pt-4">
          <SubmitButton />
          <div className="text-center text-sm text-slate-500 font-medium">
            New here?{' '}
            <Link href="/auth/signup" className="text-blue-600 hover:underline font-bold transition-colors">
              Create an account
            </Link>
          </div>
        </CardFooter>
      </form>
    </Card>
  )
}

import Link from 'next/link'
import { login } from '../actions'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card'

export default async function LoginPage(props: {
  searchParams: Promise<{ message: string; error: string }>
}) {
  const searchParams = await props.searchParams

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col items-center justify-center p-4 relative overflow-hidden text-slate-900">
      {/* Background decorations */}
      <div className="absolute inset-0 bg-[linear-gradient(to_right,#e0e7ff_1px,transparent_1px),linear-gradient(to_bottom,#e0e7ff_1px,transparent_1px)] bg-[size:4rem_4rem] [mask-image:radial-gradient(ellipse_60%_50%_at_50%_0%,#000_70%,transparent_100%)] opacity-20"></div>
      <div className="absolute top-0 left-0 w-96 h-96 bg-blue-400 rounded-full mix-blend-multiply filter blur-[128px] opacity-10 pointer-events-none animation-delay-4000"></div>
      <div className="absolute bottom-0 right-0 w-96 h-96 bg-pink-400 rounded-full mix-blend-multiply filter blur-[128px] opacity-10 pointer-events-none"></div>
      
      <Card className="w-full max-w-md z-10 border-slate-100 bg-white shadow-xl">
        <CardHeader className="space-y-1 text-center font-bold">
          <CardTitle className="text-3xl font-black tracking-tight text-blue-600">Welcome Back</CardTitle>
          <CardDescription className="text-slate-500 font-medium tracking-tight">
            Enter your credentials to access Kyro Health.
          </CardDescription>
        </CardHeader>
        <form action={login}>
          <CardContent className="space-y-4">
            {searchParams.message && (
              <div className="p-3 rounded-xl bg-blue-50 border border-blue-100 text-blue-600 text-sm font-bold animate-in fade-in zoom-in-95">
                {searchParams.message}
              </div>
            )}
            {searchParams.error && (
              <div className="p-3 rounded-xl bg-rose-50 border border-rose-100 text-rose-600 text-sm font-bold animate-in fade-in zoom-in-95">
                {searchParams.error}
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
            <Button className="w-full bg-blue-600 hover:bg-blue-700 text-white font-bold h-12 shadow-lg shadow-blue-200 transition-all active:scale-[0.98] rounded-xl">
              Sign In
            </Button>
            <div className="text-center text-sm text-slate-500 font-medium">
              New here?{' '}
              <Link href="/auth/signup" className="text-blue-600 hover:underline font-bold transition-colors">
                Create an account
              </Link>
            </div>
          </CardFooter>
        </form>
      </Card>
    </div>
  )
}

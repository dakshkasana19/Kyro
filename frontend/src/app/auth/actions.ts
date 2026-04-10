'use server'

import { revalidatePath } from 'next/cache'
import { redirect } from 'next/navigation'
import { createClient } from '@/utils/supabase/server'

export async function login(formData: FormData) {
  const supabase = await createClient()

  const data = {
    email: formData.get('email') as string,
    password: formData.get('password') as string,
  }

  console.log(`>>> [AUTH] Login Attempt: ${data.email}`)
  const { error } = await supabase.auth.signInWithPassword(data)

  if (error) {
    console.error(`>>> [AUTH] Login Failed: ${error.message}`)
    redirect('/auth/login?error=' + encodeURIComponent(error.message))
  }

  console.log(`>>> [AUTH] Login Success: ${data.email}. Redirecting...`)
  revalidatePath('/', 'layout')
  redirect('/')
}

export async function signup(formData: FormData) {
  const supabase = await createClient()

  const email = formData.get('email') as string
  const password = formData.get('password') as string
  const role = formData.get('role') as string

  console.log(`>>> [AUTH] Signup Attempt: ${email} (Role: ${role})`)
  const { error } = await supabase.auth.signUp({
    email,
    password,
    options: {
      data: {
        role: role,
      },
    },
  })

  if (error) {
    console.error(`>>> [AUTH] Signup Failed: ${error.message}`)
    redirect('/auth/signup?error=' + encodeURIComponent(error.message))
  }

  console.log(`>>> [AUTH] Signup Success: ${email}. Redirecting to login...`)
  revalidatePath('/', 'layout')
  redirect('/auth/login?message=' + encodeURIComponent('Check your email to continue the sign in process.'))
}

export async function logout() {
  const supabase = await createClient()
  await supabase.auth.signOut()
  revalidatePath('/', 'layout')
  redirect('/auth/login')
}

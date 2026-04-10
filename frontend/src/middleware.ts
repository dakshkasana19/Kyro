import { type NextRequest, NextResponse } from 'next/server'
import { updateSession } from '@/utils/supabase/middleware'
import { createClient } from '@/utils/supabase/server'

export async function middleware(request: NextRequest) {
  const { supabaseResponse, user } = await updateSession(request)
  
  const isAuthPage = request.nextUrl.pathname.startsWith('/auth')
  const isProtectedPage = 
    request.nextUrl.pathname.startsWith('/intake') || 
    request.nextUrl.pathname.startsWith('/dashboard') ||
    request.nextUrl.pathname.startsWith('/doctor') ||
    request.nextUrl.pathname === '/'

  const role = user?.user_metadata?.role

  // --- Role Based Access Control ---
  if (user) {
    if (isAuthPage) {
        return NextResponse.redirect(new URL('/', request.url))
    }

    const path = request.nextUrl.pathname
    
    // Admin only routes
    if (path.startsWith('/dashboard/admin') && role !== 'Admin') {
      return NextResponse.redirect(new URL('/dashboard', request.url))
    }

    // Nurse/Admin only routes for patient intake
    if (path.startsWith('/intake') && !['Admin', 'Nurse'].includes(role)) {
      return NextResponse.redirect(new URL('/dashboard', request.url))
    }
  }

  return supabaseResponse
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * Feel free to modify this pattern to include more paths.
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}

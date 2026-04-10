import { createClient } from '@supabase/supabase-js'
import dotenv from 'dotenv'

dotenv.config()

const supabaseUrl = process.env.SUPABASE_URL
const supabaseServiceKey = process.env.SUPABASE_KEY

if (!supabaseUrl || !supabaseServiceKey) {
  console.error('Missing SUPABASE_URL or SUPABASE_KEY in .env')
  process.exit(1)
}

const supabase = createClient(supabaseUrl, supabaseServiceKey, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
})

async function createAdmin() {
  const email = 'admin@kyro.health'
  const password = 'Password123!'
  
  console.log(`>>> Creating pre-confirmed admin: ${email}`)
  
  const { data, error } = await supabase.auth.admin.createUser({
    email,
    password,
    email_confirm: true,
    user_metadata: { role: 'Admin' }
  })

  if (error) {
    if (error.message.includes('already registered')) {
      console.log('>>> Admin user already exists.')
      
      // Update metadata just in case
      const { data: userList } = await supabase.auth.admin.listUsers()
      const user = userList.users.find(u => u.email === email)
      if (user) {
        await supabase.auth.admin.updateUserById(user.id, {
          user_metadata: { role: 'Admin' }
        })
        console.log('>>> Metadata updated to Admin role.')
      }
    } else {
      console.error('>>> Error creating admin:', error.message)
    }
  } else {
    console.log('>>> Admin user created successfully.')
  }
}

createAdmin()

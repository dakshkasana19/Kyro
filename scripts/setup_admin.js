const { createClient } = require('./frontend/node_modules/@supabase/supabase-js');
const dotenv = require('./frontend/node_modules/dotenv');

dotenv.config();

const supabaseUrl = process.env.SUPABASE_URL;
const supabaseServiceKey = process.env.SUPABASE_KEY;

if (!supabaseUrl || !supabaseServiceKey) {
  console.error('Missing SUPABASE_URL or SUPABASE_KEY in .env');
  process.exit(1);
}

const supabase = createClient(supabaseUrl, supabaseServiceKey, {
  auth: {
    autoRefreshToken: false,
    persistSession: false
  }
});

async function createAdmin() {
  const email = 'admin@kyro.health';
  const password = 'Password123!';
  
  console.log(`>>> Creating pre-confirmed admin: ${email}`);
  
  const { data, error } = await supabase.auth.admin.createUser({
    email,
    password,
    email_confirm: true,
    user_metadata: { role: 'Admin' }
  });

  if (error) {
    if (error.message.includes('already registered')) {
      console.log('>>> Admin user already exists.');
    } else {
      console.error('>>> Error creating admin:', error.message);
    }
  } else {
    console.log('>>> Admin user created successfully.');
  }
}

createAdmin();

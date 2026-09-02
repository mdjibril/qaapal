import { createClient } from "https://esm.sh/@supabase/supabase-js@2"

Deno.serve(async (req: Request) => {
  // Selar sends a POST request
  if (req.method !== 'POST') {
    return new Response('Method Not Allowed', { status: 405 })
  }

  try {
    // 0. Security Check: Verify the secret from our Google Apps Script Bridge
    const authHeader = req.headers.get('x-bridge-secret')
    const expectedSecret = Deno.env.get('BRIDGE_SECRET')
    if (!authHeader || authHeader !== expectedSecret) {
      return new Response('Unauthorized', { status: 401 })
    }

    const payload = await req.json()
    const source = payload.source || "unknown"
    console.log(`Received Webhook from ${source}:`, payload)

    // 1. Basic Validation
    // Selar status usually returns "success" for completed payments
    if (payload.status !== 'success') {
      return new Response('Ignored: Transaction not successful', { status: 200 })
    }

    const customerEmail = payload.customer?.email
    if (!customerEmail) {
      return new Response('Error: No customer email found', { status: 400 })
    }

    // 2. Initialize Supabase Admin Client
    // We use service role key to bypass RLS
    const supabaseAdmin = createClient(
      Deno.env.get('SUPABASE_URL') ?? '',
      Deno.env.get('SUPABASE_SERVICE_ROLE_KEY') ?? ''
    )

    // 3. Find the organization linked to this email
    // We look up via user_profiles -> org_id
    const { data: profile, error: profileError } = await supabaseAdmin
      .from('user_profiles')
      .select('org_id')
      .ilike('email', customerEmail)
      .single()

    if (profileError || !profile?.org_id) {
      console.error(`Org not found for email: ${customerEmail}`, profileError)
      return new Response('User/Org not found', { status: 404 })
    }

    const orgId = profile.org_id

    // 4. Map the purchased product to a subscription tier
    const product = (payload.product || "").toLowerCase()

    // Credit-pack sales (20/150/400 Report) must not change the subscription tier.
    if (product.includes("report")) {
      return new Response('Ignored: credit pack sale (tier unchanged)', { status: 200 })
    }

    let tier = "platform_pass"
    if (product.includes("lifetime")) {
      tier = "lifetime"
    } else if (product.includes("platform") || product.includes("pass")) {
      tier = "platform_pass"
    } else {
      console.warn(`Unknown product, ignoring: ${payload.product}`)
      return new Response('Ignored: unknown product', { status: 200 })
    }

    // 5. Update the Organization's Subscription
    const { error: updateError } = await supabaseAdmin
      .from('organizations')
      .update({
        subscription_tier: tier,
        subscription_start_date: new Date().toISOString()
      })
      .eq('id', orgId)

    if (updateError) {
      console.error("Database update failed:", updateError)
      return new Response('Internal Server Error', { status: 500 })
    }

    console.log(`Successfully upgraded Org ${orgId} via Selar payment.`)
    
    return new Response(JSON.stringify({ message: 'Success' }), {
      headers: { 'Content-Type': 'application/json' },
      status: 200,
    })

  } catch (err) {
    const errorMessage = err instanceof Error ? err.message : String(err)
    console.error("Webhook processing error:", errorMessage)
    return new Response('Bad Request', { status: 400 })
  }
})
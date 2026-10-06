app_name        = "nest_demo"
app_title       = "Nest Demo"
app_publisher   = "NestERP / Syncflo"
app_description = "Demo-site switch: pick a business type and the demo login sees only what suits that prospect."
app_email       = "ops@syncflo.co.za"
app_license     = "MIT"
app_icon        = "octicon octicon-briefcase"

# For the demo site only. Never install on a client site: applying a business
# type replaces the demo login's roles and restricts app icons site-wide.

# Seed the starter business types. Only missing ones are added, so changes made
# on the site are never overwritten.
after_install = "nest_demo.install.seed_business_types"
after_migrate = "nest_demo.install.seed_business_types"

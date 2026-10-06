# Nest Demo

The demo-site switch. Pick a **business type** and the demo login sees only
what suits that prospect: its modules, its apps, its home page and its demo
data. One click to apply, one click to reset. Nothing is uninstalled.

**Demo site only.** Applying a type replaces the demo login's roles and
restricts app icons site-wide. Never install on a client site.

Requires Frappe v16. Works with either Nest Home build (Gliphy or standard)
when installed, and without one (no home page is set then).

## Use it

1. Create a demo login once (a normal user, never an admin or a real person's
   account) and set its password.
2. **Demo Settings** → Demo Logins: add it. Save.
3. Pick **Show the Site As** → a business type → **Apply**.
4. Log in as the demo login. It lands on the type's home page.
5. Demo Data on the same screen: **Load** / **Remove** the sample data for
   that type. **Reset Site** puts every app icon back and switches the demo
   home page off.

## What a business type holds

- **Roles** the demo login gets (they replace its current roles).
- **Modules Shown**: everything else is hidden from the login (Core, Desk,
  Contacts, Setup and the Nest Home / Theme modules always stay).
- **Apps Shown**: app and folder icons on the desk. Every other one is
  restricted to System Manager while the type is applied, and restored on
  Reset or the next Apply.
- **Home page**: greeting, attention lists on/off, tiles (Add Tiles picks from
  the Nest Home tile library).
- **Demo Data**: which apps' sample data to offer (Add Demo Data).

What Apply maintains: one Role Profile, one Module Profile and one Nest Home
layout, each named **Nest Demo**, plus the demo logins' role and module
profiles. Admin accounts are refused as demo logins.

## Starter types

Shipped in `business_types.json` and added on install / migrate when missing:
Engineer-to-order manufacturer, Sales team with CRM, Retail with point of sale,
Manufacturer (make to stock), Wholesale and distribution. Anything a starter
names that the site doesn't have (an app not installed, a tile not created) is
left out. Existing types are never overwritten: to refresh a starter, delete
it and use **More → Reload Starter Types**. New types are added to the JSON
as the list grows.

## Offering demo data from an app

Add to the app's `hooks.py`:

```python
nest_demo_loaders = [
	{
		"key": "my_app",
		"label": "What it loads, in a few words",
		"load": "my_app.demo.load_demo",
		"remove": "my_app.demo.remove_demo",
		"is_loaded": "my_app.demo.is_loaded",  # optional, returns bool
	}
]
```

The functions take no arguments and run as the System Manager pressing the
button. Nest Projects is the first app to do this.

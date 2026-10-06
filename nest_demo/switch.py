"""The business-type switch: what the demo login sees, applied and undone in one step.

The switch maintains one Role Profile, one Module Profile and one Nest Home
layout, all named "Nest Demo", and points the demo login(s) at them. App icons
the type doesn't show are restricted to System Manager; their original roles
are kept so Reset (or the next Apply) puts them back exactly.
"""

import json

import frappe
from frappe import _
from frappe.utils import now_datetime

PROFILE = "Nest Demo"

# Modules every login needs, whatever the business type.
ALWAYS_SHOWN = {"Core", "Desk", "Contacts", "Setup", "Nest Theme", "Nest Home", "Nest Home Gliphy", "Nest Demo"}

# Nest Home comes in two builds with the same layout shape.
HOME_VARIANTS = (("Nest Home Gliphy Layout", "Nest Home Gliphy Tile"), ("Nest Home Layout", "Nest Home Tile"))

# Apps register their sample data with this hook (see README).
LOADER_HOOK = "nest_demo_loaders"


@frappe.whitelist()
def apply(business_type=None):
	frappe.only_for("System Manager")
	settings = frappe.get_single("Demo Settings")
	business_type = business_type or settings.business_type
	if not business_type:
		frappe.throw(_("Pick a business type first."))
	bt = frappe.get_doc("Business Type", business_type)
	users = [row.user for row in settings.demo_users]
	if not users:
		frappe.throw(_("Add the demo login(s) under Demo Logins first."))
	check_users(users)

	restore_icons(settings)
	ensure_role_profile([row.role for row in bt.roles])
	ensure_module_profile({row.module for row in bt.modules})
	hidden = hide_icons({row.icon for row in bt.apps})
	ensure_home(bt)
	for user in users:
		assign(user)

	settings.business_type = bt.name
	settings.applied_type = bt.name
	settings.applied_on = now_datetime()
	settings.applied_by = frappe.session.user
	settings.applied_state = json.dumps({"icons": hidden})
	settings.save(ignore_permissions=True)
	frappe.clear_cache()
	return status()


@frappe.whitelist()
def reset():
	"""Back to neutral: app icons as they were, the demo home layout off."""
	frappe.only_for("System Manager")
	settings = frappe.get_single("Demo Settings")
	restore_icons(settings)
	variant = home_variant()
	if variant and frappe.db.exists(variant[0], PROFILE):
		frappe.db.set_value(variant[0], PROFILE, "enabled", 0)
	settings.applied_type = None
	settings.applied_on = None
	settings.applied_by = None
	settings.applied_state = None
	settings.save(ignore_permissions=True)
	frappe.clear_cache()
	return status()


@frappe.whitelist()
def status():
	frappe.only_for("System Manager")
	settings = frappe.get_single("Demo Settings")
	loaders = registered_loaders()
	data = []
	if settings.applied_type:
		for row in frappe.get_all(
			"Business Type Data", filters={"parent": settings.applied_type}, fields=["loader"], order_by="idx asc"
		):
			entry = loaders.get(row.loader)
			if entry:
				data.append({"key": row.loader, "label": entry.get("label") or row.loader, "loaded": is_loaded(entry)})
	return {
		"applied_type": settings.applied_type,
		"applied_on": settings.applied_on,
		"applied_by": settings.applied_by,
		"users": [row.user for row in settings.demo_users],
		"data": data,
	}


@frappe.whitelist()
def run_loader(key, action):
	"""Load or remove one app's demo data from the switch."""
	frappe.only_for("System Manager")
	if action not in ("load", "remove"):
		frappe.throw(_("Unknown action {0}.").format(action))
	entry = registered_loaders().get(key)
	if not entry or not entry.get(action):
		frappe.throw(_("No demo data called {0} is installed.").format(key))
	frappe.get_attr(entry[action])()
	return status()


@frappe.whitelist()
def list_tiles():
	"""The Nest Home tile library, for the Business Type tile picker."""
	frappe.only_for("System Manager")
	variant = home_variant()
	if not variant:
		return []
	return frappe.get_all(
		variant[1],
		filters={"enabled": 1},
		fields=["name", "label", "description", "tile_group"],
		order_by="sort_order asc, label asc",
	)


@frappe.whitelist()
def list_loaders():
	frappe.only_for("System Manager")
	return [
		{"key": key, "label": entry.get("label") or key, "description": entry.get("description")}
		for key, entry in registered_loaders().items()
	]


def check_users(users):
	"""Applying replaces a login's roles, so never touch an admin or real account."""
	for user in users:
		if user in ("Administrator", "Guest") or user == frappe.session.user or "System Manager" in frappe.get_roles(user):
			frappe.throw(
				_("{0} can't be a demo login: applying a business type replaces its roles. Use a separate demo account.").format(
					user
				)
			)


def ensure_role_profile(roles):
	doc = singleton("Role Profile", {"role_profile": PROFILE})
	doc.set("roles", [{"role": role} for role in roles if frappe.db.exists("Role", role)])
	doc.save(ignore_permissions=True)


def ensure_module_profile(shown):
	keep = set(shown) | ALWAYS_SHOWN
	blocked = [m for m in frappe.get_all("Module Def", pluck="name", order_by="name asc") if m not in keep]
	doc = singleton("Module Profile", {"module_profile_name": PROFILE})
	doc.set("block_modules", [{"module": m} for m in blocked])
	doc.save(ignore_permissions=True)


def hide_icons(shown):
	"""Restricts every app and folder icon the type doesn't show; returns their original roles."""
	if not frappe.db.exists("DocType", "Desktop Icon"):
		return {}
	original = {}
	for name in frappe.get_all("Desktop Icon", filters={"icon_type": ["in", ["App", "Folder"]]}, pluck="name"):
		if name in shown:
			continue
		icon = frappe.get_doc("Desktop Icon", name)
		original[name] = [row.role for row in icon.roles]
		icon.set("roles", [{"role": "System Manager"}])
		icon.save(ignore_permissions=True)
	return original


def restore_icons(settings):
	state = json.loads(settings.applied_state or "{}")
	for name, roles in (state.get("icons") or {}).items():
		if not frappe.db.exists("Desktop Icon", name):
			continue
		icon = frappe.get_doc("Desktop Icon", name)
		icon.set("roles", [{"role": role} for role in roles])
		icon.save(ignore_permissions=True)
	settings.applied_state = None


def ensure_home(bt):
	variant = home_variant()
	if not variant:
		return
	layout_doctype, tile_doctype = variant
	doc = frappe.get_doc(layout_doctype, PROFILE) if frappe.db.exists(layout_doctype, PROFILE) else frappe.new_doc(layout_doctype)
	doc.update(
		{
			"layout_name": PROFILE,
			"enabled": 1,
			"priority": 100,
			"applies_to": "Role Profile",
			"role_profile": PROFILE,
			"greeting": bt.greeting,
			"show_list_a": bt.show_attention,
			"show_list_b": bt.show_attention,
			"show_list_c": bt.show_attention,
		}
	)
	doc.set("tiles", [{"tile": row.tile} for row in bt.tiles if frappe.db.exists(tile_doctype, row.tile)])
	doc.save(ignore_permissions=True)


def assign(user):
	doc = frappe.get_doc("User", user)
	doc.set("role_profiles", [{"role_profile": PROFILE}])
	doc.module_profile = PROFILE
	doc.save(ignore_permissions=True)


def singleton(doctype, values):
	name = next(iter(values.values()))
	if frappe.db.exists(doctype, name):
		return frappe.get_doc(doctype, name)
	doc = frappe.new_doc(doctype)
	doc.update(values)
	return doc


def home_variant():
	for layout_doctype, tile_doctype in HOME_VARIANTS:
		if frappe.db.exists("DocType", layout_doctype):
			return layout_doctype, tile_doctype
	return None


def registered_loaders():
	loaders = {}
	for entry in frappe.get_hooks(LOADER_HOOK) or []:
		if isinstance(entry, dict) and entry.get("key"):
			loaders[entry["key"]] = entry
	return loaders


def is_loaded(entry):
	if not entry.get("is_loaded"):
		return None
	return bool(frappe.get_attr(entry["is_loaded"])())

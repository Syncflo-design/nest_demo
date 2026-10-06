"""Starter business types, shipped with the app and added to a site once."""

import json
import os

import frappe

from nest_demo.switch import home_variant, registered_loaders

STARTERS = os.path.join(os.path.dirname(__file__), "business_types.json")


@frappe.whitelist()
def seed_business_types():
	"""Adds any starter type the site doesn't have. Existing types are never touched,
	so to refresh a starter type: delete it, then reload the starter types."""
	if frappe.session.user != "Administrator":
		frappe.only_for("System Manager")
	with open(STARTERS, encoding="utf-8") as fh:
		starters = json.load(fh)
	variant = home_variant()
	loaders = registered_loaders()
	added = []
	for starter in starters:
		if frappe.db.exists("Business Type", starter["business_type"]):
			continue
		# Anything not on this site (an app not installed, a tile not created) is left out.
		doc = frappe.get_doc(
			{
				"doctype": "Business Type",
				"business_type": starter["business_type"],
				"description": starter.get("description"),
				"is_standard": 1,
				"greeting": starter.get("greeting"),
				"show_attention": starter.get("show_attention", 1),
				"roles": [{"role": r} for r in starter.get("roles", []) if frappe.db.exists("Role", r)],
				"modules": [{"module": m} for m in starter.get("modules", []) if frappe.db.exists("Module Def", m)],
				"apps": [
					{"icon": a}
					for a in starter.get("apps", [])
					if frappe.db.exists("DocType", "Desktop Icon") and frappe.db.exists("Desktop Icon", a)
				],
				"tiles": [{"tile": t} for t in starter.get("tiles", []) if variant and frappe.db.exists(variant[1], t)],
				"data_sources": [{"loader": k} for k in starter.get("data_sources", []) if k in loaders],
			}
		)
		if not doc.roles:
			continue
		doc.insert(ignore_permissions=True)
		added.append(doc.name)
	frappe.db.commit()
	return added

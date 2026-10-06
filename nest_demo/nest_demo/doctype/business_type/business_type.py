import frappe
from frappe.model.document import Document

from nest_demo.switch import home_variant, registered_loaders


class BusinessType(Document):
	def validate(self):
		# Show what each tile and data source is, next to its key.
		variant = home_variant()
		for row in self.tiles:
			row.label = frappe.db.get_value(variant[1], row.tile, "label") if variant else None
		loaders = registered_loaders()
		for row in self.data_sources:
			row.label = (loaders.get(row.loader) or {}).get("label")

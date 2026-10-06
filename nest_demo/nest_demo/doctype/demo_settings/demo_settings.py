from frappe.model.document import Document

from nest_demo.switch import check_users


class DemoSettings(Document):
	def validate(self):
		# Refuse an admin or real account here, not only when Apply runs.
		check_users([row.user for row in self.demo_users])

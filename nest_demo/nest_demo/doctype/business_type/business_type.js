// Business Type: pickers for home tiles and demo data, and a shortcut to apply it.

frappe.ui.form.on('Business Type', {
	setup(frm) {
		// Only app and folder icons are switched; workspace links follow the modules.
		frm.set_query('icon', 'apps', function() {
			return { filters: { icon_type: ['in', ['App', 'Folder']] } };
		});
	},

	refresh(frm) {
		frm.add_custom_button(__('Add Tiles'), function() { nest_demo_pick_tiles(frm); }, __('Home Page'));
		frm.add_custom_button(__('Add Demo Data'), function() { nest_demo_pick_data(frm); });
		if (!frm.is_new()) {
			frm.add_custom_button(__('Apply This Type'), function() {
				frappe.confirm(
					__('Show the demo site as {0}? The demo login(s) in Demo Settings get these roles and this view.', [frm.doc.name.bold()]),
					function() {
						frappe.call({
							method: 'nest_demo.switch.apply',
							args: { business_type: frm.doc.name },
							freeze: true,
							freeze_message: __('Applying...'),
							callback: function() {
								frappe.show_alert({ message: __('The demo site now shows {0}', [frm.doc.name]), indicator: 'green' });
							}
						});
					}
				);
			}).addClass('btn-primary');
		}
	}
});

// A tick-list dialog; the picked keys are appended as rows in the given table.
function nest_demo_pick(frm, title, options, table, field) {
	var have = (frm.doc[table] || []).map(function(r) { return r[field]; });
	var choices = options.filter(function(o) { return have.indexOf(o.value) === -1; });
	if (!choices.length) {
		frappe.msgprint(__('Everything available is already listed.'));
		return;
	}
	var dialog = new frappe.ui.Dialog({
		title: title,
		fields: [{ fieldname: 'picked', fieldtype: 'MultiCheck', options: choices, columns: 1 }],
		primary_action_label: __('Add'),
		primary_action: function(v) {
			(v.picked || []).forEach(function(key) {
				var row = frm.add_child(table);
				row[field] = key;
			});
			frm.refresh_field(table);
			frm.dirty();
			dialog.hide();
		}
	});
	dialog.show();
}

function nest_demo_pick_tiles(frm) {
	frappe.call('nest_demo.switch.list_tiles').then(function(r) {
		var tiles = r.message || [];
		if (!tiles.length) {
			frappe.msgprint(__('No Nest Home tiles found. Install Nest Home and create tiles first.'));
			return;
		}
		nest_demo_pick(frm, __('Add home tiles'), tiles.map(function(t) {
			return { label: t.label + (t.description ? ' &middot; <span class="text-muted">' + frappe.utils.escape_html(t.description) + '</span>' : ''), value: t.name };
		}), 'tiles', 'tile');
	});
}

function nest_demo_pick_data(frm) {
	frappe.call('nest_demo.switch.list_loaders').then(function(r) {
		var loaders = r.message || [];
		if (!loaders.length) {
			frappe.msgprint(__('No installed app offers demo data yet.'));
			return;
		}
		nest_demo_pick(frm, __('Add demo data'), loaders.map(function(l) {
			return { label: frappe.utils.escape_html(l.label), value: l.key };
		}), 'data_sources', 'loader');
	});
}

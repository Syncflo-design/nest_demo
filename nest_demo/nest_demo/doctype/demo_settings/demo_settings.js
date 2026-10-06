// Demo Settings: the business-type switch.

frappe.ui.form.on('Demo Settings', {
	refresh(frm) {
		frm.add_custom_button(__('Apply'), function() { nest_demo_apply(frm); }).addClass('btn-primary');
		frm.add_custom_button(__('Reset Site'), function() {
			frappe.confirm(__('Put every app icon back as it was and switch off the demo home page?'), function() {
				nest_demo_call(frm, 'nest_demo.switch.reset', {}, __('The site is back to neutral'));
			});
		});
		frm.add_custom_button(__('Reload Starter Types'), function() {
			frappe.call({
				method: 'nest_demo.install.seed_business_types',
				callback: function(r) {
					var added = r.message || [];
					frappe.msgprint(added.length ? __('Added: {0}', [added.join(', ')]) : __('Every starter type is already here.'));
				}
			});
		}, __('More'));
		nest_demo_status(frm);
	}
});

function nest_demo_apply(frm) {
	if (!frm.doc.business_type) {
		frappe.msgprint(__('Pick a business type first.'));
		return;
	}
	var go = function() {
		nest_demo_call(frm, 'nest_demo.switch.apply', { business_type: frm.doc.business_type },
			__('The demo site now shows {0}', [frm.doc.business_type]));
	};
	// Save the picks first so Apply uses what is on screen.
	if (frm.is_dirty()) frm.save().then(go);
	else go();
}

function nest_demo_call(frm, method, args, done) {
	frappe.call({
		method: method,
		args: args,
		freeze: true,
		freeze_message: __('Working...'),
		callback: function(r) {
			frappe.show_alert({ message: done, indicator: 'green' });
			frm.reload_doc();
		}
	});
}

function nest_demo_status(frm) {
	frappe.call('nest_demo.switch.status').then(function(r) {
		var s = r.message || {};
		var esc = frappe.utils.escape_html;
		frm.get_field('status_html').$wrapper.html(s.applied_type
			? '<div class="alert alert-success" style="margin:0">' + __('Showing as {0}', ['<b>' + esc(s.applied_type) + '</b>']) +
				' &middot; ' + __('applied {0} by {1}', [frappe.datetime.comment_when(s.applied_on), esc(s.applied_by || '')]) +
				(s.users.length ? '<br><span class="text-muted">' + __('Demo logins: {0}', [s.users.map(esc).join(', ')]) + '</span>' : '') + '</div>'
			: '<div class="alert alert-secondary" style="margin:0">' + __('Neutral: no business type applied.') + '</div>');

		var $data = frm.get_field('data_html').$wrapper;
		if (!s.applied_type || !s.data.length) {
			$data.html('<p class="text-muted">' + (s.applied_type ? __('This business type has no demo data.') : __('Apply a business type to see its demo data.')) + '</p>');
			return;
		}
		$data.html(s.data.map(function(d) {
			var state = d.loaded === null ? '' : (d.loaded
				? '<span class="indicator-pill green">' + __('Loaded') + '</span>'
				: '<span class="indicator-pill gray">' + __('Not loaded') + '</span>');
			return '<div style="display:flex;align-items:center;gap:10px;padding:8px 0;border-bottom:1px solid var(--border-color)">' +
				'<div style="flex:1"><b>' + esc(d.label) + '</b> ' + state + '</div>' +
				'<button class="btn btn-xs btn-default" data-loader="' + esc(d.key) + '" data-action="load">' + __('Load') + '</button>' +
				'<button class="btn btn-xs btn-default" data-loader="' + esc(d.key) + '" data-action="remove">' + __('Remove') + '</button></div>';
		}).join(''));
		$data.find('[data-loader]').on('click', function() {
			var key = $(this).attr('data-loader');
			var action = $(this).attr('data-action');
			var run = function() {
				nest_demo_call(frm, 'nest_demo.switch.run_loader', { key: key, action: action },
					action === 'load' ? __('Demo data loaded') : __('Demo data removed'));
			};
			if (action === 'remove') frappe.confirm(__('Remove this demo data?'), run);
			else run();
		});
	});
}

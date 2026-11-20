from importlib import import_module
from unittest import TestCase
from unittest.mock import MagicMock, patch

from frappe import _dict

add_landscape_graph_link = import_module("it_management.patches.0_4.add_landscape_graph_link")


class FakeWorkspace:
	def __init__(self, links):
		self.links = [_dict(link) for link in links]
		self.saved = False

	def get(self, fieldname, default=None):
		return getattr(self, fieldname, default)

	def append(self, fieldname, value):
		self.get(fieldname).append(_dict(value))

	def remove(self, row):
		self.links.remove(row)

	def save(self, **kwargs):
		invalid_links = [row for row in self.links if row.link_type == "Workspace"]
		if invalid_links:
			raise AssertionError("Workspace link type is invalid in Frappe v16")
		self.saved = True


class TestAddLandscapeGraphLink(TestCase):
	def test_removes_obsolete_networking_workspace_link_before_save(self):
		workspace = FakeWorkspace(
			[
				{
					"type": "Link",
					"label": "Networking",
					"link_type": "Workspace",
					"link_to": "Networking",
				}
			]
		)
		fake_frappe = MagicMock()
		fake_frappe.db.exists.return_value = True
		fake_frappe.get_doc.return_value = workspace

		with patch.object(add_landscape_graph_link, "frappe", fake_frappe):
			add_landscape_graph_link._ensure_workspace_link()

		self.assertTrue(workspace.saved)
		self.assertFalse(any(row.link_type == "Workspace" for row in workspace.links))
		self.assertTrue(
			any(
				row.link_type == "Page" and row.link_to == add_landscape_graph_link.PAGE_NAME
				for row in workspace.links
			)
		)
		fake_frappe.db.commit.assert_called_once_with()

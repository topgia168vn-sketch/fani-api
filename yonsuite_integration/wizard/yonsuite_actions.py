# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class YonsuiteActions(models.TransientModel):
    _name = 'yonsuite.actions'
    _description = 'YonSuite Actions'

    name = fields.Char(
        string='Action',
        default='YonSuite Actions',
        readonly=True
    )

    action_type = fields.Selection([
        ('import_partners', 'Import Partners'),
        ('import_admindepts', 'Import Admin Departments'),
        ('import_orgunits', 'Import Orgunits'),
        ('import_getallorgdept', 'Import Org/Dept'),
        ('import_products', 'Import Products'),
        ('import_orders', 'Import Order'),
        ('import_vendors', 'Import Vendors'),
        ('import_brands', 'Import Brands'),
        ('import_units', 'Import Units'),
        ('import_warehouses', 'Import Warehouses'),
        ('import_carriers', 'Import Carriers'),
        ('import_salearea', 'Import Sale Area'),
        ('import_stores', 'Import Stores'),
        ('import_staff', 'Import Staff'),
        ('import_countries', 'Import Countries'),
        ('import_currencies', 'Import Currencies'),
        ('import_management_classes', 'Import Management Classes'),
        ('import_purchase_classes', 'Import Purchase Classes'),
        ('import_sale_classes', 'Import Sale Classes'),
        ('get_access_token', 'Get Access Token'),
    ], string='Action Type', required=True, default='get_access_token')

    def do_action(self):
        """
        Execute action based on action_type
        """
        self.ensure_one()

        action_map = {
            'import_partners': self.env['yonsuite.partner'].action_import_partners_pagination,
            'import_admindepts': self.env['yonsuite.admindept'].action_import_admindepts_pagination,
            'import_orgunits': self.env['yonsuite.orgunit'].action_import_orgunits_pagination,
            'import_getallorgdept': self.env['yonsuite.getallorgdept'].action_import_getallorgdept_pagination,
            'import_products': self.env['yonsuite.product'].action_import_products_pagination,
            'import_orders': self.env['yonsuite.order'].action_import_orders_pagination,
            'import_vendors': self.env['yonsuite.vendor'].action_import_vendors_pagination,
            'import_brands': self.env['yonsuite.brand'].action_import_brands_pagination,
            'import_units': self.env['yonsuite.unit'].action_import_units_pagination,
            'import_warehouses': self.env['yonsuite.warehouse'].action_import_warehouses_pagination,
            'import_carriers': self.env['yonsuite.carrier'].action_import_carriers_pagination,
            'import_staff': self.env['yonsuite.staff'].action_import_staff_pagination,
            'import_salearea': self.env['yonsuite.salearea'].action_import_saleareas_pagination,
            'import_stores': self.env['yonsuite.store'].action_import_stores_pagination,
            'import_countries': self.env['yonsuite.country'].action_import_countries_pagination,
            'import_currencies': self.env['yonsuite.currency'].action_import_currencies_pagination,
            'import_management_classes': self.env['yonsuite.management.class'].action_import_management_classes_pagination,
            'import_purchase_classes': self.env['yonsuite.purchase.class'].action_import_purchase_classes_pagination,
            'import_sale_classes': self.env['yonsuite.sale.class'].action_import_sale_classes_pagination,
            'get_access_token': self.env['yonsuite.api'].get_access_token,
        }

        action_method = action_map.get(self.action_type)
        if not action_method:
            raise UserError(_('Unknown action type: %s') % self.action_type)

        action_method()

# -*- coding: utf-8 -*-

from odoo import models, fields, api, _
from odoo.exceptions import UserError
import logging

_logger = logging.getLogger(__name__)


class YonsuiteProductOrges(models.Model):
    _name = 'yonsuite.product.orges'
    _description = 'YonSuite Product Organizations'
    _order = 'product_id, range_type, org_code'

    product_id = fields.Many2one(
        'yonsuite.product',
        string='Product',
        required=True,
        ondelete='cascade',
        help='Related YonSuite Product'
    )

    range_type = fields.Integer(
        string='Range Type',
        help='Range type from YonSuite'
    )

    org_id = fields.Char(
        string='Organization ID',
        help='Organization ID from YonSuite'
    )

    org_code = fields.Char(
        string='Organization Code',
        help='Organization code from YonSuite'
    )

    is_creator = fields.Boolean(
        string='Is Creator',
        help='Is creator flag from YonSuite'
    )

    is_applied = fields.Boolean(
        string='Is Applied',
        help='Is applied flag from YonSuite'
    )

    org_type = fields.Integer(
        string='Organization Type',
        help='Organization type from YonSuite'
    )

    # Computed fields for display
    display_name = fields.Char(
        string='Display Name',
        compute='_compute_display_name',
        store=True,
        help='Computed display name'
    )

    @api.depends('org_code', 'org_id', 'range_type')
    def _compute_display_name(self):
        """
        Compute display name for the record
        """
        for record in self:
            if record.org_code and record.org_id:
                record.display_name = f"{record.org_code} ({record.org_id})"
            elif record.org_code:
                record.display_name = record.org_code
            elif record.org_id:
                record.display_name = record.org_id
            else:
                record.display_name = f"Range Type {record.range_type}"

    @api.model
    def create_or_update_product_orges(self, product_id, product_orges_data):
        """
        Create or update product organizations from API data
        
        Args:
            product_id (int): ID of the yonsuite.product record
            product_orges_data (list): List of productOrges data from API
        """
        if not product_orges_data:
            return

        # Get existing records for this product
        existing_records = self.search([('product_id', '=', product_id)])
        existing_dict = {}
        for record in existing_records:
            key = f"{record.org_id}_{record.range_type}"
            existing_dict[key] = record

        # Process new data
        new_keys = set()
        for org_data in product_orges_data:
            org_id = str(org_data.get("orgId", ""))
            range_type = org_data.get("rangeType", 0)
            key = f"{org_id}_{range_type}"
            new_keys.add(key)

            vals = {
                'product_id': product_id,
                'range_type': range_type,
                'org_id': org_id,
                'org_code': org_data.get("orgCode", ""),
                'is_creator': org_data.get("isCreator", False),
                'is_applied': org_data.get("isApplied", False),
                'org_type': org_data.get("orgType", 0),
            }

            if key in existing_dict:
                # Update existing record
                existing_dict[key].write(vals)
            else:
                # Create new record
                self.create(vals)

        # Remove records that are no longer in the API data
        for key, record in existing_dict.items():
            if key not in new_keys:
                record.unlink()

    @api.model
    def get_product_orges_by_product(self, product_id):
        """
        Get all organizations for a specific product
        
        Args:
            product_id (int): ID of the yonsuite.product record
            
        Returns:
            recordset: All organization records for the product
        """
        return self.search([('product_id', '=', product_id)])

    @api.model
    def get_applied_organizations(self, product_id):
        """
        Get only applied organizations for a specific product
        
        Args:
            product_id (int): ID of the yonsuite.product record
            
        Returns:
            recordset: Applied organization records for the product
        """
        return self.search([
            ('product_id', '=', product_id),
            ('is_applied', '=', True)
        ])

    @api.model
    def get_creator_organizations(self, product_id):
        """
        Get only creator organizations for a specific product
        
        Args:
            product_id (int): ID of the yonsuite.product record
            
        Returns:
            recordset: Creator organization records for the product
        """
        return self.search([
            ('product_id', '=', product_id),
            ('is_creator', '=', True)
        ])

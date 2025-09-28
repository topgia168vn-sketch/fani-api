from odoo import models, fields


class WizardSyncJSTSaleOrder(models.TransientModel):
    _name = 'wizard.sync.jst.sale.order'
    _description = 'Wizard Sync JST Order'

    def _default_date_from(self):
        return fields.Datetime.now()
    def _default_date_to(self):
        return fields.Datetime.now()

    # Basic info from API
    type = fields.Selection([('create', 'Theo ngày tạo đơn'), ('write', 'Theo ngày cập nhật')], string='Kiểu thời gian', default='create')
    date_from = fields.Datetime("Ngày Bắt đầu", default=_default_date_from)
    date_to = fields.Datetime("Ngày kết thúc", default=_default_date_to)

    def action_sync(self):
        modifiedBegin = int(self.date_from.timestamp())
        modifiedEnd = int(self.date_to.timestamp())

        if self.type == 'create':
            selection_type = 'order_time'
            only_create = True
        else:
            selection_type = 'modify_time'
            only_create = False
        self.env['jst.sale.order'].action_sync_jst_orders(modifiedBegin, modifiedEnd, field=selection_type, only_create=only_create)

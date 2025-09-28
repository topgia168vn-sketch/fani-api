from odoo import models, fields


class WizardSyncJSTSaleOrderAfter(models.TransientModel):
    _name = 'wizard.sync.jst.sale.order.after'
    _description = 'Wizard Sync JST Order After'

    def _default_date_from(self):
        return fields.Datetime.now()
    def _default_date_to(self):
        return fields.Datetime.now()

    # Basic info from API
    type = fields.Selection([('order_time', 'Theo ngày đặt đơn'), ('write', 'Theo ngày cập nhật')], string='Kiểu thời gian', default='order_time')
    date_from = fields.Datetime("Ngày Bắt đầu", default=_default_date_from)
    date_to = fields.Datetime("Ngày kết thúc", default=_default_date_to)

    def action_sync(self):
        modifiedBegin = int(self.date_from.timestamp())
        modifiedEnd = int(self.date_to.timestamp())

        if self.type == 'order_time':
            selection_type = 'order_time'
        else:
            selection_type = 'modify_time'
        self.env['jst.sale.order.after'].action_sync_jst_after_orders(modifiedBegin, modifiedEnd, field=selection_type)

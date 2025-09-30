from odoo import models, fields, _
from odoo.exceptions import UserError


class WizardSyncJSTStockInout(models.TransientModel):
    _name = 'wizard.sync.jst.stock.inout'
    _description = 'Wizard Sync JST Stock Inout'

    def _default_date_from(self):
        return fields.Datetime.now()
    def _default_date_to(self):
        return fields.Datetime.now()

    # Basic info from API
    inout_type = fields.Selection([('sale', 'Phiếu giao hàng'), ('purchase', 'Phiếu nhận hàng'), ('other', 'Phiếu giao khác')], string='Kiểu phiếu', default='sale')
    time_type = fields.Selection([('create', 'Theo thời gian tạo phiếu'), ('send', 'Theo thời gian gửi')], string='Kiểu thời gian', default='create')
    date_from = fields.Datetime("Ngày Bắt đầu", default=_default_date_from)
    date_to = fields.Datetime("Ngày kết thúc", default=_default_date_to)

    def action_sync(self):
        self.ensure_one()
        modifiedBegin = int(self.date_from.timestamp())
        modifiedEnd = int(self.date_to.timestamp())

        if self.inout_type == 'sale':
            if self.time_type == 'create':
                requestModel = {
                    "CreateBegin": modifiedBegin,
                    "CreateEnd": modifiedEnd
                }
            else:
                requestModel = {
                    "SendTimeBegin": modifiedBegin,
                    "SendTimeEnd": modifiedEnd
                }
            self.env['jst.stock.inout']._sync_jst_sale_inouts(requestModel)
        else:
            requestModel = {
                "modifiedBegin": modifiedBegin,
                "modifiedEnd": modifiedEnd
            }
            if self.inout_type == 'purchase':
                self.env['jst.stock.inout']._sync_jst_purchase_inouts(requestModel)
            else:
                self.env['jst.stock.inout']._sync_jst_other_out_inouts(requestModel)
                self.env['jst.stock.inout']._sync_jst_other_in_inouts(requestModel)

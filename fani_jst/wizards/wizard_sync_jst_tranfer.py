from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class WizardSyncJSTTranfer(models.TransientModel):
    _name = 'wizard.sync.jst.tranfer'
    _description = 'Wizard Sync JST Tranfer'

    def _default_date_from(self):
        return fields.Datetime.now()
    def _default_date_to(self):
        return fields.Datetime.now()

    # Basic info from API
    date_from = fields.Datetime("Từ ngày", default=_default_date_from, required=True)
    date_to = fields.Datetime("Đến ngày", default=_default_date_to, required=True)

    def action_sync(self):
        requestModel = {
            "ModifiedBegin": int(self.date_from.timestamp()),
            "ModifiedEnd": int(self.date_to.timestamp())
        }
        # Đồng bộ phiếu chuyển JST
        _logger.info("Sync JST Stock Transfer: Wizard -> Đồng bộ phiếu chuyển JST ...")
        self.env['jst.stock.tranfer']._sync_jst_stock_tranfers(requestModel)
        # Đồng bộ phiếu chuyển JST Out InOut
        _logger.info("Sync JST Stock Transfer: Wizard -> Đồng bộ phiếu chuyển JST Out InOut ...")
        self.env['jst.stock.inout']._sync_jst_transfer_out_inouts(requestModel)
        # Đồng bộ phiếu chuyển JST In InOut
        _logger.info("Sync JST Stock Transfer: Wizard -> Đồng bộ phiếu chuyển JST In InOut ...")
        self.env['jst.stock.inout']._sync_jst_transfer_in_inouts(requestModel)

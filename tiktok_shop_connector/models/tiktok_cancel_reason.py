from odoo import api, models, fields


class TiktokCancelReason(models.Model):
    _name = "tiktok.cancel.reason"
    _description = "TikTok Cancel Reasons"
    _order = "code"
    _rec_name = "name"

    # ===== Basic Information =====
    code = fields.Char(string="Reason Code", required=True, index=True)
    name = fields.Char(string="Reason Name", required=True)

    _sql_constraints = [
        ('unique_code', 'unique(code)', 'Reason code must be unique!'),
    ]

    @api.model
    def _upsert_reason(self, code, name):
        """
        Tìm hoặc tạo cancel reason record.
        Returns: tiktok.cancel.reason record
        """
        if not code or not name:
            return False

        # Tìm existing reason
        reason = self.search([('code', '=', code)], limit=1)
        if reason:
            if reason.name != name:
                reason.name = name
            return reason

        # Tạo mới nếu chưa có
        return self.create({
            'code': code,
            'name': name
        })

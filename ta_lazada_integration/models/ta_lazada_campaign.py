from odoo import api, fields, models, _


class TaLazadaCampaign(models.Model):
    _name = 'ta.lazada.campaign'
    _description = 'Lazada Sponsored Campaign'
    _order = 'start_date desc, id desc'

    authorized_shop_id = fields.Many2one('ta.lazada.authorized.shop', 'Authorized Shop', required=True, index=True, ondelete='cascade')

    # Identifiers
    campaign_id = fields.Char('Campaign ID', required=True, index=True)
    name = fields.Char('Campaign Name')

    # List API fields (searchCampaignList)
    ctr = fields.Char('CTR')
    campaign_daily_budget_status = fields.Selection([
        ('0', 'Off'), ('1', 'On')
    ], string='Daily Budget Status')
    end_date = fields.Date('End Date')
    store_revenue = fields.Char('Store Revenue')
    store_orders = fields.Char('Store Orders')
    impressions = fields.Char('Impressions')
    store_units_sold = fields.Char('Store Units Sold')
    campaign_switch_status = fields.Selection([
        ('0', 'Off'), ('1', 'On')
    ], string='Campaign Switch Status')
    ad_account_balance_status = fields.Selection([
        ('0', 'Insufficient'), ('1', 'Sufficient')
    ], string='Ad Account Balance Status')
    store_roi = fields.Char('Store ROI')
    daily_budget = fields.Char('Daily Budget')
    cpc = fields.Char('CPC')
    spend = fields.Char('Spend')
    campaign_schedule_status = fields.Selection([
        ('0', 'Off'), ('1', 'On')
    ], string='Schedule Status')
    clicks = fields.Char('Clicks')
    have_active_ad_status = fields.Selection([
        ('0', 'No'), ('1', 'Yes')
    ], string='Have Active Ad')
    start_date = fields.Date('Start Date')
    status = fields.Char('Status')

    # Detail API fields (getCampaign)
    objective = fields.Char('Campaign Objective')
    type = fields.Char('Campaign Type')
    online_status = fields.Selection([
        ('0', 'Offline'), ('1', 'Online'), ('9', 'Deleted')
    ], string='Online Status')
    switch_status = fields.Selection([
        ('0', 'Off'), ('1', 'On')
    ], string='Switch Status')
    platform = fields.Char('Platform Raw')
    budget_used_amount = fields.Char('Budget Used Amount')
    auto_item_select = fields.Selection([
        ('1', 'Manual'), ('2', 'Auto'), ('0', 'Unknown')
    ], string='Auto Item Select')
    model_code = fields.Char('Campaign Model')
    max_bid = fields.Char('Max Bid')
    have_ad_count = fields.Char('Have Ad Count')
    scene_id = fields.Char('Scene ID')
    auto_creative = fields.Selection([
        ('0', 'Off'), ('1', 'On')
    ], string='Auto Creative')
    day_budget = fields.Char('Day Budget')

    _sql_constraints = [
        ('uniq_shop_campaign', 'unique(authorized_shop_id, campaign_id)', 'Campaign must be unique per shop.')
    ]

    # =============================
    # Sync logic (similar to orders)
    # =============================
    def import_from_lazada_for_shop(self, authorized_shop):
        """Fetch campaigns for the given shop and upsert records, then fetch details per campaign."""
        self = self.sudo()
        authorized_shop.ensure_one()
        try:
            list_endpoint = '/sponsor/solutions/campaign/searchCampaignList'
            page_no = int(authorized_shop.campaign_page_no or 1)
            page_size = int(authorized_shop.campaign_page_size or 50)
            total_count = None
            success_count = 0
            error_count = 0

            while True:
                list_params = {
                    'bizCode': authorized_shop.campaign_biz_code or 'sponsoredSearch',
                    'startDate': fields.Date.to_string(authorized_shop.campaign_start_date) if authorized_shop.campaign_start_date else None,
                    'endDate': fields.Date.to_string(authorized_shop.campaign_end_date) if authorized_shop.campaign_end_date else None,
                    'pageNo': str(page_no),
                    'pageSize': str(page_size),
                }
                response = authorized_shop._make_api_request(list_endpoint, list_params, 'GET')

                # capture totalCount for first page
                if total_count is None:
                    total_count = int(response.get('totalCount') or 0)

                items = response.get('result') or []
                for item in items:
                    try:
                        vals = self._prepare_vals_from_list(item, authorized_shop)
                        campaign = self.search([
                            ('authorized_shop_id', '=', authorized_shop.id),
                            ('campaign_id', '=', vals.get('campaign_id'))
                        ], limit=1)
                        if campaign:
                            campaign.write(vals)
                        else:
                            campaign = self.create(vals)

                        # Fetch detail
                        detail = self._fetch_campaign_detail(authorized_shop, campaign.campaign_id)
                        if detail:
                            campaign.write(self._prepare_vals_from_detail(detail))
                        success_count += 1
                    except Exception as item_error:
                        error_count += 1
                        try:
                            authorized_shop.message_post(body=_('Error syncing campaign %s: %s') % (item.get('campaignId'), str(item_error)))
                        except:
                            pass

                # pagination: stop when covered totalCount or page returns fewer than page_size
                if not items or (total_count is not None and page_no * page_size >= total_count):
                    break
                page_no += 1

            try:
                authorized_shop.message_post(
                    body=_('Campaign sync completed. Total from API: %s, Success: %s, Errors: %s') % (str(total_count or 0), str(success_count), str(error_count))
                )
            except:
                pass
        except Exception as e:
            try:
                authorized_shop.message_post(body=_('Error syncing campaigns: %s') % str(e))
            except:
                pass
            raise

    def _fetch_campaign_detail(self, authorized_shop, campaign_id):
        detail_endpoint = '/sponsor/solutions/campaign/getCampaign'
        detail_params = {
            'campaignId': campaign_id,
            'bizCode': authorized_shop.campaign_biz_code or 'sponsoredSearch',
        }
        detail_response = authorized_shop._make_api_request(detail_endpoint, detail_params, 'GET')
        if detail_response.get('code') == '0' and detail_response.get('result'):
            return detail_response.get('result')
        return None

    def _prepare_vals_from_list(self, item, authorized_shop):
        # Coerce numeric enums to strings for selection fields
        def s(v):
            return str(v) if v is not None and v != '' else False
        return {
            'authorized_shop_id': authorized_shop.id,
            'campaign_id': item.get('campaignId'),
            'name': item.get('campaignName'),
            'ctr': item.get('ctr'),
            'campaign_daily_budget_status': s(item.get('campaignDailyBudgetStatus')),
            'end_date': item.get('endDate'),
            'store_revenue': item.get('storeRevenue'),
            'store_orders': item.get('storeOrders'),
            'impressions': item.get('impressions'),
            'store_units_sold': item.get('storeUnitsSold'),
            'campaign_switch_status': s(item.get('campaignSwitchStatus')),
            'ad_account_balance_status': s(item.get('adAccountBalanceStatus')),
            'store_roi': item.get('storeRoi'),
            'daily_budget': item.get('dailyBudget'),
            'cpc': item.get('cpc'),
            'spend': item.get('spend'),
            'campaign_schedule_status': s(item.get('campaignScheduleStatus')),
            'clicks': item.get('clicks'),
            'have_active_ad_status': s(item.get('haveActiveAdStatus')),
            'start_date': item.get('startDate'),
            'status': s(item.get('status')) or item.get('status'),
        }

    def _prepare_vals_from_detail(self, result):
        def s(v):
            return str(v) if v is not None and v != '' else False
        return {
            'objective': s(result.get('campaignObjective')) or result.get('campaignObjective'),
            'type': s(result.get('campaignType')) or result.get('campaignType'),
            'end_date': result.get('endDate') or False,
            'online_status': s(result.get('onlineStatus')),
            'switch_status': s(result.get('switchStatus')),
            'platform': str(result.get('platform') or []),
            'budget_used_amount': result.get('budgetUsedAmount'),
            'auto_item_select': s(result.get('autoItemSelect')),
            'model_code': result.get('campaignModel'),
            'max_bid': result.get('maxBid'),
            'have_ad_count': result.get('haveAdCount'),
            'scene_id': result.get('sceneId'),
            'auto_creative': s(result.get('autoCreative')),
            'name': result.get('campaignName'),
            'start_date': result.get('startDate') or False,
            'day_budget': result.get('dayBudget'),
        }


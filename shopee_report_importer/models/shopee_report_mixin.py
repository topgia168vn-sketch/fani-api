# -*- coding: utf-8 -*-

import os
import logging
import pytz
import pandas as pd
import re
from datetime import datetime, date, timezone
from odoo import models, fields, api
from odoo.tools import config

_logger = logging.getLogger(__name__)


class ShopeeReportMixin(models.AbstractModel):
    _name = 'shopee.report.mixin'
    _description = 'Shopee Report Mixin'

    # ==================== HELPER METHODS ====================
    def _parse_percentage(self, percent_str):
        """Parse percentage string to float"""
        if not percent_str or percent_str == '-':
            return 0.0
        try:
            # Remove % and convert to float
            return float(percent_str.replace('%', '').replace(',', '.'))
        except:
            return 0.0

    def _parse_float(self, float_str):
        """Parse float string to float"""
        if not float_str or float_str == '-':
            return 0.0
        try:
            return float(float_str.replace(',', ''))
        except:
            return 0.0

    def _parse_date(self, date_str, format='%Y-%m-%d'):
        """Parse date string to date object"""
        if not date_str or date_str in ['-', 'Không giới hạn']:
            return False
        try:
            # Format: "05/09/2025"
            return datetime.strptime(date_str, format).date()
        except:
            return False

    def _parse_datetime(self, dt_str, format='%Y-%m-%d %H:%M:%S'):
        """Parse datetime and convert to UTC"""
        if not dt_str or dt_str == '-':
            return False
        try:
            # Parse as datetime in local timezone
            dt = datetime.strptime(dt_str, format)
            tz = self.env.user.tz or 'Asia/Ho_Chi_Minh'
            # Convert to UTC
            tz_obj = pytz.timezone(tz)
            dt_with_tz = tz_obj.localize(dt)
            return dt_with_tz.astimezone(timezone.utc).replace(tzinfo=None)
        except ValueError:
            return False

    def _parse_hour_to_float(self, hour_str):
        """Parse hour string 'HH:MM' to float"""
        if not hour_str or hour_str == '-':
            return 0.0
        try:
            if ':' in hour_str:
                hours, minutes = hour_str.split(':')
                return float(hours) + float(minutes) / 60.0
            else:
                return float(hour_str)
        except:
            return 0.0

    @api.model
    def _upsert(self, domain, values):
        """
        Helper method để upsert (update hoặc create) records.

        Args:
            domain (list): Domain để search existing record
            values (dict): Values để write/create

        Returns:
            recordset: Record được update hoặc create
        """
        existing_record = self.search(domain, limit=1)

        if existing_record:
            existing_record.write(values)
        else:
            existing_record = self.create(values)

        return existing_record

    # ==================== CRON METHODS ====================
    @api.model
    def _cron_import_downloaded_data(self):
        """New cron method - import data from downloaded files"""
        _logger.info("Start importing downloaded data...")

        # Get filestore path
        filestore_path = config.filestore(self.env.cr.dbname)
        shopee_scripts_dir = os.path.join(filestore_path, 'shopee_scripts')

        if not os.path.exists(shopee_scripts_dir):
            _logger.info("No shopee_scripts directory found")
            return

        # Find all shop workspaces
        workspaces = []
        for item in os.listdir(shopee_scripts_dir):
            if item.startswith('shop_') and os.path.isdir(os.path.join(shopee_scripts_dir, item)):
                shop_id = int(item.replace('shop_', ''))
                workspace_path = os.path.join(shopee_scripts_dir, item)
                workspaces.append({
                    'shop_id': shop_id,
                    'workspace_path': workspace_path
                })

        if not workspaces:
            _logger.info("No workspaces found")
            return

        _logger.info(f"Found {len(workspaces)} workspaces")

        # Process each workspace
        total_imported = 0
        for workspace in workspaces:
            try:
                imported = self._import_workspace_downloaded_data(workspace)
                total_imported += imported
                _logger.info(f"Shop {workspace['shop_id']}: {imported} records imported")
            except Exception as e:
                _logger.error(f"Error importing workspace {workspace['workspace_path']}: {str(e)}")
                continue

        _logger.info(f"Imported {total_imported} records for {len(workspaces)} shops.")

    def _import_workspace_downloaded_data(self, workspace):
        """Import data from a single workspace"""
        shop_id = workspace['shop_id']
        workspace_path = workspace['workspace_path']

        _logger.info(f"Processing workspace: shop_{shop_id}")

        # Get shop record
        shop = self.env['shopee.shop'].browse(shop_id)
        if not shop.exists():
            _logger.error(f"Shop {shop_id} not found in database")
            return 0

        # Define report mappings
        report_mappings = {
            'ads_cpc': {
                'model': 'shopee.ads.cpc.report',
                'download_dir': 'downloads/ads_cpc'
            },
            'ads_live': {
                'model': 'shopee.ads.live.report',
                'download_dir': 'downloads/ads_live'
            },
            'booking': {
                'model': 'shopee.booking.report',
                'download_dir': 'downloads/booking'
            },
            'laban': {
                'model': 'shopee.laban.report',
                'download_dir': 'downloads/laban'
            },
            'live_product': {
                'model': 'shopee.live.product.report',
                'download_dir': 'downloads/live_product'
            },
            'order': {
                'model': 'shopee.order.report',
                'download_dir': 'downloads/order'
            },
            'video_product': {
                'model': 'shopee.video.product.report',
                'download_dir': 'downloads/video_product'
            }
        }

        total_imported = 0
        for report_type, config in report_mappings.items():
            try:
                imported = self._import_report_files_from_workspace(shop, workspace_path, report_type, config)
                total_imported += imported
            except Exception as e:
                _logger.error(f"Error importing {report_type} for shop {shop_id}: {str(e)}")

        # Update shop sync date
        shop.last_sync_date = fields.Datetime.now()

        return total_imported

    def _import_report_files_from_workspace(self, shop, workspace_path, report_type, config):
        """Import files for specific report type from workspace"""
        download_dir = os.path.join(workspace_path, config['download_dir'])

        if not os.path.exists(download_dir):
            _logger.info(f"No download directory found: {download_dir}")
            return 0

        # Find CSV/XLSX files
        files = []
        for file in os.listdir(download_dir):
            if file.endswith(('.csv', '.xlsx')):
                files.append(os.path.join(download_dir, file))

        if not files:
            _logger.info(f"No CSV/XLSX files found in: {download_dir}")
            return 0

        _logger.info(f"Found {len(files)} files for {report_type}")

        # Get model
        model = self.env[config['model']]
        imported_count = 0

        for file_path in files:
            try:
                _logger.info(f"Processing file: {file_path}")

                file_name = os.path.basename(file_path)
                parent_dir = os.path.basename(os.path.dirname(file_path))

                # Get report date from file name
                report_date = self._extract_report_date(file_name, parent_dir)
                if not report_date:
                    report_date = date.today()  # Fallback to today

                # Read file using pandas with proper header detection
                df = self._read_report_file(file_path)

                _logger.info(f"Loaded {len(df)} rows from {os.path.basename(file_path)}")

                # Process each row
                for _, row in df.iterrows():
                    try:
                        row_data = row.to_dict()
                        # Convert pandas NaN to None for Odoo
                        row_data = {k: (None if pd.isna(v) else v) for k, v in row_data.items()}

                        # Call the model method dynamically
                        if hasattr(model, '_import_row'):
                            model._import_row(shop.id, report_date, row_data)
                        else:
                            _logger.error(f"Method _import_row not found in {config['model']}")
                            break
                        imported_count += 1
                    except Exception as e:
                        _logger.warning(f"Error processing row in {file_path}: {str(e)}")
                        continue

                _logger.info(f"Imported {imported_count} records from {os.path.basename(file_path)}")

                # Delete file after successful import
                os.remove(file_path)
                _logger.info(f"Deleted file: {file_path}")

            except Exception as e:
                _logger.error(f"Error processing file {file_path}: {str(e)}")
                continue

        return imported_count

    def _read_report_file(self, file_path):
        """Read Shopee report file (CSV/XLSX) with proper header detection"""
        file_name = os.path.basename(file_path)
        
        def is_header_line(line):
            """Check if a CSV line is a header line"""
            # Count non-empty cells (split by comma and filter empty)
            cells = [cell.strip() for cell in line.split(',') if cell.strip()]
            return len(cells) > 5
        
        def is_header_row(row):
            """Check if a row is a header row"""
            # Count non-empty cells
            cells = [str(cell).strip() for cell in row if pd.notna(cell) and str(cell).strip()]
            return len(cells) > 5
        
        def find_header_row():
            """Find the header row in the file"""
            if file_name.endswith('.csv'):
                # Read file line by line to find header (streaming)
                with open(file_path, 'r', encoding='utf-8') as f:
                    for i, line in enumerate(f):
                        if is_header_line(line):
                            return i
            else:  # .xlsx
                # Read XLSX to find header row
                df_temp = pd.read_excel(file_path, header=None)
                for i, row in df_temp.iterrows():
                    if is_header_row(row):
                        return i
            
            return None
        
        def clean_dataframe(df):
            """Clean up the dataframe"""
            # Remove any completely empty rows
            df = df.dropna(how='all')
            # Remove rows that are all NaN or empty strings
            df = df[df.notna().any(axis=1)]
            return df
        
        # Find header row
        header_row = find_header_row()
        
        # Read file with proper header
        if file_name.endswith('.csv'):
            if header_row is not None:
                df = pd.read_csv(file_path, encoding='utf-8', skiprows=header_row)
            else:
                df = pd.read_csv(file_path, encoding='utf-8')
        else:  # .xlsx
            if header_row is not None:
                df = pd.read_excel(file_path, header=header_row)
            else:
                df = pd.read_excel(file_path)
        
        # Clean up and return dataframe
        return clean_dataframe(df)

    def _extract_report_date(self, file_name, parent_dir):
        """Extract report date from file name and parent directory"""
        if parent_dir == 'order':
            # Order.all.order_creation_date.20250922_20250922.xlsx
            match = re.search(r'(\d{8})', file_name)
            if match:
                date_str = match.group(1)
                return self._parse_date(date_str, '%Y%m%d')

        elif parent_dir == 'ads_cpc':
            # Dữ+liệu+Dịch+vụ+Hiển+thị+Shopee-24_09_2025-24_09_2025.csv
            match = re.search(r'(\d{2}_\d{2}_\d{4})', file_name)
            if match:
                date_str = match.group(1)
                return self._parse_date(date_str, '%d_%m_%Y')

        elif parent_dir == 'ads_live':
            # Dữ+liệu+tổng+quan+Dịch+vụ+Hiển+thị+Livestream+-24_09_2025-24_09_2025.csv
            match = re.search(r'(\d{2}_\d{2}_\d{4})', file_name)
            if match:
                date_str = match.group(1)
                return self._parse_date(date_str, '%d_%m_%Y')

        elif parent_dir == 'live_product':
            # export-sc_0_1d_2025-09-22_0638592_1758725946756.csv
            match = re.search(r'(\d{4}-\d{2}-\d{2})', file_name)
            if match:
                date_str = match.group(1)
                return self._parse_date(date_str, '%Y-%m-%d')

        elif parent_dir == 'booking':
            # ProductPerformance_202509241436.csv
            match = re.search(r'(\d{8})', file_name)
            if match:
                date_str = match.group(1)
                return self._parse_date(date_str, '%Y%m%d')

        elif parent_dir == 'laban':
            # productoverview20250924-20250924.xlsx
            match = re.search(r'(\d{8})', file_name)
            if match:
                date_str = match.group(1)
                return self._parse_date(date_str, '%Y%m%d')

        elif parent_dir == 'video_product':
            # export-sc_0_1d_2025-09-22_0398065_1758725994541.csv
            match = re.search(r'(\d{4}-\d{2}-\d{2})', file_name)
            if match:
                date_str = match.group(1)
                return self._parse_date(date_str, '%Y-%m-%d')

        return False

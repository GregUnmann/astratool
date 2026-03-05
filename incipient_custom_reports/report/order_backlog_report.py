from odoo import api, fields, models, _
from datetime import datetime
from dateutil.relativedelta import relativedelta
from collections import defaultdict

class OrderBacklogReport(models.AbstractModel):
    _name = 'report.incipient_custom_reports.report_order_backlog'
    _description = 'Order Backlog Report PDF Logic'

    @api.model
    def _get_report_values(self, docids, data=None):
        wizard = self.env['order.backlog.wizard'].browse(data.get('id', docids))
        start_date = wizard.start_date
        backlog_thru = int(wizard.backlog_thru)
        partner_ids = wizard.partner_ids

        month_columns = []
        for i in range(1, backlog_thru + 1):
            next_date = start_date + relativedelta(months=i)
            month_columns.append(next_date)
        domain = [
            ('state', 'in', ['sale', 'done']),
            ('product_id.type', 'in', ['consu', 'product']),
        ]
        if partner_ids:
            domain.append(('order_id.partner_id', 'in', partner_ids.ids))

        order_lines = self.env['sale.order.line'].search(domain, order='order_id, sequence')

        report_data = defaultdict(lambda: {
            'customer_name': '',
            'lines': [],
            'customer_total_price': 0.0,
            'customer_total_backlog': 0.0,
            'customer_monthly_totals': [0.0] * len(month_columns)
        })

        report_totals = {
            'grand_total_price': 0.0,
            'grand_total_backlog': 0.0,
            'grand_monthly_totals': [0.0] * len(month_columns)
        }

        for line in order_lines:
            qty_backlog = line.product_uom_qty - line.qty_delivered
            if qty_backlog <= 0:
                continue

            partner = line.order_id.partner_id
            partner_id = partner.id
            
            if not report_data[partner_id]['customer_name']:
                code = partner.ref or ''
                name = partner.name or ''
                report_data[partner_id]['customer_name'] = f"{code} {name}".strip()

            # Find Next Ship Date from pending moves (prioritize scheduled_date)
            pending_moves = line.move_ids.filtered(lambda m: m.state not in ['done', 'cancel'])
            next_ship_date = False
            if pending_moves:
                # Use min(scheduled_date) from pickings, fallback to move date
                all_move_dates = []
                for m in pending_moves:
                    dt = m.picking_id.scheduled_date or m.date
                    if dt:
                        all_move_dates.append(dt)
                if all_move_dates:
                    next_ship_date = min(all_move_dates)
                    if isinstance(next_ship_date, datetime):
                        next_ship_date = next_ship_date.date()
                else:
                    next_ship_date = fields.Date.today()
            else:
                next_ship_date = line.order_id.commitment_date or line.order_id.date_order
                if isinstance(next_ship_date, datetime):
                    next_ship_date = next_ship_date.date()

            total_price = line.price_total 
            backlog_amount = qty_backlog * line.price_reduce_taxinc 

            all_so_lines = line.order_id.order_line.filtered(lambda l: not l.display_type)
            line_index = list(all_so_lines.ids).index(line.id) + 1

            line_data = {
                'order': line.order_id.name,
                'line_no': line_index,
                'part': line.product_id.name,
                'next_ship': next_ship_date.strftime('%d/%m/%y') if next_ship_date else '',
                'tot_price': total_price,
                'tot_backlog': backlog_amount,
                'monthly_values': [0.0] * len(month_columns),
                'raw_ship_date': getattr(next_ship_date, 'date', lambda: next_ship_date)() if next_ship_date else None
            }

            if pending_moves:
                for move in pending_moves:
                    move_date = (move.picking_id.scheduled_date or move.date).date()
                    move_amount = move.product_uom_qty * line.price_reduce_taxinc
                    
                    found_bucket = False
                    for i, col_end in enumerate(month_columns):
                        bucket_start = start_date if i == 0 else month_columns[i-1]
                        
                        if i == 0:
                            is_in_bucket = move_date <= col_end
                        else:
                            is_in_bucket = bucket_start < move_date <= col_end
                        
                        if is_in_bucket:
                            line_data['monthly_values'][i] += move_amount
                            report_data[partner_id]['customer_monthly_totals'][i] += move_amount
                            report_totals['grand_monthly_totals'][i] += move_amount
                            found_bucket = True
                            break
                    
                    if not found_bucket and move_date < month_columns[0]:
                        line_data['monthly_values'][0] += move_amount
                        report_data[partner_id]['customer_monthly_totals'][0] += move_amount
                        report_totals['grand_monthly_totals'][0] += move_amount
            else:
                found_bucket = False
                for i, col_end in enumerate(month_columns):
                    bucket_start = start_date if i == 0 else month_columns[i-1]
                    
                    if i == 0:
                        is_in_bucket = next_ship_date <= col_end
                    else:
                        is_in_bucket = bucket_start < next_ship_date <= col_end

                    if is_in_bucket:
                        line_data['monthly_values'][i] += backlog_amount
                        report_data[partner_id]['customer_monthly_totals'][i] += backlog_amount
                        report_totals['grand_monthly_totals'][i] += backlog_amount
                        found_bucket = True
                        break
                if not found_bucket and next_ship_date < month_columns[0]:
                    line_data['monthly_values'][0] += backlog_amount
                    report_data[partner_id]['customer_monthly_totals'][0] += backlog_amount
                    report_totals['grand_monthly_totals'][0] += backlog_amount

            report_data[partner_id]['lines'].append(line_data)
            report_data[partner_id]['customer_total_price'] += total_price
            report_data[partner_id]['customer_total_backlog'] += backlog_amount
            
            report_totals['grand_total_price'] += total_price
            report_totals['grand_total_backlog'] += backlog_amount

        # Sort lines by Next Ship date (raw_ship_date) for each customer
        for partner_id in report_data:
            report_data[partner_id]['lines'].sort(key=lambda x: x.get('raw_ship_date') or datetime.max.date())

        sorted_customer_list = sorted(
            [c for c in report_data.values() if c['lines']], 
            key=lambda x: (
                min((l.get('raw_ship_date') or datetime.max.date()) for l in x['lines']),
                x['customer_name']
            )
        )

        return {
            'doc_ids': docids,
            'doc_model': 'order.backlog.wizard',
            'docs': wizard,
            'month_columns': [d.strftime('%d/%m/%y') for d in month_columns],
            'customers_data': sorted_customer_list,
            'totals': report_totals,
            'res_user': self.env.user,
            'res_company': self.env.company,
            'report_date': fields.Datetime.context_timestamp(self, datetime.now()).strftime('%d/%m/%y'),
            'report_time': fields.Datetime.context_timestamp(self, datetime.now()).strftime('%H:%M'),
        }

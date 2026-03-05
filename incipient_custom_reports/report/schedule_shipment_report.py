from odoo import api, fields, models
from collections import defaultdict
from datetime import datetime


class ReportScheduleShipment(models.AbstractModel):
    _name = 'report.incipient_custom_reports.report_schedule_shipment'
    _description = 'Schedule Shipment Report'

    def _get_carrier_name(self, picking):
        """Safely get carrier name from a delivery order (stock.picking)."""
        try:
            if picking and picking.carrier_id:
                return picking.carrier_id.name
        except Exception:
            pass
        try:
            if picking and picking.sale_id and picking.sale_id.carrier_id:
                return picking.sale_id.carrier_id.name
        except Exception:
            pass
        return ''

    @api.model
    def _get_report_values(self, docids, data=None):
        wizard = self.env['schedule.shipment.wizard'].browse(docids)
        start_date = wizard.start_date.strftime('%Y-%m-%d') if wizard.start_date else False
        end_date = wizard.end_date.strftime('%Y-%m-%d') if wizard.end_date else False

        # Moves in date range
        range_domain = [
            ('picking_id.picking_type_code', '=', 'outgoing'),
            ('state', 'not in', ['draft', 'cancel']),
            ('sale_line_id', '!=', False),
        ]
        if start_date:
            range_domain.append(('picking_id.scheduled_date', '>=', start_date))
        if end_date:
            range_domain.append(('picking_id.scheduled_date', '<=', end_date + ' 23:59:59'))

        range_moves = self.env['stock.move'].search(range_domain)
        range_moves = range_moves.sorted(key=lambda m: (m.picking_id.scheduled_date or datetime.min, m.id))

        report_lines = []
        for move in range_moves:
            so_line = move.sale_line_id
            
            # Line No
            all_so_lines = so_line.order_id.order_line.filtered(lambda l: not l.display_type)
            line_index = list(all_so_lines.ids).index(so_line.id) + 1

            # Carrier (Via)
            via = self._get_carrier_name(move.picking_id) or so_line.order_id.carrier_id.name

            # Ship Date
            ship_date = move.picking_id.scheduled_date.strftime('%d/%m/%y') if move.picking_id.scheduled_date else ''

            # Quantities for this specific split
            qty_shipped = move.quantity if move.state == 'done' else 0.0
            qty_to_ship = move.product_uom_qty if move.state != 'done' else 0.0

            report_lines.append({
                'order': so_line.order_id.name,
                'line_no': line_index,
                'customer': so_line.order_id.partner_id.name,
                'via': via,
                'part': so_line.product_id.display_name,
                'order_qty': so_line.product_uom_qty,
                'ship_date': ship_date,
                'qty_shipped': qty_shipped,
                'qty_to_ship': qty_to_ship,
            })

        formatted_start = wizard.start_date.strftime('%d/%m/%y') if wizard.start_date else ''
        formatted_end = wizard.end_date.strftime('%d/%m/%y') if wizard.end_date else ''

        now = fields.Datetime.context_timestamp(self, datetime.now())
        return {
            'doc_ids': docids,
            'doc_model': 'schedule.shipment.wizard',
            'start_date': formatted_start,
            'end_date': formatted_end,
            'report_lines': report_lines,
            'res_user': self.env.user,
            'res_company': self.env.company,
            'report_date': now.strftime('%d/%m/%y'),
            'report_time': now.strftime('%H:%M'),
        }

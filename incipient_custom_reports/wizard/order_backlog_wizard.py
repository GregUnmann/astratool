from odoo import api, fields, models, _

class OrderBacklogWizard(models.TransientModel):
    _name = 'order.backlog.wizard'
    _description = 'Order Backlog Report Wizard'

    start_date = fields.Date(string="Start Date", required=True, default=fields.Date.context_today)
    backlog_thru = fields.Selection([
        ('1', '1'),
        ('2', '2'),
        ('3', '3'),
        ('4', '4')
    ], string="Backlog Thru", required=True)
    partner_ids = fields.Many2many('res.partner', string="Customer")

    def action_print_report(self):
        report_action = self.env.ref(
            'incipient_custom_reports.action_report_order_backlog'
        ).report_action(self)
        report_action['close_on_report_download'] = True
        return report_action

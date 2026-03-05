from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class ScheduleShipmentWizard(models.TransientModel):
    _name = 'schedule.shipment.wizard'
    _description = 'Schedule Shipment Report Wizard'

    start_date = fields.Date(string="Start Date", required=True)
    end_date = fields.Date(string="End Date", required=True)

    @api.constrains('start_date', 'end_date')
    def _check_dates(self):
        for record in self:
            if record.start_date and record.end_date and record.start_date > record.end_date:
                raise ValidationError(_('Start Date cannot be greater than End Date.'))

    def action_print_report(self):
        report_action = self.env.ref(
            'incipient_custom_reports.action_report_schedule_shipment'
        ).report_action(self)
        report_action['close_on_report_download'] = True
        return report_action

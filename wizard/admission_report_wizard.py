# -*- coding: utf-8 -*-

from odoo import models, fields, api

class AdmissionReportWizard(models.TransientModel):
    _name = 'institute.admission.report.wizard'
    _description = 'Admission Report Wizard'

    date_from = fields.Date(string='From Date', required=True)
    date_to = fields.Date(string='To Date', required=True, default=fields.Date.context_today)
    report_type = fields.Selection([
        ('college', 'College Wise Admission'),
        ('course', 'Course Wise Admission'),
        ('source', 'Source Wise Admission'),
    ], string='Report Type', required=True, default='course')

    def action_generate_report(self):
        self.ensure_one()
        
        # Filter for Admitted / Won leads within the date range
        domain = [
            ('active', '=', True),
            ('probability', '=', 100),
            ('date_closed', '>=', self.date_from),
            ('date_closed', '<=', self.date_to),
        ]
        
        if self.report_type == 'college':
            group_by_field = 'admitted_campus'
            name = 'Campus Wise Admission'
        elif self.report_type == 'course':
            group_by_field = 'course_interested'
            name = 'Course Wise Admission'
        else:
            group_by_field = 'source_id'
            name = 'Source Wise Admission'
            
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'pivot,graph,tree,form',
            'domain': domain,
            'context': {
                'search_default_group_by_' + group_by_field: 1,
                'group_by': [group_by_field],
            }
        }

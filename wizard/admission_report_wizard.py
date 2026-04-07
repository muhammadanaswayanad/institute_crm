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
        ('batch', 'Batch Wise Admission'),
        ('officer', 'Admission Officer Wise Admission'),
    ], string='Report Type', required=True, default='course')

    def action_generate_report(self):
        self.ensure_one()
        
        # Populate missing admitted_campus data for existing "Won/Admitted" records
        if 'student.student' in self.env:
            empty_campus_leads = self.env['crm.lead'].search([
                ('admitted_campus', '=', False),
                ('probability', '=', 100)
            ])
            if empty_campus_leads:
                students = self.env['student.student'].search([
                    ('lead_id', 'in', empty_campus_leads.ids)
                ])
                for student in students:
                    if student.branch and student.lead_id:
                        student.lead_id.admitted_campus = student.branch.name
        
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
            measures = ['__count__']
        elif self.report_type == 'course':
            group_by_field = 'course_interested'
            name = 'Course Wise Admission'
            measures = ['__count__']
        elif self.report_type == 'batch':
            group_by_field = 'batch_id'
            name = 'Batch Wise Admission'
            measures = ['__count__', 'batch_target']
        elif self.report_type == 'officer':
            group_by_field = 'user_id'
            name = 'Admission Officer Wise Admission'
            measures = ['__count__']
        else:
            group_by_field = 'source_id'
            name = 'Source Wise Admission'
            measures = ['__count__']
            
        pivot_column_groupby = []
        if self.report_type == 'officer':
            pivot_column_groupby = ['date_closed:month']
            
        return {
            'name': name,
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'pivot,graph,tree,form',
            'domain': domain,
            'context': {
                'search_default_group_by_' + group_by_field: 1,
                'group_by': [group_by_field],
                'pivot_measures': measures,
                'pivot_column_groupby': pivot_column_groupby, 
            }
        }

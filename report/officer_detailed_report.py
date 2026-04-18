# -*- coding: utf-8 -*-
from odoo import api, models

class OfficerDetailedReport(models.AbstractModel):
    _name = 'report.institute_crm.report_officer_detailed'
    _description = 'Admission Officer Detailed Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['institute.admission.report.wizard'].browse(docids)
        doc = docs[0]
        domain = [
            ('active', '=', True),
            ('probability', '=', 100),
            ('date_closed', '>=', doc.date_from),
            ('date_closed', '<=', doc.date_to),
        ]
        
        leads = self.env['crm.lead'].search(domain)
        
        officer_data = {}
        for lead in leads:
            officer = lead.user_id.name if lead.user_id else 'Unknown Officer'
            course = lead.course_interested.name if lead.course_interested else ''
            source = lead.source_id.name if lead.source_id else ''
            campus = lead.admitted_campus or ''
            
            # Fetch Amount Paid from student
            amount_paid = 0.0
            if 'student.student' in self.env:
                student = self.env['student.student'].search([('lead_id', '=', lead.id)], limit=1)
                if student:
                    amount_paid = student.paid_amount
                    
            if officer not in officer_data:
                officer_data[officer] = []
                
            officer_data[officer].append({
                'course': course,
                'amount_paid': amount_paid,
                'source': source,
                'campus': campus,
            })
            
        return {
            'doc_ids': docids,
            'doc_model': 'institute.admission.report.wizard',
            'docs': docs,
            'officer_data': officer_data,
        }

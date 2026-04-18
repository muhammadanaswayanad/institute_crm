# -*- coding: utf-8 -*-
from odoo import api, models

class OfficerDetailedReport(models.AbstractModel):
    _name = 'report.institute_crm.report_officer_detailed'
    _description = 'Admission Officer Detailed Report'

    @api.model
    def _get_report_values(self, docids, data=None):
        docs = self.env['institute.admission.report.wizard'].browse(docids)
        doc = docs[0]
        # We query student.student directly to guarantee it matches the Student Management UI identically.
        domain = [
            ('enrollment_date', '>=', doc.date_from),
            ('enrollment_date', '<=', doc.date_to),
        ]
        
        # Optional: Apply campus filter if the wizard has branch_id
        if hasattr(doc, 'branch_id') and doc.branch_id:
            domain.append(('branch', '=', doc.branch_id.id))
            
        students = self.env['student.student'].search(domain)
        
        officer_data = {}
        for student in students:
            # user_id on student is 'Admitted By' -> Admission Officer
            officer = student.user_id.name if student.user_id else 'Unknown Officer'
            course = student.course_id.name if student.course_id else ''
            source = student.lead_id.source_id.name if student.lead_id and student.lead_id.source_id else ''
            campus = student.branch.name if student.branch else ''
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

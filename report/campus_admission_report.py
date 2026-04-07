# -*- coding: utf-8 -*-
from odoo import api, models

class CampusAdmissionReport(models.AbstractModel):
    _name = 'report.institute_crm.report_campus_wise'
    _description = 'Campus Wise Admission Report'

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
        if hasattr(doc, 'branch_id') and doc.branch_id:
            domain.append(('admitted_campus', '=', doc.branch_id.name))
        
        leads = self.env['crm.lead'].search(domain)
        
        campus_data = {}
        for lead in leads:
            campus = lead.admitted_campus or 'Unknown Campus'
            course = lead.course_interested.name if lead.course_interested else 'Unknown Course'
            
            batch_name = 'Unknown Batch'
            target = 0
            
            try:
                if lead.batch_id:
                    batch_name = lead.batch_id.name
            except Exception:
                pass
                
            try:
                target = lead.batch_target or 0
            except Exception:
                pass
            
            if campus not in campus_data:
                campus_data[campus] = {}
            if course not in campus_data[campus]:
                campus_data[campus][course] = []
            
            batch_entry = next((item for item in campus_data[campus][course] if item['batch_name'] == batch_name), None)
            if not batch_entry:
                batch_entry = {
                    'batch_name': batch_name,
                    'target': target,
                    'achieved': 0
                }
                campus_data[campus][course].append(batch_entry)
                
            batch_entry['achieved'] += 1
            
        return {
            'doc_ids': docids,
            'doc_model': 'institute.admission.report.wizard',
            'docs': docs,
            'campus_data': campus_data,
        }

# -*- coding: utf-8 -*-

from odoo import models, fields, api, tools


class CrmLeadReportInstitute(models.Model):
    """Report model for admission officer performance tracking"""
    _name = 'crm.lead.report.institute'
    _description = 'Institute CRM Lead Report'
    _auto = False
    _rec_name = 'user_id'
    _order = 'user_id'

    # Fields
    user_id = fields.Many2one('res.users', string='Admission Officer', readonly=True)
    overdue_count = fields.Integer(string='Overdue', readonly=True, help='Number of leads with past deadline')
    due_count = fields.Integer(string='Due', readonly=True, help='Number of leads with upcoming or today deadline')
    total_count = fields.Integer(string='Total Leads', readonly=True, help='Total number of assigned leads')
    active_count = fields.Integer(string='Active Leads', readonly=True, help='Leads not won or lost')
    won_count = fields.Integer(string='Won', readonly=True, help='Number of won leads')
    lost_count = fields.Integer(string='Lost', readonly=True, help='Number of lost leads')
    
    # Date field for filtering
    date_deadline = fields.Date(string='Deadline', readonly=True)
    create_date = fields.Datetime(string='Created On', readonly=True)

    def init(self):
        """Initialize the SQL view for the report"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            CREATE OR REPLACE VIEW %s AS (
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY user_id) as id,
                    user_id,
                    COUNT(*) as total_count,
                    COUNT(*) FILTER (
                        WHERE date_deadline < CURRENT_DATE 
                        AND active = true 
                        AND probability < 100
                        AND probability >= 0
                    ) as overdue_count,
                    COUNT(*) FILTER (
                        WHERE date_deadline >= CURRENT_DATE 
                        AND active = true 
                        AND probability < 100
                        AND probability >= 0
                    ) as due_count,
                    COUNT(*) FILTER (
                        WHERE active = true 
                        AND probability < 100
                        AND probability >= 0
                    ) as active_count,
                    COUNT(*) FILTER (WHERE probability = 100) as won_count,
                    COUNT(*) FILTER (WHERE probability = 0 AND active = false) as lost_count,
                    MAX(date_deadline) as date_deadline,
                    MAX(create_date) as create_date
                FROM 
                    crm_lead
                WHERE 
                    user_id IS NOT NULL
                GROUP BY 
                    user_id
            )
        """ % self._table
        self.env.cr.execute(query)

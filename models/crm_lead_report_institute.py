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
    overdue_count = fields.Integer(string='Overdue', readonly=True, help='Number of leads with past deadline (pending/unattended)')
    today_count = fields.Integer(string="Today's Activity", readonly=True, help='Number of leads with deadline today')
    scheduled_count = fields.Integer(string='Scheduled', readonly=True, help='Number of leads with future deadline')
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
                        WHERE date_deadline = CURRENT_DATE 
                        AND active = true 
                        AND probability < 100
                        AND probability >= 0
                    ) as today_count,
                    COUNT(*) FILTER (
                        WHERE date_deadline > CURRENT_DATE 
                        AND active = true 
                        AND probability < 100
                        AND probability >= 0
                    ) as scheduled_count,
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

    def action_view_all_leads(self):
        """Open all leads for this admission officer"""
        self.ensure_one()
        return {
            'name': f'All Leads - {self.user_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'tree,kanban,form,calendar,graph,activity',
            'domain': [('user_id', '=', self.user_id.id)],
            'context': {
                'default_user_id': self.user_id.id,
                'search_default_user_id': self.user_id.id,
            }
        }

    def action_view_overdue_leads(self):
        """Open overdue leads for this admission officer"""
        self.ensure_one()
        today = fields.Date.today()
        return {
            'name': f'Overdue Leads - {self.user_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'tree,kanban,form,calendar,activity',
            'domain': [
                ('user_id', '=', self.user_id.id),
                ('date_deadline', '<', today),
                ('active', '=', True),
                ('probability', '<', 100),
                ('probability', '>=', 0),
            ],
            'context': {
                'default_user_id': self.user_id.id,
            }
        }

    def action_view_today_leads(self):
        """Open today's leads for this admission officer"""
        self.ensure_one()
        today = fields.Date.today()
        return {
            'name': f"Today's Leads - {self.user_id.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'tree,kanban,form,calendar,activity',
            'domain': [
                ('user_id', '=', self.user_id.id),
                ('date_deadline', '=', today),
                ('active', '=', True),
                ('probability', '<', 100),
                ('probability', '>=', 0),
            ],
            'context': {
                'default_user_id': self.user_id.id,
            }
        }

    def action_view_scheduled_leads(self):
        """Open scheduled (future) leads for this admission officer"""
        self.ensure_one()
        today = fields.Date.today()
        return {
            'name': f'Scheduled Leads - {self.user_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'tree,kanban,form,calendar,activity',
            'domain': [
                ('user_id', '=', self.user_id.id),
                ('date_deadline', '>', today),
                ('active', '=', True),
                ('probability', '<', 100),
                ('probability', '>=', 0),
            ],
            'context': {
                'default_user_id': self.user_id.id,
            }
        }

    def action_view_active_leads(self):
        """Open active leads for this admission officer"""
        self.ensure_one()
        return {
            'name': f'Active Leads - {self.user_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'tree,kanban,form,calendar,activity',
            'domain': [
                ('user_id', '=', self.user_id.id),
                ('active', '=', True),
                ('probability', '<', 100),
                ('probability', '>=', 0),
            ],
            'context': {
                'default_user_id': self.user_id.id,
            }
        }


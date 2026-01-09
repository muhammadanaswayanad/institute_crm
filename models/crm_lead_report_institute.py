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

    def action_view_calendar(self):
        """Open calendar view showing all activities"""
        return {
            'name': 'Activities Calendar',
            'type': 'ir.actions.act_window',
            'res_model': 'mail.activity',
            'view_mode': 'calendar,tree,form',
            'domain': [
                ('res_model', '=', 'crm.lead'),
                ('user_id', 'in', self.env['crm.lead'].search([]).mapped('user_id').ids),
            ],
            'context': {
                'default_res_model': 'crm.lead',
            }
        }

    def init(self):
        """Initialize the SQL view for the report"""
        tools.drop_view_if_exists(self.env.cr, self._table)
        query = """
            CREATE OR REPLACE VIEW %s AS (
                SELECT 
                    ROW_NUMBER() OVER (ORDER BY user_id) as id,
                    user_id,
                    COUNT(DISTINCT lead_id) as total_count,
                    COUNT(DISTINCT CASE 
                        WHEN activity_date < CURRENT_DATE THEN lead_id 
                    END) as overdue_count,
                    COUNT(DISTINCT CASE 
                        WHEN activity_date = CURRENT_DATE THEN lead_id 
                    END) as today_count,
                    COUNT(DISTINCT CASE 
                        WHEN activity_date > CURRENT_DATE THEN lead_id 
                    END) as scheduled_count,
                    COUNT(DISTINCT CASE 
                        WHEN active = true AND probability < 100 AND probability >= 0 
                        THEN lead_id 
                    END) as active_count,
                    COUNT(DISTINCT CASE 
                        WHEN probability = 100 THEN lead_id 
                    END) as won_count,
                    COUNT(DISTINCT CASE 
                        WHEN probability = 0 AND active = false THEN lead_id 
                    END) as lost_count,
                    MAX(activity_date) as date_deadline,
                    MAX(create_date) as create_date
                FROM (
                    SELECT 
                        l.id as lead_id,
                        l.user_id,
                        l.active,
                        l.probability,
                        l.create_date,
                        a.date_deadline as activity_date
                    FROM 
                        crm_lead l
                    LEFT JOIN 
                        mail_activity a ON a.res_id = l.id 
                        AND a.res_model = 'crm.lead'
                        AND a.user_id = l.user_id
                    WHERE 
                        l.user_id IS NOT NULL
                ) as lead_activities
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
        # Get leads with activities that are overdue
        return {
            'name': f'Overdue Activities - {self.user_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'tree,kanban,form,calendar,activity',
            'domain': [
                ('user_id', '=', self.user_id.id),
                ('activity_ids.date_deadline', '<', today),
                ('activity_ids.user_id', '=', self.user_id.id),
            ],
            'context': {
                'default_user_id': self.user_id.id,
            }
        }

    def action_view_today_leads(self):
        """Open today's leads for this admission officer"""
        self.ensure_one()
        today = fields.Date.today()
        # Get leads with activities due today
        return {
            'name': f"Today's Activities - {self.user_id.name}",
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'tree,kanban,form,calendar,activity',
            'domain': [
                ('user_id', '=', self.user_id.id),
                ('activity_ids.date_deadline', '=', today),
                ('activity_ids.user_id', '=', self.user_id.id),
            ],
            'context': {
                'default_user_id': self.user_id.id,
            }
        }

    def action_view_scheduled_leads(self):
        """Open scheduled (future) leads for this admission officer"""
        self.ensure_one()
        today = fields.Date.today()
        # Get leads with activities scheduled for future
        return {
            'name': f'Scheduled Activities - {self.user_id.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'crm.lead',
            'view_mode': 'tree,kanban,form,calendar,activity',
            'domain': [
                ('user_id', '=', self.user_id.id),
                ('activity_ids.date_deadline', '>', today),
                ('activity_ids.user_id', '=', self.user_id.id),
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


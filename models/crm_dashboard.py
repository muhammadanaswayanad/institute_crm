from odoo import models, fields, api
from datetime import timedelta
import random

class CrmDashboard(models.AbstractModel):
    _name = 'crm.dashboard.data'
    _description = 'CRM Dashboard Data Provider'

    @api.model
    def get_dashboard_data(self):
        is_manager = self.env.user.has_group('sales_team.group_sale_manager')
        uid = self.env.uid
        today = fields.Date.context_today(self)
        end_of_week = today + timedelta(days=7)
        
        # Base Data Dictionary
        data = {
            'is_manager': is_manager,
            'today': today.strftime("%Y-%m-%d"),
        }
        
        user_name = self.env.user.name.split()[0] if self.env.user.name else 'there'

        
        if not is_manager:
            # NORMAL SALESPERSON LOGIC
            
            # 1. Motivational Quote
            quotes = [
                "The secret of getting ahead is getting started.",
                "Sales are contingent upon the attitude of the salesman.",
                "Every sale has five basic obstacles: no need, no money, no hurry, no desire, no trust.",
                "The best time to plant a tree was 20 years ago. The second best time is now.",
                "Success is not final, failure is not fatal: it is the courage to continue that counts.",
                "Don't watch the clock; do what it does. Keep going.",
                "Opportunities don't happen. You create them."
            ]
            data['quote'] = random.choice(quotes)
            
            # 2. Activities Today & This Week
            # We filter activities on CRM lead model
            Activity = self.env['mail.activity']
            
            base_domain = [('user_id', '=', uid), ('res_model', '=', 'crm.lead')]
            
            today_activities = Activity.search_read(
                base_domain + [('date_deadline', '<=', today)],
                ['res_name', 'summary', 'date_deadline', 'res_id', 'activity_type_id']
            )
            
            week_activities = Activity.search_read(
                base_domain + [('date_deadline', '>', today), ('date_deadline', '<=', end_of_week)],
                ['res_name', 'summary', 'date_deadline', 'res_id', 'activity_type_id']
            )
            
            lead_ids = [act['res_id'] for act in today_activities + week_activities]
            if lead_ids:
                leads_data = self.env['crm.lead'].search_read([('id', 'in', lead_ids)], ['id', 'student_name', 'name'])
                lead_map = {l['id']: (l['student_name'] or l['name']) for l in leads_data}
                for act in today_activities + week_activities:
                    act['display_name'] = lead_map.get(act['res_id'], act['res_name'])
            else:
                for act in today_activities + week_activities:
                    act['display_name'] = act['res_name']
            
            data['activities_today'] = today_activities
            data['activities_week'] = week_activities
            
            welcome_msgs = [
                f"Welcome {user_name}, let's get it done.",
                f"Hello {user_name}, ready to crush it today?",
                f"Great to see you {user_name}!"
            ]
            data['welcome_message'] = random.choice(welcome_msgs)

            
            # 3. Overall Leads Converted (Won)
            converted_leads = self.env['crm.lead'].search_count([
                ('user_id', '=', uid),
                ('stage_id.is_won', '=', True)
            ])
            data['converted_leads'] = converted_leads
            
            # 4. AI Suggestion finding old untouched leads
            suggestion = False
            last_week = fields.Datetime.now() - timedelta(days=3)
            forgotten_lead = self.env['crm.lead'].search([
                ('user_id', '=', uid),
                ('stage_id.is_won', '=', False),
                ('write_date', '<', last_week)
            ], limit=1, order='priority desc, write_date asc')
            
            if forgotten_lead:
                suggestion = {
                    'text': f"Lead '{forgotten_lead.name}' hasn't been updated in over 3 days. Send a follow up WhatsApp?",
                    'lead_id': forgotten_lead.id,
                    'lead_name': forgotten_lead.name
                }
            else:
                suggestion = {
                     'text': "You're all caught up! Keep finding new prospects.",
                     'lead_id': False,
                     'lead_name': False
                }
            
            data['ai_suggestion'] = suggestion
            
        else:
            # CRM ADMIN LOGIC
            
            # Overall salesperson performance
            leads_group = self.env['crm.lead'].read_group(
                [], 
                ['user_id', 'stage_id'], 
                ['user_id', 'stage_id'],
                lazy=False
            )
            
            performance = {}
            for res in leads_group:
                user_name = res['user_id'][1] if res['user_id'] else 'Unassigned'
                stage_name = res['stage_id'][1] if res['stage_id'] else 'New'
                count = res['__count']
                
                if user_name not in performance:
                    performance[user_name] = {'total': 0, 'won': 0, 'stages': {}}
                
                performance[user_name]['total'] += count
                # Assuming "Admitted" or "Won" in stage name or check if we want to search is_won specifically.
                # Actually, read_group doesn't easily expose is_won from stage. We can do separate query or assume stage logic
                performance[user_name]['stages'][stage_name] = count
            
            won_leads_group = self.env['crm.lead'].read_group(
                [('stage_id.is_won', '=', True)],
                ['user_id'],
                ['user_id']
            )
            for res in won_leads_group:
                user_name = res['user_id'][1] if res['user_id'] else 'Unassigned'
                if user_name in performance:
                    performance[user_name]['won'] = res['user_id_count']
            
            # Format performance for frontend charts
            perf_list = []
            for user, stats in performance.items():
                perf_list.append({
                    'user': user,
                    'total': stats['total'],
                    'won': stats['won']
                })
            perf_list.sort(key=lambda x: x['won'], reverse=True)
            data['salesperson_perf'] = perf_list
            
            # Global pending activities
            Activity = self.env['mail.activity']
            admin_domain = [('res_model', '=', 'crm.lead')]
            
            today_activities = Activity.search_read(
                admin_domain + [('date_deadline', '<=', today)],
                ['res_name', 'summary', 'date_deadline', 'res_id', 'user_id'],
                limit=20
            )
            
            week_activities = Activity.search_read(
                admin_domain + [('date_deadline', '>', today), ('date_deadline', '<=', end_of_week)],
                ['res_name', 'summary', 'date_deadline', 'res_id', 'user_id'],
                limit=20
            )
            
            # For admin, resolving user_id tuple to dict or primitive
            lead_ids = [act['res_id'] for act in today_activities + week_activities]
            if lead_ids:
                leads_data = self.env['crm.lead'].search_read([('id', 'in', lead_ids)], ['id', 'student_name', 'name'])
                lead_map = {l['id']: (l['student_name'] or l['name']) for l in leads_data}
            else:
                lead_map = {}
                
            for act in today_activities + week_activities:
                act['display_name'] = lead_map.get(act['res_id'], act['res_name'])
                if act.get('user_id'):
                    act['user_name'] = act['user_id'][1]
            
            team_today_count = Activity.search_count(admin_domain + [('date_deadline', '<=', today)])
            team_week_count = Activity.search_count(admin_domain + [('date_deadline', '>', today), ('date_deadline', '<=', end_of_week)])
            
            # Completed activities (messages logged by completed activities)
            completed_count = self.env['mail.message'].search_count([
                ('model', '=', 'crm.lead'),
                ('mail_activity_type_id', '!=', False)
            ])
            
            data['team_activities_today'] = today_activities
            data['team_activities_week'] = week_activities
            data['team_today_count'] = team_today_count
            data['team_week_count'] = team_week_count
            data['team_completed_count'] = completed_count
            
            # Average lead closure time
            won_leads = self.env['crm.lead'].search_read(
                [('stage_id.is_won', '=', True), ('date_closed', '!=', False), ('create_date', '!=', False)],
                ['create_date', 'date_closed']
            )
            if won_leads:
                total_seconds = sum((l['date_closed'] - l['create_date']).total_seconds() for l in won_leads)
                avg_days = (total_seconds / len(won_leads)) / 86400.0
                data['avg_lead_closure_days'] = round(avg_days, 1)
            else:
                data['avg_lead_closure_days'] = 0
            
            # Total admissions / total converted leads for the institute
            data['total_admissions'] = sum(stat['won'] for stat in perf_list)
            
        return data

from odoo import models, fields, api
from datetime import timedelta
import random
import json
import logging

_logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

# Removed ResUsers to avoid postgres schema bootloops

class CrmDashboard(models.AbstractModel):
    _name = 'crm.dashboard.data'
    _description = 'CRM Dashboard Data Provider'

    @api.model
    def save_sticky_note(self, text):
        self.env['ir.config_parameter'].sudo().set_param(f'dashboard_sticky_note_{self.env.uid}', text)
        return True

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
        
        # General Data
        welcome_msgs = [
            f"Welcome {user_name}, let's get it done.",
            f"Hello {user_name}, ready to crush it today?",
            f"Great to see you {user_name}!",
            f"Good to have you back, {user_name}!"
        ]
        data['welcome_message'] = random.choice(welcome_msgs)
        
        if not is_manager:
            # NORMAL SALESPERSON LOGIC
            
            # 1. Motivational Quote
            quotes = [
                "The secret of getting ahead is getting started.",
                "Sales are contingent upon the attitude of the salesman.",
                "Every sale has five basic obstacles: no need, no money, no hurry, no desire, no trust.",
                "The best time to plant a tree was 20 years ago. The second best time is now.",
                "Success is not final, failure is not fatal: it is the courage to continue that counts.",
                "Either you run the day, or the day runs you.",
                "Don't watch the clock; do what it does. Keep going.",
                "Your attitude, not your aptitude, will determine your altitude.",
                "Opportunities don't happen. You create them.",
                "Good things come to people who wait, but better things come to those who go out and get them.",
                "The harder you work, the luckier you get.",
                "Don't let the fear of losing be greater than the excitement of winning.",
                "Act as if what you do makes a difference. It does.",
                "Great things are done by a series of small things brought together.",
                "The way to get started is to quit talking and begin doing.",
                "Believe you can and you're halfway there.",
                "Setting goals is the first step in turning the invisible into the visible.",
                "Energy and persistence conquer all things.",
                "If you are not taking care of your customer, your competitor will.",
                "Growth and comfort do not coexist.",
                "To build a long-term, successful enterprise, when you don't close a sale, open a relationship."
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
            
            # 3. Overall Leads Converted (Won)
            converted_leads = self.env['crm.lead'].search_count([
                ('user_id', '=', uid),
                ('stage_id.is_won', '=', True)
            ])
            data['converted_leads'] = converted_leads
            
            data['ai_suggestions'] = []
            
        else:
            # CRM ADMIN LOGIC
            
            # --- 1. Problem Alerts ---
            three_days_ago = fields.Datetime.now() - timedelta(days=3)
            untouched_leads = self.env['crm.lead'].search_count([
                ('stage_id.is_won', '=', False),
                ('active', '=', True),
                ('write_date', '<', three_days_ago)
            ])
            data['alert_untouched_leads'] = untouched_leads

            last_week_start = today - timedelta(days=14)
            last_week_end = today - timedelta(days=7)
            this_week_won = self.env['crm.lead'].search_count([
                ('stage_id.is_won', '=', True),
                ('date_closed', '>=', last_week_end)
            ])
            last_week_won = self.env['crm.lead'].search_count([
                ('stage_id.is_won', '=', True),
                ('date_closed', '>=', last_week_start),
                ('date_closed', '<', last_week_end)
            ])
            data['alert_conversion_drop'] = last_week_won > this_week_won
            data['this_week_won'] = this_week_won
            data['last_week_won'] = last_week_won

            # --- 2. Team Comparison Heatmap & Performance ---
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
            
            perf_list = []
            low_conversion_reps = 0
            for user, stats in performance.items():
                win_rate = (stats['won'] / stats['total'] * 100) if stats['total'] > 0 else 0
                if win_rate < 2 and stats['total'] > 0:
                    low_conversion_reps += 1
                perf_list.append({
                    'user': user,
                    'total': stats['total'],
                    'won': stats['won'],
                    'win_rate': round(win_rate)
                })
            perf_list.sort(key=lambda x: x['won'], reverse=True)
            data['salesperson_perf'] = perf_list
            data['alert_low_conversion_reps'] = low_conversion_reps
            
            # --- 3. Lead Source Performance ---
            source_group = self.env['crm.lead'].read_group(
                [],
                ['source_id', 'stage_id'],
                ['source_id', 'stage_id'],
                lazy=False
            )
            source_perf = {}
            for res in source_group:
                src_name = res['source_id'][1] if res['source_id'] else 'Unknown'
                count = res['__count']
                if src_name not in source_perf:
                    source_perf[src_name] = {'total': 0, 'won': 0, 'lost': 0}
                source_perf[src_name]['total'] += count
            
            source_won = self.env['crm.lead'].read_group(
                [('stage_id.is_won', '=', True)],
                ['source_id'],
                ['source_id']
            )
            for res in source_won:
                src_name = res['source_id'][1] if res['source_id'] else 'Unknown'
                if src_name in source_perf:
                    source_perf[src_name]['won'] = res['source_id_count']
            
            source_lost = self.env['crm.lead'].read_group(
                [('active', '=', False)],
                ['source_id'],
                ['source_id']
            )
            for res in source_lost:
                src_name = res['source_id'][1] if res['source_id'] else 'Unknown'
                if src_name in source_perf:
                    source_perf[src_name]['lost'] = res['source_id_count']

            source_list = [{'source': k, **v} for k, v in source_perf.items()]
            source_list.sort(key=lambda x: x['total'], reverse=True)
            data['source_performance'] = source_list[:5]

            # --- 4. Time-based Trends (Last 7 Days) ---
            trend_dates = [(today - timedelta(days=i)).strftime('%Y-%m-%d') for i in range(6, -1, -1)]
            trend_admissions = {d: 0 for d in trend_dates}
            trend_activities = {d: 0 for d in trend_dates}
            
            recent_won = self.env['crm.lead'].search_read([
                ('stage_id.is_won', '=', True),
                ('date_closed', '>=', trend_dates[0])
            ], ['date_closed'])
            for rw in recent_won:
                d = rw['date_closed'].strftime('%Y-%m-%d') if rw['date_closed'] else None
                if d in trend_admissions:
                    trend_admissions[d] += 1
                    
            recent_activities = self.env['mail.message'].search_read([
                ('model', '=', 'crm.lead'),
                ('mail_activity_type_id', '!=', False),
                ('date', '>=', trend_dates[0])
            ], ['date'])
            for ra in recent_activities:
                d = ra['date'].strftime('%Y-%m-%d') if ra['date'] else None
                if d in trend_activities:
                    trend_activities[d] += 1

            data['time_trends'] = {
                'labels': [d[-5:] for d in trend_dates],
                'admissions': [trend_admissions[d] for d in trend_dates],
                'activities': [trend_activities[d] for d in trend_dates]
            }

            # --- 5. Funnel Conversion View ---
            stage_group = self.env['crm.lead'].read_group(
                [],
                ['stage_id'],
                ['stage_id']
            )
            funnel = [{'stage': res['stage_id'][1] if res['stage_id'] else 'Unknown', 'count': res['stage_id_count']} for res in stage_group]
            funnel.sort(key=lambda x: x['count'], reverse=True)
            data['funnel'] = funnel

            # --- 6. Revenue Intelligence ---
            students = self.env['student.student'].search_read(
                [('lead_id', '!=', False)],
                ['paid_amount', 'enrollment_date', 'user_id', 'lead_id']
            )
            
            total_revenue = sum(s.get('paid_amount', 0) for s in students)
            
            today_str = today.strftime('%Y-%m-%d')
            month_str = today.strftime('%Y-%m')
            
            today_revenue = sum(s.get('paid_amount', 0) for s in students if s.get('enrollment_date') and str(s.get('enrollment_date')).startswith(today_str))
            month_revenue = sum(s.get('paid_amount', 0) for s in students if s.get('enrollment_date') and str(s.get('enrollment_date')).startswith(month_str))
            
            revenue_per_rep = {}
            for s in students:
                rep_name = s['user_id'][1] if s.get('user_id') else 'Unassigned'
                if rep_name not in revenue_per_rep:
                    revenue_per_rep[rep_name] = 0
                revenue_per_rep[rep_name] += s.get('paid_amount', 0)
                
            rev_rep_list = [{'rep': k, 'revenue': v} for k, v in revenue_per_rep.items()]
            rev_rep_list.sort(key=lambda x: x['revenue'], reverse=True)
            
            avg_deal_value = total_revenue / len(students) if students else 0
            
            open_leads = self.env['crm.lead'].search_read(
                [('stage_id.is_won', '=', False), ('active', '=', True)],
                ['expected_revenue', 'course_interested']
            )
            
            forecasted_revenue = 0
            course_ids = [l['course_interested'][0] for l in open_leads if l.get('course_interested')]
            course_prices = {}
            if course_ids:
                courses = self.env['product.product'].search_read([('id', 'in', course_ids)], ['id', 'list_price'])
                course_prices = {c['id']: c['list_price'] for c in courses}
                
            for l in open_leads:
                if l.get('course_interested') and l['course_interested'][0] in course_prices:
                    forecasted_revenue += course_prices[l['course_interested'][0]]
                elif l.get('expected_revenue'):
                    forecasted_revenue += l['expected_revenue']
                    
            data['revenue'] = {
                'total': total_revenue,
                'today': today_revenue,
                'month': month_revenue,
                'avg_deal': avg_deal_value,
                'forecast': forecasted_revenue,
                'per_rep': rev_rep_list[:5]
            }

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
            
            completed_count = self.env['mail.message'].search_count([
                ('model', '=', 'crm.lead'),
                ('mail_activity_type_id', '!=', False)
            ])
            
            data['team_activities_today'] = today_activities
            data['team_activities_week'] = week_activities
            data['team_today_count'] = team_today_count
            data['team_week_count'] = team_week_count
            data['team_completed_count'] = completed_count
            
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
            
            data['total_admissions'] = sum(stat['won'] for stat in perf_list)
            data['admin_sticky_note'] = self.env['ir.config_parameter'].sudo().get_param(f'dashboard_sticky_note_{uid}', default='')
            
        return data

    @api.model
    def get_ai_suggestions(self):
        uid = self.env.uid
        api_key = self.env['ir.config_parameter'].sudo().get_param('institute_crm.openrouter_api_key')
        ai_suggestions = []
        
        if OpenAI and api_key:
            try:
                # Fetch 2 active, non-won leads
                target_leads = self.env['crm.lead'].search([
                    ('user_id', '=', uid),
                    ('stage_id.is_won', '=', False),
                    ('active', '=', True)
                ], limit=2, order='priority desc, write_date desc')
                
                if target_leads:
                    prompt_context = []
                    for lead in target_leads:
                        # Fetch up to 3 recent logs
                        logs = self.env['mail.message'].search_read([
                            ('model', '=', 'crm.lead'),
                            ('res_id', '=', lead.id),
                            ('message_type', 'in', ['comment', 'email'])
                        ], ['body', 'date'], limit=3, order='date desc')
                        
                        log_text = " \\n ".join([f"({log['date']}) {log['body']}" for log in logs])
                        
                        prompt_context.append({
                            'lead_id': lead.id,
                            'lead_name': lead.student_name or lead.name or 'Unknown Lead',
                            'recent_logs': log_text
                        })
                        
                    # Build prompt
                    salesperson_name = self.env.user.name or 'Salesperson'
                    company_name = self.env.company.name or 'our Institution'
                    sys_prompt = f"You are an AI sales assistant for {company_name}. The salesperson handling these leads is {salesperson_name}, and your goal is to sell admission into our courses (do not refer to 'products' or 'solutions', use 'courses' or 'programs'). Review the context for 2 leads. Suggest a short next action and a very brief, casual draft response (e.g. WhatsApp length) for each. Output carefully structured strict JSON ONLY, resolving into an array of EXACTLY 2 objects with keys: `lead_id` (integer), `lead_name` (string), `suggested_action` (string), and `draft_message` (string). No markdown block backticks around the json."
                    user_prompt = f"Leads Context: {json.dumps(prompt_context)}"
                    
                    client = OpenAI(
                        base_url="https://openrouter.ai/api/v1",
                        api_key=api_key
                    )
                    
                    response = client.chat.completions.create(
                        model="qwen/qwen-2.5-7b-instruct",
                        messages=[
                            {"role": "system", "content": sys_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=0.7,
                        response_format={"type": "json_object"}
                    )
                    
                    resp_content = response.choices[0].message.content
                    if resp_content:
                        # Strip potential markdown formatting sometimes returned by qwen despite instructions
                        resp_content = resp_content.strip()
                        if resp_content.startswith('```json'):
                            resp_content = resp_content[7:]
                        if resp_content.startswith('```'):
                            resp_content = resp_content[3:]
                        if resp_content.endswith('```'):
                            resp_content = resp_content[:-3]
                            
                        parsed_data = json.loads(resp_content)
                        # Handle both object wrapped array or direct array
                        if isinstance(parsed_data, dict):
                            for key, val in parsed_data.items():
                                if isinstance(val, list):
                                    ai_suggestions = val
                                    break
                            if not ai_suggestions:
                                ai_suggestions = [parsed_data]
                        elif isinstance(parsed_data, list):
                            ai_suggestions = parsed_data
                            
            except Exception as e:
                _logger.error("OpenRouter AI Suggestion Generation Failed: %s", str(e))
        
        if not ai_suggestions:
            # Fallback to old basic query if API fails, key missing, or openai absent
            last_week = fields.Datetime.now() - timedelta(days=3)
            forgotten_lead = self.env['crm.lead'].search([
                ('user_id', '=', uid),
                ('stage_id.is_won', '=', False),
                ('write_date', '<', last_week)
            ], limit=1, order='priority desc, write_date asc')
            
            if forgotten_lead:
                ai_suggestions = [{
                    'lead_id': forgotten_lead.id,
                    'lead_name': forgotten_lead.student_name or forgotten_lead.name,
                    'suggested_action': f"Lead '{forgotten_lead.student_name or forgotten_lead.name}' hasn't been updated in over 3 days.",
                    'draft_message': "Send a follow up WhatsApp to check on their interest."
                }]
            else:
                ai_suggestions = [{
                     'lead_id': False,
                     'lead_name': False,
                     'suggested_action': "Awesome! You're all caught up.",
                     'draft_message': "Keep finding new prospects and creating leads."
                }]
                
        return ai_suggestions

from odoo import models, fields, api
from datetime import datetime, timedelta, time
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
    def get_dashboard_data(self, timeframe='month'):
        is_manager = self.env.user.has_group('sales_team.group_sale_manager')
        uid = self.env.uid
        today = fields.Date.context_today(self)
        end_of_week = today + timedelta(days=7)
        
        # Base Data Dictionary
        data = {
            'is_manager': is_manager,
            'today': today.strftime("%Y-%m-%d"),
            'timeframe': timeframe,
        }
        user_name = self.env.user.name.split()[0] if self.env.user.name else 'there'
        
        # Fetch hidden users from security group
        hidden_group = self.env.ref('institute_crm.group_hide_from_dashboard', raise_if_not_found=False)
        if hidden_group:
            hidden_user_ids = hidden_group.users.ids
        else:
            hidden_user_ids = []
        
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
            
            # --- 1. Personal Conversion Metrics ---
            # User Win Rate
            user_total = self.env['crm.lead'].search_count([('user_id', '=', uid)])
            user_won = self.env['crm.lead'].search_count([('user_id', '=', uid), ('stage_id.is_won', '=', True)])
            user_win_rate = round((user_won / user_total * 100) if user_total else 0, 1)

            # Team Average
            team_total = self.env['crm.lead'].search_count([('user_id', '!=', False)])
            team_won = self.env['crm.lead'].search_count([('user_id', '!=', False), ('stage_id.is_won', '=', True)])
            team_win_rate = round((team_won / team_total * 100) if team_total else 0, 1)

            # Avg Time to Close
            user_won_leads = self.env['crm.lead'].search_read([('user_id', '=', uid), ('stage_id.is_won', '=', True)], ['day_close'])
            avg_close_time = sum(l['day_close'] for l in user_won_leads) / len(user_won_leads) if user_won_leads else 0

            # Top 3 Lost Reasons
            lost_group = self.env['crm.lead'].read_group(
                [('user_id', '=', uid), ('active', '=', False), ('lost_reason_id', '!=', False)],
                ['lost_reason_id'],
                ['lost_reason_id']
            )
            lost_group.sort(key=lambda x: x['lost_reason_id_count'], reverse=True)
            top_lost_reasons = [{'reason': r['lost_reason_id'][1], 'count': r['lost_reason_id_count']} for r in lost_group[:3]]

            # --- 2. Leaderboard ---
            first_of_month = today.replace(day=1)
            won_this_month = self.env['crm.lead'].sudo().read_group(
                [('stage_id.is_won', '=', True), ('date_closed', '>=', first_of_month)],
                ['user_id', 'day_close:avg'],
                ['user_id'],
                lazy=False
            )
            won_this_month.sort(key=lambda x: x['__count'], reverse=True)
            leaderboard = []
            top_closer = None
            fastest_closer = None
            min_close_time = float('inf')
            
            for index, res in enumerate(won_this_month):
                if not res['user_id']: continue
                u_id = res['user_id'][0]
                if u_id in hidden_user_ids: continue
                u_name = res['user_id'][1]
                count = res['__count']
                avg_close = res['day_close'] or 0
                
                badges = []
                if index == 0:
                    badges.append('🔥 Top Closer')
                    if top_closer is None: top_closer = u_id
                if avg_close < min_close_time and count > 0:
                    min_close_time = avg_close
                    fastest_closer = u_id
                
                leaderboard.append({
                    'user_id': u_id,
                    'user_name': u_name,
                    'won': count,
                    'badges': badges,
                    'rank': index + 1
                })
            data['leaderboard'] = leaderboard
            
            # Last month top 3
            first_of_last_month = (first_of_month - timedelta(days=1)).replace(day=1)
            won_last_month = self.env['crm.lead'].sudo().read_group(
                [('stage_id.is_won', '=', True), ('date_closed', '>=', first_of_last_month), ('date_closed', '<', first_of_month)],
                ['user_id'],
                ['user_id'],
                lazy=False
            )
            won_last_month.sort(key=lambda x: x['__count'], reverse=True)
            last_month_leaderboard = []
            for res in won_last_month:
                if not res['user_id']: continue
                u_id = res['user_id'][0]
                if u_id in hidden_user_ids: continue
                last_month_leaderboard.append({
                    'name': res['user_id'][1],
                    'won': res['__count']
                })
                if len(last_month_leaderboard) == 3:
                    break
            data['last_month_leaderboard'] = last_month_leaderboard
            
            for rep in leaderboard:
                if rep['user_id'] == fastest_closer:
                    rep['badges'].append('⚡ Fastest Closer')

            # --- 3. Activity Efficiency Score ---
            try:
                completed_activities = self.env['mail.message'].search_count([
                    ('author_id.user_ids', 'in', [uid]),
                    ('model', '=', 'crm.lead'),
                    ('subtype_id', '=', self.env.ref('mail.mt_activities').id)
                ])
            except ValueError:
                completed_activities = 0
            efficiency_score = round((user_won / completed_activities * 100) if completed_activities else 0, 1)

            # --- 4. Personal Trend Data ---
            last_week_start = today - timedelta(days=14)
            last_week_end = today - timedelta(days=7)
            this_week_won = self.env['crm.lead'].search_count([
                ('user_id', '=', uid), ('stage_id.is_won', '=', True), ('date_closed', '>=', last_week_end)
            ])
            last_week_won = self.env['crm.lead'].search_count([
                ('user_id', '=', uid), ('stage_id.is_won', '=', True),
                ('date_closed', '>=', last_week_start), ('date_closed', '<', last_week_end)
            ])
            trend_percent = round(((this_week_won - last_week_won) / last_week_won * 100) if last_week_won else (100 if this_week_won else 0))

            # --- 5. Micro Coaching Tips ---
            coaching_tips = []
            source_group = self.env['crm.lead'].read_group(
                [('user_id', '=', uid), ('stage_id.is_won', '=', True), ('source_id', '!=', False)],
                ['source_id'], ['source_id']
            )
            if source_group:
                source_group.sort(key=lambda x: x['source_id_count'], reverse=True)
                top_source = source_group[0]
                coaching_tips.append(f"Leads from {top_source['source_id'][1]} work best for you ({top_source['source_id_count']} wins).")
            
            user_won_leads_dates = self.env['crm.lead'].search_read([('user_id', '=', uid), ('stage_id.is_won', '=', True), ('date_closed', '!=', False)], ['date_closed'], limit=500)
            if user_won_leads_dates:
                import pytz
                user_tz = pytz.timezone(self.env.user.tz or 'UTC')
                hours = []
                for l in user_won_leads_dates:
                    if l['date_closed']:
                        utc_dt = pytz.utc.localize(l['date_closed'])
                        user_dt = utc_dt.astimezone(user_tz)
                        hours.append(user_dt.hour)
                
                if hours:
                    best_hour = max(set(hours), key=hours.count)
                    time_of_day = "morning" if best_hour < 12 else "afternoon" if best_hour < 17 else "evening"
                    display_hour = best_hour if best_hour <= 12 else best_hour - 12
                    display_hour = 12 if display_hour == 0 else display_hour
                    am_pm = "AM" if best_hour < 12 else "PM"
                    coaching_tips.append(f"You close most of your deals in the {time_of_day} (around {display_hour}:00 {am_pm}).")

            # --- Advanced Coaching Insights ---
            user_rank = next((r['rank'] for r in leaderboard if r['user_id'] == uid), None)
            if user_rank and user_rank > 3:
                top_3_won = next((r['won'] for r in leaderboard if r['rank'] == 3), 0)
                diff = top_3_won - user_won
                if diff > 0 and diff <= 5:
                    coaching_tips.append(f"⚡ You’re just {diff} deal{'s' if diff > 1 else ''} away from the Top 3!")

            if trend_percent > 0:
                coaching_tips.append(f"📈 Great momentum! Your win rate improved by +{trend_percent}% vs last week.")
            elif trend_percent < 0:
                coaching_tips.append(f"📉 Your win volume dropped {abs(trend_percent)}% vs last week. Let's push hard!")

            # Task Completion
            today_str = fields.Date.today()
            due_today_count = self.env['mail.activity'].search_count([
                ('user_id', '=', uid), ('res_model', '=', 'crm.lead'), ('date_deadline', '=', today_str)
            ])
            today_dt = datetime.combine(today, time.min)
            completed_today_count = self.env['mail.message'].search_count([
                ('author_id.user_ids', 'in', [uid]), ('model', '=', 'crm.lead'),
                ('subtype_id', '=', self.env.ref('mail.mt_activities').id),
                ('date', '>=', today_dt)
            ])
            total_today = due_today_count + completed_today_count
            if total_today > 0:
                pct = int((completed_today_count / total_today) * 100)
                if pct > 0:
                    coaching_tips.append(f"🏁 {pct}% of your scheduled tasks for today are completed.")

            # Missed yesterday
            yesterday = today - timedelta(days=1)
            missed_yesterday = self.env['mail.activity'].search_count([
                ('user_id', '=', uid), ('res_model', '=', 'crm.lead'), ('date_deadline', '=', yesterday)
            ])
            if missed_yesterday > 0:
                coaching_tips.append(f"⚠️ You missed {missed_yesterday} scheduled follow-up{'s' if missed_yesterday > 1 else ''} yesterday.")

            # Neglected leads
            two_days_ago = fields.Datetime.now() - timedelta(days=2)
            neglected_leads = self.env['crm.lead'].search_count([
                ('user_id', '=', uid), 
                ('stage_id.is_won', '=', False),
                ('active', '=', True),
                ('activity_ids', '=', False),
                ('write_date', '<', two_days_ago)
            ])
            if neglected_leads > 0:
                coaching_tips.append(f"🕰️ {neglected_leads} active leads haven't had any updates in over 48 hours.")

            if not coaching_tips:
                coaching_tips.append("Keep following up on your activities to discover your best closing strategies.")
            # --- 6. Priority Queue ---
            Activity = self.env['mail.activity']
            base_act_domain = [('user_id', '=', uid), ('res_model', '=', 'crm.lead')]
            
            overdue_activities = Activity.search_read(
                base_act_domain + [('date_deadline', '<', today)],
                ['res_name', 'summary', 'date_deadline', 'res_id', 'activity_type_id'], limit=15
            )
            due_today_activities = Activity.search_read(
                base_act_domain + [('date_deadline', '=', today)],
                ['res_name', 'summary', 'date_deadline', 'res_id', 'activity_type_id'], limit=15
            )
            hot_leads = self.env['crm.lead'].search_read([
                ('user_id', '=', uid), ('stage_id.is_won', '=', False), ('active', '=', True),
                '|', ('priority', '=', '3'), ('probability', '>=', 70)
            ], ['name', 'student_name', 'probability', 'priority'], limit=15)

            all_act_res_ids = [a['res_id'] for a in overdue_activities + due_today_activities]
            if all_act_res_ids:
                act_leads = self.env['crm.lead'].search_read([('id', 'in', all_act_res_ids)], ['id', 'student_name', 'name'])
                act_lead_map = {l['id']: (l['student_name'] or l['name']) for l in act_leads}
                for act in overdue_activities + due_today_activities:
                    act['display_name'] = act_lead_map.get(act['res_id'], act['res_name'])
            else:
                for act in overdue_activities + due_today_activities:
                    act['display_name'] = act['res_name']

            data.update({
                'current_uid': uid,
                'user_win_rate': user_win_rate,
                'team_win_rate': team_win_rate,
                'avg_close_time': round(avg_close_time, 1),
                'top_lost_reasons': top_lost_reasons,
                'leaderboard': leaderboard,
                'efficiency_score': efficiency_score,
                'trend_percent': trend_percent,
                'this_week_won': this_week_won,
                'coaching_tips': coaching_tips,
                'overdue_activities': overdue_activities,
                'due_today_activities': due_today_activities,
                'hot_leads': hot_leads,
                'domain_hot_leads': [('user_id', '=', uid), ('stage_id.is_won', '=', False), ('active', '=', True), '|', ('priority', '=', '3'), ('probability', '>=', 70)],
                'domain_overdue': base_act_domain + [('date_deadline', '<', today)],
                'domain_due_today': base_act_domain + [('date_deadline', '=', today)],
                'ai_suggestions': [],
                'converted_leads': user_won,
            })
            
            my_open_leads = self.env['crm.lead'].search([('user_id', '=', uid), ('stage_id.is_won', '=', False), ('active', '=', True)])
            my_revenue = sum(my_open_leads.mapped('expected_revenue'))
            my_avg_deal = my_revenue / len(my_open_leads) if my_open_leads else 0
            
            data['my_pipeline'] = {
                'expected_revenue': my_revenue,
                'avg_deal': round(my_avg_deal),
                'total_leads': len(my_open_leads)
            }
            
            # --- My Funnel ---
            unfolded_stages = self.env['crm.stage'].search([('fold', '=', False)])
            unfolded_stage_ids = unfolded_stages.ids
            stage_sequences = {s.id: s.sequence for s in unfolded_stages}
            
            my_stage_group = self.env['crm.lead'].read_group(
                [('user_id', '=', uid), ('stage_id.fold', '=', False)],
                ['stage_id'],
                ['stage_id']
            )
            my_funnel = [{'stage_id': res['stage_id'][0], 'stage': res['stage_id'][1] if res['stage_id'] else 'Unknown', 'count': res['stage_id_count']} 
                      for res in my_stage_group if res.get('stage_id') and res['stage_id'][0] in unfolded_stage_ids]
            my_funnel.sort(key=lambda x: stage_sequences.get(x['stage_id'], 0))
            data['my_funnel'] = my_funnel
            
        else:
            # NORMAL MANAGER LOGIC
            
            # --- 1. Problem Alerts ---
            three_days_ago = fields.Datetime.now() - timedelta(days=3)
            untouched_leads = self.env['crm.lead'].search_count([
                ('stage_id.is_won', '=', False),
                ('active', '=', True),
                ('write_date', '<', three_days_ago),
                ('stage_id.fold', '=', False)
            ])
            data['alert_untouched_leads'] = untouched_leads
            data['domain_untouched_leads'] = [('stage_id.is_won', '=', False), ('active', '=', True), ('write_date', '<', three_days_ago.strftime('%Y-%m-%d %H:%M:%S')), ('stage_id.fold', '=', False)]

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

            # --- SmartHive DNA: System Health Score ---
            total_pending = self.env['mail.activity'].search_count([('res_model', '=', 'crm.lead')])
            thirty_days_ago = today - timedelta(days=30)
            
            try:
                completed_30d = self.env['mail.message'].search_count([
                    ('model', '=', 'crm.lead'), 
                    ('subtype_id', '=', self.env.ref('mail.mt_activities').id),
                    ('date', '>=', thirty_days_ago)
                ])
            except ValueError:
                completed_30d = 0
                
            follow_up_score = round((completed_30d / (completed_30d + total_pending) * 100) if (completed_30d + total_pending) else 100)

            total_active = self.env['crm.lead'].search_count([('stage_id.is_won', '=', False), ('active', '=', True)])
            response_score = round(100 - ((untouched_leads / total_active) * 100) if total_active else 100)

            total_won = self.env['crm.lead'].search_count([('stage_id.is_won', '=', True)])
            total_lost = self.env['crm.lead'].search_count([('active', '=', False), ('probability', '=', 0)])
            conversion_score = round((total_won / (total_won + total_lost) * 100) if (total_won + total_lost) else 0)

            overdue_pending = self.env['mail.activity'].search_count([('res_model', '=', 'crm.lead'), ('date_deadline', '<', today)])
            overload_score = round(100 - ((overdue_pending / total_pending) * 100) if total_pending else 100)

            dna_score = round((follow_up_score + response_score + conversion_score + overload_score) / 4)

            data.update({
                'dna_score': dna_score,
                'dna_follow_up': follow_up_score,
                'dna_response': response_score,
                'dna_conversion': conversion_score,
                'dna_overload': overload_score
            })

            # --- 2. Team Comparison Heatmap & Performance ---
            heatmap_domain = []
            if timeframe == 'month':
                first_of_month = today.replace(day=1)
                heatmap_domain = [('create_date', '>=', first_of_month)]

            leads_group = self.env['crm.lead'].read_group(
                heatmap_domain, 
                ['user_id', 'stage_id'], 
                ['user_id', 'stage_id'],
                lazy=False
            )
            
            performance = {}
            sales_users = self.env['res.users'].search([
                ('share', '=', False),
                ('groups_id', 'in', self.env.ref('sales_team.group_sale_salesman').id)
            ])
            for u in sales_users:
                if u.id not in hidden_user_ids:
                    performance[u.name] = {'user_id': u.id, 'total': 0, 'won': 0, 'stages': {}}
            
            for res in leads_group:
                user_id = res['user_id'][0] if res['user_id'] else False
                if user_id in hidden_user_ids:
                    continue
                
                user_name = res['user_id'][1] if res['user_id'] else 'Unassigned'
                stage_name = res['stage_id'][1] if res['stage_id'] else 'New'
                count = res['__count']
                
                if user_name not in performance:
                    performance[user_name] = {'user_id': user_id, 'total': 0, 'won': 0, 'stages': {}}
                
                performance[user_name]['total'] += count
                performance[user_name]['stages'][stage_name] = count
            
            won_domain = [('stage_id.is_won', '=', True)]
            if timeframe == 'month':
                won_domain.append(('date_closed', '>=', first_of_month))
                
            won_leads_group = self.env['crm.lead'].read_group(
                won_domain,
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
                if stats['total'] == 0 and stats['won'] > 0:
                    stats['total'] = stats['won']
                win_rate = (stats['won'] / stats['total'] * 100) if stats['total'] > 0 else 0
                if win_rate < 2 and stats['total'] > 0:
                    low_conversion_reps += 1
                perf_list.append({
                    'user': user,
                    'user_id': stats.get('user_id'),
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
                src_id = res['source_id'][0] if res['source_id'] else False
                src_name = res['source_id'][1] if res['source_id'] else 'Unknown'
                count = res['__count']
                if src_name not in source_perf:
                    source_perf[src_name] = {'source_id': src_id, 'total': 0, 'won': 0, 'lost': 0}
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
            source_list.sort(key=lambda x: x['won'], reverse=True)
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
            unfolded_stages = self.env['crm.stage'].search([('fold', '=', False)])
            unfolded_stage_ids = unfolded_stages.ids
            stage_sequences = {s.id: s.sequence for s in unfolded_stages}
            
            stage_group = self.env['crm.lead'].read_group(
                [('stage_id.fold', '=', False)],
                ['stage_id'],
                ['stage_id']
            )
            funnel = [{'stage_id': res['stage_id'][0], 'stage': res['stage_id'][1] if res['stage_id'] else 'Unknown', 'count': res['stage_id_count']} 
                      for res in stage_group if res.get('stage_id') and res['stage_id'][0] in unfolded_stage_ids]
            funnel.sort(key=lambda x: stage_sequences.get(x['stage_id'], 0))
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

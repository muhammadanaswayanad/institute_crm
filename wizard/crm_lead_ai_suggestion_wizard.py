from odoo import api, fields, models
from odoo.exceptions import UserError
import json
import logging

_logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class CrmLeadAiSuggestionWizard(models.TransientModel):
    _name = 'crm.lead.ai.suggestion.wizard'
    _description = 'AI Lead Suggestion Wizard'

    lead_id = fields.Many2one('crm.lead', string='Lead', required=True)
    suggested_action = fields.Text(string='Suggested Action', readonly=False)
    draft_message = fields.Text(string='Draft Message', readonly=False)
    is_generated = fields.Boolean(default=False)

    def action_generate_suggestion(self):
        self.ensure_one()
        api_key = self.env['ir.config_parameter'].sudo().get_param('institute_crm.openrouter_api_key')
        
        if not OpenAI or not api_key:
            raise UserError("OpenRouter API is not configured. Please add the API key in Settings.")
            
        lead = self.lead_id
        try:
            # Fetch recent logs
            logs = self.env['mail.message'].search_read([
                ('model', '=', 'crm.lead'),
                ('res_id', '=', lead.id),
                ('message_type', 'in', ['comment', 'email'])
            ], ['body', 'date'], limit=5, order='date desc')
            
            log_text = " \\n ".join([f"({log['date']}) {log['body']}" for log in logs])
            
            context_data = {
                'lead_name': lead.student_name or lead.name,
                'course_interested': lead.course_interested.name if lead.course_interested else 'Unknown Course',
                'contact_status': dict(lead._fields['contact_status'].selection).get(lead.contact_status, 'Unknown') if lead.contact_status else 'Unknown',
                'contact_remarks': lead.contact_remarks or 'No remarks',
                'stage': lead.stage_id.name if lead.stage_id else 'New',
                'recent_logs': log_text
            }
            
            salesperson_name = self.env.user.name or 'Salesperson'
            company_name = self.env.company.name or 'our Institution'
            
            sys_prompt = (
                f"You are an AI sales assistant for {company_name}. The salesperson handling this lead is {salesperson_name}. "
                "Your goal is to sell admission into our courses (do not refer to 'products' or 'solutions', use 'courses' or 'programs'). "
                "Review the context for this single lead, including their course interested, contact status, stage, and recent communication logs. "
                "Suggest a short next action for the salesperson and a very brief, casual draft response (extremely short WhatsApp length, 1-2 sentences maximum) ready to copy. "
                "Output carefully structured strict JSON ONLY, resolving into exactly one object with keys: `suggested_action` (string) and `draft_message` (string). "
                "No markdown block backticks around the json."
            )
            user_prompt = f"Lead Context: {json.dumps(context_data)}"
            
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
                resp_content = resp_content.strip()
                if resp_content.startswith('```json'):
                    resp_content = resp_content[7:]
                if resp_content.startswith('```'):
                    resp_content = resp_content[3:]
                if resp_content.endswith('```'):
                    resp_content = resp_content[:-3]
                    
                parsed_data = json.loads(resp_content)
                self.suggested_action = parsed_data.get('suggested_action', 'Could not generate action.')
                self.draft_message = parsed_data.get('draft_message', 'Could not generate message.')
                self.is_generated = True
                
            return {
                'type': 'ir.actions.act_window',
                'res_model': 'crm.lead.ai.suggestion.wizard',
                'res_id': self.id,
                'view_mode': 'form',
                'target': 'new',
            }
        except Exception as e:
            _logger.error("OpenRouter Lead AI Suggestion Failed: %s", str(e))
            raise UserError(f"Failed to generate suggestion: {str(e)}")

    def action_close(self):
        return {'type': 'ir.actions.act_window_close'}

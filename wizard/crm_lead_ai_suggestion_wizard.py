from odoo import api, fields, models

class CrmLeadAiSuggestionWizard(models.TransientModel):
    _name = 'crm.lead.ai.suggestion.wizard'
    _description = 'AI Lead Suggestion Wizard'

    lead_id = fields.Many2one('crm.lead', string='Lead', required=True)
    suggested_action = fields.Text(string='Suggested Action', readonly=True)
    draft_message = fields.Text(string='Draft Message', readonly=True)

    def action_close(self):
        return {'type': 'ir.actions.act_window_close'}

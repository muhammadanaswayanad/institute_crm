from odoo import fields, models

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    institute_crm_openrouter_api_key = fields.Char(
        string='OpenRouter API Key',
        config_parameter='institute_crm.openrouter_api_key',
        help="API Key for OpenRouter to grab LLM AI suggestions horizontally across the CRM Dashboard."
    )

from odoo import models, fields

class ResUsers(models.Model):
    _inherit = 'res.users'

    # hide_from_dashboard = fields.Boolean(
    #     string="Hide from CRM Dashboard", 
    #     help="If checked, this user will not appear on the CRM Dashboard leaderboards or heatmaps."
    # )

from odoo import models, api
import logging

_logger = logging.getLogger(__name__)

class SaaSMenuRestriction(models.AbstractModel):
    _name = 'saas.menu.restriction'
    _description = 'Utility to dynamicially restrict SaaS menus'

    @api.model
    def apply_restrictions(self):
        super_admin_group = self.env.ref('institute_crm.group_saas_super_admin', raise_if_not_found=False)
        if not super_admin_group:
            _logger.error("SaaS Super Admin group not found. Cannot restrict menus.")
            return

        menus_to_restrict = {
            'Settings': 'base.menu_administration',
            'Apps': 'base.menu_management',
            'Link Tracker': 'link_tracker.menu_link_tracker_root',
            'Surveys': 'survey.menu_surveys',
            'Email Marketing': 'mass_mailing.mass_mailing_menu_root',
            'Project': 'project.menu_main_pm',
            'Invoicing': 'account.menu_finance',
            'Dashboards': 'board.menu_board_root',
            'Social Dashboard': 'social.menu_social_global',
            'Employees': 'hr.menu_hr_root',
            'Sales': 'sale.sale_menu_root',
            'SmartHive Client': 'smarthive_client.menu_root'
        }

        for display_name, xml_id in menus_to_restrict.items():
            menu = self.env.ref(xml_id, raise_if_not_found=False)
            if not menu:
                # Fallback: Find root menu by exact display name
                menu = self.env['ir.ui.menu'].search([('name', '=', display_name), ('parent_id', '=', False)], limit=1)
            
            if menu:
                # Remove all existing groups and add strictly the Super Admin group
                menu.write({'groups_id': [(6, 0, [super_admin_group.id])]})
                _logger.info("Restricted menu '%s' to only SaaS Super Admin.", display_name)
            else:
                _logger.info("Menu '%s' not found. Skipping restriction.", display_name)

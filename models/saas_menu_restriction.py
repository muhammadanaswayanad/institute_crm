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

        menus_to_restrict = [
            'base.menu_administration',            # Settings
            'base.menu_management',                # Apps
            'link_tracker.menu_link_tracker_root', # Link Tracker
            'survey.menu_surveys',                 # Surveys
            'mass_mailing.mass_mailing_menu_root', # Email Marketing
            'project.menu_main_pm',                # Project
            'account.menu_finance',                # Invoicing
            'board.menu_board_root',               # Dashboards
            'social.menu_social_global'            # Social Dashboard
        ]

        for xml_id in menus_to_restrict:
            menu = self.env.ref(xml_id, raise_if_not_found=False)
            if menu:
                # Remove all existing groups and add strictly the Super Admin group
                menu.write({'groups_id': [(6, 0, [super_admin_group.id])]})
                _logger.info(f"Restricted menu '{xml_id}' to only SaaS Super Admin.")
            else:
                _logger.info(f"Menu '{xml_id}' not found. Skipping restriction.")

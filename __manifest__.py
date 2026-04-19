# -*- coding: utf-8 -*-
{
    'name': 'Institute CRM',
    'version': '17.0.1.0.0',
    'category': 'CRM/Education',
    'summary': 'Simplified CRM system for educational institutes',
    'description': """
        Institute CRM - Simplified Student Lead Management
        ===================================================
        
        This module provides a simplified CRM interface tailored for educational institutes:
        
        Key Features:
        * Student-focused fields (Student Name, Parent Name, Qualification, School/College)
        * Lead source tracking (Meta Facebook/Instagram, Google, Purchased, Referral)
        * Custom contact status workflow
        * Simplified form views removing complex CRM fields
        * Institute-specific pipeline stages
        
        Perfect for institutes that find the standard Odoo CRM too complicated.
    """,
    'author': 'Custom Development',
    'website': '',
    'depends': ['crm'],
    'external_dependencies': {'python': ['openai']},
    'data': [
        'security/saas_security.xml',
        'security/ir.model.access.csv',
        # 'data/crm_stage_data.xml',  # Commented out to prevent duplicate stages on upgrade
        'data/crm_actions.xml',
        'views/institute_crm_views.xml',
        'views/institute_crm_report_views.xml',
        'views/admission_report_wizard_views.xml',
        'wizard/crm_lead_ai_suggestion_wizard_views.xml',
        'report/campus_admission_report.xml',
        'report/officer_detailed_report.xml',
        'views/institute_crm_menu.xml',
        'views/crm_dashboard_views.xml',
        'views/res_config_settings_views.xml',
        'data/saas_menu_restrictions.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'institute_crm/static/src/css/crm_dashboard.scss',
            'institute_crm/static/src/js/crm_dashboard.js',
            'institute_crm/static/src/xml/crm_dashboard.xml',
        ],
    },
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

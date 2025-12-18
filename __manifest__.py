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
    'data': [
        'security/ir.model.access.csv',
        # 'data/crm_stage_data.xml',  # Commented out to prevent duplicate stages on upgrade
        'data/crm_actions.xml',
        'views/institute_crm_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}

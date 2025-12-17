# -*- coding: utf-8 -*-

from odoo import models, fields, api


class CrmLeadInstitute(models.Model):
    """Extend CRM Lead with institute-specific fields for student management"""
    _inherit = 'crm.lead'

    # Student Information
    student_name = fields.Char(
        string='Student Name',
        help='Full name of the student'
    )
    parent_name = fields.Char(
        string='Parent Name',
        help='Name of parent or guardian'
    )
    student_phone = fields.Char(
        string='Student Number',
        help='Primary contact number for the student'
    )
    alternative_phone = fields.Char(
        string='Alternative Number',
        help='Alternative contact number'
    )
    district = fields.Char(
        string='District',
        help='District in the address'
    )

    # Academic Background
    present_qualification = fields.Selection([
        ('12_science', '12th Science'),
        ('12_commerce', '12th Commerce'),
        ('12_humanities', '12th Humanities'),
        ('graduate', 'Graduate'),
        ('postgraduate', 'Post Graduate'),
    ], string='Present Qualification', help='Current educational qualification')
    
    school_college = fields.Char(
        string='School/College',
        help='Current or previous institution name'
    )
    
    course_interested = fields.Char(
        string='Course Interested',
        help='Course the student is interested in'
    )

    # Lead Source Information
    lead_source_type = fields.Selection([
        ('meta_facebook', 'Meta Facebook'),
        ('meta_instagram', 'Meta Instagram'),
        ('google', 'Google'),
        ('purchased', 'Purchased'),
        ('referral', 'Referral'),
    ], string='Lead Source', help='Source from which the lead was generated')
    
    referral_type = fields.Selection([
        ('student', 'Student'),
        ('staff', 'Staff'),
        ('teachers', 'Teachers'),
    ], string='Referral Type', help='Type of referral if source is referral')
    
    is_referral = fields.Boolean(
        string='Is Referral',
        compute='_compute_is_referral',
        store=True,
        help='Technical field to show/hide referral type'
    )

    # Contact Status Workflow
    contact_status = fields.Selection([
        ('connected', 'Connected'),
        ('not_connected', 'Not Connected'),
        ('switched_off', 'Switched Off'),
        ('number_not_in_use', 'Number Not In Use'),
    ], string='Contact Status', help='Status of the first contact attempt')
    
    follow_up_status = fields.Selection([
        ('contacted', 'Contacted'),
        ('not_contacted', 'Not Contacted'),
    ], string='Follow-up Status', help='Status after initial contact')
    
    contact_remarks = fields.Text(
        string='Contact Remarks',
        help='Remarks about contact attempts and conversations'
    )
    
    follow_up_date = fields.Date(
        string='Follow-up Date',
        help='Next follow-up date'
    )
    
    show_follow_up_fields = fields.Boolean(
        string='Show Follow-up Fields',
        compute='_compute_show_follow_up_fields',
        store=True,
        help='Technical field to show/hide follow-up fields'
    )

    @api.depends('lead_source_type')
    def _compute_is_referral(self):
        """Compute if the lead source is referral to show/hide referral type field"""
        for record in self:
            record.is_referral = record.lead_source_type == 'referral'

    @api.depends('contact_status')
    def _compute_show_follow_up_fields(self):
        """Compute if follow-up fields should be shown based on contact status"""
        for record in self:
            record.show_follow_up_fields = record.contact_status == 'connected'

    @api.onchange('lead_source_type')
    def _onchange_lead_source_type(self):
        """Clear referral type when source is not referral"""
        if self.lead_source_type != 'referral':
            self.referral_type = False

    @api.onchange('contact_status')
    def _onchange_contact_status(self):
        """Clear follow-up fields when contact status changes from connected"""
        if self.contact_status != 'connected':
            self.follow_up_status = False
            self.follow_up_date = False

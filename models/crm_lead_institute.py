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
    district = fields.Selection([
        ('thiruvananthapuram', 'Thiruvananthapuram'),
        ('kollam', 'Kollam'),
        ('pathanamthitta', 'Pathanamthitta'),
        ('alappuzha', 'Alappuzha'),
        ('kottayam', 'Kottayam'),
        ('idukki', 'Idukki'),
        ('ernakulam', 'Ernakulam'),
        ('thrissur', 'Thrissur'),
        ('palakkad', 'Palakkad'),
        ('malappuram', 'Malappuram'),
        ('kozhikode', 'Kozhikode'),
        ('wayanad', 'Wayanad'),
        ('kannur', 'Kannur'),
        ('kasaragod', 'Kasaragod'),
        ('outside_kerala', 'Outside Kerala'),
    ], string='District', help='District in Kerala or outside')

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
    
    course_interested = fields.Many2one(
        'product.product',
        string='Course Interested',
        help='Course the student is interested in',
        domain=[('type', '=', 'service')]
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

    def action_sync_student_fields(self):
        """Sync student fields with standard CRM fields for existing leads"""
        for record in self:
            vals = {}
            # Sync student_phone to phone
            if record.student_phone and record.student_phone != record.phone:
                vals['phone'] = record.student_phone
            # Sync phone to student_phone if student_phone is empty
            elif record.phone and not record.student_phone:
                vals['student_phone'] = record.phone
            
            # Sync with partner if exists
            if record.partner_id:
                # Sync student_name to partner name
                if record.student_name and record.student_name != record.partner_id.name:
                    record.partner_id.name = record.student_name
                # Sync partner name to student_name if student_name is empty
                elif record.partner_id.name and not record.student_name:
                    vals['student_name'] = record.partner_id.name
                    
                # Sync phone with partner
                if record.phone and record.phone != record.partner_id.phone:
                    record.partner_id.phone = record.phone
            # No partner but student_name exists - set contact_name
            elif record.student_name and not record.contact_name:
                vals['contact_name'] = record.student_name
            
            if vals:
                record.write(vals)
        
        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': 'Sync Complete',
                'message': f'{len(self)} lead(s) synchronized successfully!',
                'type': 'success',
                'sticky': False,
            }
        }

    # Sync student fields with standard CRM fields
    @api.onchange('student_name')
    def _onchange_student_name(self):
        """Sync student name to contact name"""
        if self.student_name and not self.partner_id:
            # Student name changed but no contact exists
            # We'll create contact when lead is saved
            self.contact_name = self.student_name
        elif self.student_name and self.partner_id:
            # Update existing contact name
            self.partner_id.name = self.student_name

    @api.onchange('partner_id')
    def _onchange_partner_id(self):
        """Sync contact name to student name"""
        if self.partner_id and self.partner_id.name:
            self.student_name = self.partner_id.name
        if self.partner_id and self.partner_id.phone:
            self.student_phone = self.partner_id.phone
            self.phone = self.partner_id.phone

    @api.onchange('student_phone')
    def _onchange_student_phone(self):
        """Sync student phone to standard phone field"""
        if self.student_phone:
            self.phone = self.student_phone
            if self.partner_id:
                self.partner_id.phone = self.student_phone

    @api.onchange('phone')
    def _onchange_phone(self):
        """Sync standard phone to student phone"""
        if self.phone:
            self.student_phone = self.phone

    @api.model_create_multi
    def create(self, vals_list):
        """Override create to sync fields"""
        for vals in vals_list:
            # Sync student_name with contact_name for contact creation
            if vals.get('student_name') and not vals.get('contact_name'):
                vals['contact_name'] = vals['student_name']
            # Sync student_phone with phone
            if vals.get('student_phone') and not vals.get('phone'):
                vals['phone'] = vals['student_phone']
        return super().create(vals_list)

    def write(self, vals):
        """Override write to sync fields"""
        # Sync student_name to partner
        if vals.get('student_name') and self.partner_id:
            self.partner_id.name = vals['student_name']
        # Sync student_phone to phone and partner
        if vals.get('student_phone'):
            vals['phone'] = vals['student_phone']
            if self.partner_id:
                self.partner_id.phone = vals['student_phone']
        # Sync phone to student_phone
        if vals.get('phone') and not vals.get('student_phone'):
            vals['student_phone'] = vals['phone']
        return super().write(vals)

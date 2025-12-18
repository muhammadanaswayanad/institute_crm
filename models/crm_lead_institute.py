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
    
    joining_frequency = fields.Char(
        string='Joining Frequency',
        help='When the student plans to join (e.g., January 2024, Next semester)'
    )

    # No custom lead source - using standard source_id field from Odoo CRM

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



    @api.depends('contact_status')
    def _compute_show_follow_up_fields(self):
        """Compute if follow-up fields should be shown based on contact status"""
        for record in self:
            record.show_follow_up_fields = record.contact_status == 'connected'

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
            
            # Sync alternative_phone to mobile
            if record.alternative_phone and record.alternative_phone != record.mobile:
                vals['mobile'] = record.alternative_phone
            # Sync mobile to alternative_phone if alternative_phone is empty
            elif record.mobile and not record.alternative_phone:
                vals['alternative_phone'] = record.mobile
            
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
                    
                # Sync mobile with partner
                if record.mobile and record.mobile != record.partner_id.mobile:
                    record.partner_id.mobile = record.mobile
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
        if self.partner_id and self.partner_id.mobile:
            self.alternative_phone = self.partner_id.mobile
            self.mobile = self.partner_id.mobile

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

    @api.onchange('alternative_phone')
    def _onchange_alternative_phone(self):
        """Sync alternative phone to standard mobile field"""
        if self.alternative_phone:
            self.mobile = self.alternative_phone
            if self.partner_id:
                self.partner_id.mobile = self.alternative_phone

    @api.onchange('mobile')
    def _onchange_mobile(self):
        """Sync standard mobile to alternative phone"""
        if self.mobile:
            self.alternative_phone = self.mobile

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
            # Sync alternative_phone with mobile
            if vals.get('alternative_phone') and not vals.get('mobile'):
                vals['mobile'] = vals['alternative_phone']
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
        # Sync alternative_phone to mobile and partner
        if vals.get('alternative_phone'):
            vals['mobile'] = vals['alternative_phone']
            if self.partner_id:
                self.partner_id.mobile = vals['alternative_phone']
        # Sync mobile to alternative_phone
        if vals.get('mobile') and not vals.get('alternative_phone'):
            vals['alternative_phone'] = vals['mobile']
        return super().write(vals)

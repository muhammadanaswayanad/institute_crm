# -*- coding: utf-8 -*-

from odoo import models, fields, api
from odoo.exceptions import ValidationError, UserError
import datetime
import re
import json
import logging

_logger = logging.getLogger(__name__)

try:
    from openai import OpenAI
except ImportError:
    OpenAI = None



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
    
    admitted_campus = fields.Char(
        string='Admitted Campus',
        help='Campus name where the student was admitted'
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
        """Override create to sync fields and schedule activity"""
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
        
        leads = super().create(vals_list)
        
        # Skip activity scheduling during import to avoid email sender errors
        if not self._context.get('import_file'):
            for lead in leads:
                if lead.user_id:
                    lead._schedule_salesperson_activity(lead.user_id)
        return leads

    def write(self, vals):
        """Override write to sync fields and schedule activity"""
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

        # Capture user_id change for activity scheduling
        user_id_changed = 'user_id' in vals
        
        res = super(CrmLeadInstitute, self).write(vals)
        
        if user_id_changed and vals.get('user_id'):
            # Schedule activity for the new salesperson
            new_user = self.env['res.users'].browse(vals['user_id'])
            for lead in self:
                lead._schedule_salesperson_activity(new_user)
        return res

    def _schedule_salesperson_activity(self, user):
        """Schedule a call activity for the salesperson for the next day"""
        for lead in self:
            date_deadline = fields.Date.today() + datetime.timedelta(days=1)
            # Use existing activity_schedule method from mail.thread
            lead.activity_schedule(
                'mail.mail_activity_data_call',
                user_id=user.id,
                date_deadline=date_deadline,
                summary='Follow-up Call (New Assignment)'
            )

    @api.constrains('phone', 'mobile', 'student_phone', 'alternative_phone', 'type', 'active')
    def _check_duplicate_phones(self):
        """Check for duplicate phone numbers across leads and opportunities"""
        # Skip duplicate check during data import to allow bulk imports without interruption
        if self._context.get('import_file'):
            return
        for record in self:
            if not record.active:
                continue

            # Gather all numbers to check
            numbers = []
            if record.phone: numbers.append(record.phone)
            if record.mobile: numbers.append(record.mobile)
            if record.student_phone: numbers.append(record.student_phone)
            if record.alternative_phone: numbers.append(record.alternative_phone)

            check_digits = set()
            for num in numbers:
                # Extract only digits
                digits = re.sub(r'\D', '', num)
                if len(digits) >= 10:
                    check_digits.add(digits[-10:])
                elif len(digits) > 5:  # Arbitrary min length if less than 10 digits
                    check_digits.add(digits)

            if not check_digits:
                continue

            for digits in check_digits:
                # Use SQL REGEXP_REPLACE to strip non-digits from db fields and compare rightmost chars
                # This ensures we handle spaces, +91, dashes existing in the database as well
                self.env.cr.execute(r"""
                    SELECT id, name, type FROM crm_lead 
                    WHERE id != %s 
                    AND active = true
                    AND (
                        REGEXP_REPLACE(phone, '\D', '', 'g') LIKE %s OR 
                        REGEXP_REPLACE(mobile, '\D', '', 'g') LIKE %s OR
                        REGEXP_REPLACE(student_phone, '\D', '', 'g') LIKE %s OR
                        REGEXP_REPLACE(alternative_phone, '\D', '', 'g') LIKE %s
                    )
                    LIMIT 1
                """, (
                    record.id, 
                    f'%{digits}', 
                    f'%{digits}', 
                    f'%{digits}', 
                    f'%{digits}'
                ))
                
                res = self.env.cr.fetchone()
                if res:
                    dup_id, dup_name, dup_type = res
                    record_type = "Opportunity" if dup_type == 'opportunity' else "Lead"
                    raise ValidationError(
                        f"Duplicate Prevention: A {record_type} with this phone number already exists!\\n"
                        f"Existing Record: {dup_name}"
                    )

    def action_get_ai_suggestion(self):
        self.ensure_one()
        api_key = self.env['ir.config_parameter'].sudo().get_param('institute_crm.openrouter_api_key')
        
        if not OpenAI or not api_key:
            raise UserError("OpenRouter API is not configured. Please add the API key in Settings.")
            
        try:
            # Fetch recent logs
            logs = self.env['mail.message'].search_read([
                ('model', '=', 'crm.lead'),
                ('res_id', '=', self.id),
                ('message_type', 'in', ['comment', 'email'])
            ], ['body', 'date'], limit=5, order='date desc')
            
            log_text = " \\n ".join([f"({log['date']}) {log['body']}" for log in logs])
            
            context_data = {
                'lead_name': self.student_name or self.name,
                'course_interested': self.course_interested.name if self.course_interested else 'Unknown Course',
                'contact_status': dict(self._fields['contact_status'].selection).get(self.contact_status, 'Unknown') if self.contact_status else 'Unknown',
                'contact_remarks': self.contact_remarks or 'No remarks',
                'stage': self.stage_id.name if self.stage_id else 'New',
                'recent_logs': log_text
            }
            
            salesperson_name = self.env.user.name or 'Salesperson'
            company_name = self.env.company.name or 'our Institution'
            
            sys_prompt = (
                f"You are an AI sales assistant for {company_name}. The salesperson handling this lead is {salesperson_name}. "
                "Your goal is to sell admission into our courses (do not refer to 'products' or 'solutions', use 'courses' or 'programs'). "
                "Review the context for this single lead, including their course interested, contact status, stage, and recent communication logs. "
                "Suggest a short next action for the salesperson and a very brief, casual draft response (extremely short WhatsApp length, 1-2 sentences maximum) ready to copy. "
                "Output carefully structured strict JSON ONLY, resolving into exactly one object with keys: `suggested_action` (string) and `draft_message` (string). "
                "No markdown block backticks around the json."
            )
            user_prompt = f"Lead Context: {json.dumps(context_data)}"
            
            client = OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=api_key
            )
            
            response = client.chat.completions.create(
                model="qwen/qwen-2.5-7b-instruct",
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.7,
                response_format={"type": "json_object"}
            )
            
            resp_content = response.choices[0].message.content
            if resp_content:
                resp_content = resp_content.strip()
                if resp_content.startswith('```json'):
                    resp_content = resp_content[7:]
                if resp_content.startswith('```'):
                    resp_content = resp_content[3:]
                if resp_content.endswith('```'):
                    resp_content = resp_content[:-3]
                    
                parsed_data = json.loads(resp_content)
                suggested_action = parsed_data.get('suggested_action', 'Could not generate action.')
                draft_message = parsed_data.get('draft_message', 'Could not generate message.')
                
                wizard = self.env['crm.lead.ai.suggestion.wizard'].create({
                    'lead_id': self.id,
                    'suggested_action': suggested_action,
                    'draft_message': draft_message,
                    'is_generated': True
                })
                
                return {
                    'name': 'AI Suggestion',
                    'type': 'ir.actions.act_window',
                    'view_mode': 'form',
                    'res_model': 'crm.lead.ai.suggestion.wizard',
                    'res_id': wizard.id,
                    'target': 'new',
                }
        except Exception as e:
            _logger.error("OpenRouter Lead AI Suggestion Failed: %s", str(e))
            raise UserError(f"Failed to generate suggestion: {str(e)}")

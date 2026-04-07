import sys

file_path = '../student_management/views/crm_lead_views.xml'
with open(file_path, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    if "</odoo>" in line:
        new_lines.append("""
    <!-- Add Batch to Search View -->
    <record id="view_institute_crm_lead_search_inherit_student_management" model="ir.ui.view">
        <field name="name">institute.crm.lead.search.inherit.student_management</field>
        <field name="model">crm.lead</field>
        <field name="inherit_id" ref="institute_crm.view_institute_crm_lead_search"/>
        <field name="arch" type="xml">
            <xpath expr="//filter[@name='group_by_admitted_campus']" position="after">
                <filter string="Batch" name="group_by_batch_id" context="{'group_by': 'batch_id'}"/>
            </xpath>
        </field>
    </record>
""")
    new_lines.append(line)

with open(file_path, 'w') as f:
    f.writelines(new_lines)
print("Patched completely.")

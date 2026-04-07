import sys

file_path = '../student_management/models/crm_lead.py'
with open(file_path, 'r') as f:
    lines = f.readlines()

new_lines = []
for line in lines:
    new_lines.append(line)
    if "batch_id = fields.Many2one('student.batch', string='Batch', help='Select the batch for this lead')" in line:
        new_lines.append("    batch_target = fields.Integer(\n")
        new_lines.append("        string='Batch Target',\n")
        new_lines.append("        related='batch_id.target_admission',\n")
        new_lines.append("        store=True,\n")
        new_lines.append("        group_operator='avg',\n")
        new_lines.append("        help='Target number of admissions for the selected batch'\n")
        new_lines.append("    )\n")

with open(file_path, 'w') as f:
    f.writelines(new_lines)
print("Patched successfully!")

# Integration with student_management Module

The Institute CRM addon is designed to work seamlessly with the existing `student_management` module.

## What Was Integrated

### 1. Student Onboard Button
- **Location:** Header of the CRM lead form
- **Label:** "Student Onboard"
- **Visibility:** Only shown when:
  - Lead is in a won stage (`is_won_stage == True`)
  - Student profile has not been created yet (`student_profile_created == False`)
- **Action:** Opens the student creation wizard from the `student_management` module

### 2. Student Count Stat Button
- **Location:** Smart button box (top-right of form)
- **Icon:** fa-id-badge
- **Display:** Shows count of student records created from this lead
- **Action:** Opens a list view of related student records
- **Visibility:** Only shown when `student_count > 0`

### 3. Required Fields
Added three hidden fields to support the `student_management` integration:
- `student_profile_created` - Boolean flag indicating if student was onboarded
- `is_won_stage` - Boolean indicating if lead is in won stage
- `student_count` - Integer count of linked student records

## How It Works

1. When a lead progresses to a won stage (e.g., "Admission"), the `is_won_stage` field becomes True
2. The "Student Onboard" button appears in the header
3. Clicking the button opens the student creation wizard
4. After creating a student record, `student_profile_created` becomes True
5. The onboard button hides, and the student count stat button appears
6. Users can click the stat button to view/manage the created student record

## Technical Implementation

The integration was achieved using **dual view inheritance** in the `student_management` module:

### 1. Standard CRM Inheritance
**View ID:** `crm_lead_view_form_inherit`
- Inherits from: `crm.crm_lead_view_form` (standard Odoo CRM form)
- Injects buttons into users who don't have `institute_crm` installed

### 2. Institute CRM Inheritance
**View ID:** `crm_lead_view_form_inherit_institute_crm`
- Inherits from: `institute_crm.view_institute_crm_lead_form`
- Injects the same buttons into the simplified institute form
- Uses XPath expressions tailored to institute_crm's structure

### How It Works
1. The `institute_crm` form includes an empty `<div name="button_box">` element
2. When both modules are installed, `student_management` detects the institute_crm view
3. The second inheritance view activates and injects buttons into the institute_crm form
4. This prevents duplicate buttons and ensures consistent behavior

### Key Changes Made

**In `institute_crm/views/institute_crm_views.xml`:**
- Added `<div class="oe_button_box" name="button_box">` to the form (empty, for injection)
- Kept the form priority at `1` for higher precedence

**In `student_management/views/crm_lead_views.xml`:**
- Original inheritance for standard CRM remains unchanged
- Added new `crm_lead_view_form_inherit_institute_crm` record
- Uses XPath `//header/field[@name='stage_id']` to inject onboard button
- Uses `<div name="button_box" position="inside">` to inject stat button

This approach ensures **maximum compatibility**:
- ✅ Works when only `student_management` is installed
- ✅ Works when only `institute_crm` is installed  
- ✅ Works when both modules are installed together
- ✅ No duplicate buttons
- ✅ No dependency required from `institute_crm` to `student_management`

## Testing the Integration

To verify the integration works:
1. Install both `institute_crm` and `student_management` modules
2. Create a new student lead
3. Move it through the pipeline to the "Admission" stage
4. Verify the "Student Onboard" button appears
5. Click the button and create a student record
6. Verify the button hides and the student count stat button appears
7. Click the stat button to view the student record

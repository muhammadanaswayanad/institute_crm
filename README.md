# Institute CRM for Odoo 17

## Overview

Institute CRM is a simplified CRM module specifically designed for educational institutes. It addresses the complexity of standard Odoo CRM by providing a streamlined, student-focused interface.

## Features

### SimplifiedForm Interface
- **Student Information**: Student name, parent name, contact numbers, address with district
- **Academic Background**: Current qualification (12th Science/Commerce/Humanities, Graduate, Post Graduate), school/college, course interested
- **Lead Source Tracking**: Meta Facebook, Meta Instagram, Google, Purchased, Referral (with sub-types: Student, Staff, Teachers)
- **Contact Status Workflow**: Track contact attempts (Connected, Not Connected, Switched Off, Number Not In Use) with follow-up management

### Custom Pipeline Stages
Pre-configured stages tailored for institute admissions:
1. New Inquiry
2. Contacted
3. Interested
4. Counselling Scheduled
5. Counselling Done
6. Admission (Won)
7. Lost

### Views
- **Kanban View**: Visual pipeline with student cards showing key information
- **Tree View**: List view with essential columns (student, parent, phone, course, status)
- **Form View**: Simplified form removing complex CRM fields (Expected Revenue, Probability, etc.)
- **Search & Filters**: Filter by contact status, lead source, qualification, follow-up dates

## Installation

1. Copy the `institute_crm` folder to your Odoo custom addons directory
2. Restart Odoo server
3. Go to Apps menu, update app list
4. Search for "Institute CRM" and click Install

## Usage

### Creating a New Student Lead

1. Navigate to **Institute CRM** > **Student Leads**
2. Click **New**
3. Fill in the student information:
   - Lead title (e.g., "Inquiry for Computer Science")
   - Student name and parent name
   - Contact numbers
   - Address and district
4. Add academic background:
   - Select present qualification
   - Enter school/college name
   - Specify course interested
5. Set lead source and contact status
6. Add remarks and set follow-up date if connected
7. Save the record

### Managing the Pipeline

Use the **Kanban** view to visualize and manage your student admission pipeline:
- Drag and drop cards between stages
- Click on cards to view/edit details
- Use filters to find specific leads
- Group by salesperson, team, or contact status

### Reporting

Access **Reporting** > **Pipeline Analysis** to:
- View pipeline statistics
- Analyze conversion rates
- Track team performance
- Monitor lead sources effectiveness

## Configuration

### Customizing Stages

Go to **Configuration** > **Stages** to:
- Add custom stages
- Modify existing stages
- Set stage requirements

### Managing Teams

Go to **Configuration** > **Sales Teams** to:
- Create teams
- Assign team members
- Set team targets

## Technical Details

- **Module Name**: institute_crm
- **Version**: 17.0.1.0.0
- **Depends on**: crm
- **License**: LGPL-3

## Support

For issues or feature requests, please contact your development team.

/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";

export class CrmDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        
        this.state = useState({
            data: null,
            isLoading: true,
        });

        onWillStart(async () => {
            await this.loadData();
        });
    }

    async loadData() {
        this.state.isLoading = true;
        try {
            this.state.data = await this.orm.call(
                "crm.dashboard.data",
                "get_dashboard_data",
                []
            );
        } catch (e) {
            console.error("Error loading dashboard data:", e);
            this.state.data = { error: true };
        }
        this.state.isLoading = false;
    }

    // Handlers
    openLead(leadId) {
        if (!leadId) return;
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: 'crm.lead',
            res_id: leadId,
            views: [[false, 'form']],
            target: 'current',
        });
    }

    openActivity(activityModel, activityResId) {
        if (!activityModel || !activityResId) return;
        this.action.doAction({
            type: 'ir.actions.act_window',
            res_model: activityModel,
            res_id: activityResId,
            views: [[false, 'form']],
            target: 'current',
        });
    }
    
    openConvertedLeads(isManager) {
        let domain = [['stage_id.is_won', '=', true]];
        if (!isManager) {
            domain.push(['user_id', '=', this.env.session.uid]);
        }
        
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Converted Leads',
            res_model: 'crm.lead',
            view_mode: 'kanban,tree,form',
            views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
            domain: domain,
            target: 'current',
        });
    }
}

CrmDashboard.template = "institute_crm.CrmDashboard";

registry.category("actions").add("institute_crm_dashboard", CrmDashboard);

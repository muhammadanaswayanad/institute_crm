/** @odoo-module **/

import { Component, useState, onWillStart } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";

export class CrmDashboard extends Component {
    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.notification = useService("notification");
        
        this.state = useState({
            data: null,
            isLoading: true,
            aiSuggestions: null,
            isAiLoading: false,
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

    async fetchAiSuggestions() {
        this.state.isAiLoading = true;
        try {
            this.state.aiSuggestions = await this.orm.call(
                "crm.dashboard.data",
                "get_ai_suggestions",
                []
            );
        } catch (e) {
            console.error("Error loading AI suggestions:", e);
            this.state.aiSuggestions = [];
        }
        this.state.isAiLoading = false;
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
    
    openPipeline() {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: 'Pipeline',
            res_model: 'crm.lead',
            view_mode: 'kanban,tree,form',
            views: [[false, 'kanban'], [false, 'list'], [false, 'form']],
            context: {'default_type': 'opportunity', 'search_default_assigned_to_me': 1},
            target: 'current',
        });
    }

    openConvertedLeads(isManager) {
        let domain = [['stage_id.is_won', '=', true]];
        if (!isManager) {
            domain.push(['user_id', '=', session.uid]);
        }
        this.openLeadsList(domain, 'Converted Leads');
    }

    openLeadsList(domain, title) {
        this.action.doAction({
            type: 'ir.actions.act_window',
            name: title || 'Leads',
            res_model: 'crm.lead',
            view_mode: 'list,kanban,form',
            views: [[false, 'list'], [false, 'kanban'], [false, 'form']],
            domain: domain,
            target: 'current',
        });
    }

    async copyDraft(text) {
        if (!text) return;
        try {
            await navigator.clipboard.writeText(text);
            this.notification.add("Draft copied to clipboard!", { type: 'success' });
        } catch (err) {
            console.error("Failed to copy text: ", err);
            this.notification.add("Failed to copy text.", { type: 'danger' });
        }
    }

    async onChangeStickyNote(ev) {
        const text = ev.target.value;
        try {
            await this.orm.call(
                "crm.dashboard.data",
                "save_sticky_note",
                [text]
            );
            // Optionally, add a subtle notification if desired. We avoid standard loading overlay.
        } catch (e) {
            console.error("Error saving sticky note:", e);
        }
    }
}

CrmDashboard.template = "institute_crm.CrmDashboard";

registry.category("actions").add("institute_crm_dashboard", CrmDashboard);

/** @odoo-module **/

import { registry } from "@web/core/registry";
import { Component, onWillStart, useState } from "@odoo/owl";
import { useService } from "@web/core/utils/hooks";
import { standardActionServiceProps } from "@web/webclient/actions/action_service";
import { ControlPanel } from "@web/search/control_panel/control_panel";

class LarkTableView extends Component {
    static components = { ControlPanel };
    static props = { ...standardActionServiceProps };
    static template = "lark_table_view_template";

    setup() {
        this.action = useService("action");
        this.orm = useService("orm");
        this.state = useState({ fields: [], rows: [] });
        this.display = useState({ title: this.props.action && this.props.action.name ? this.props.action.name : "" });

        onWillStart(async () => {
            const tableId = this.props.action.params.table_id;
            // Load table data
            const data = await this.orm.call(
                "lark.file.bitable.table",
                "get_table_data",
                [[tableId]]
            );
            this.state.fields = data.fields;
            this.state.rows = data.rows;

            // Prefer action name from backend; fallback to record read if empty
            if (!this.display.title) {
                const records = await this.orm.read(
                    "lark.file.bitable.table",
                    [tableId],
                    ["name"]
                );
                this.display.title = records && records[0] ? records[0].name : this.display.title;
            }
        });
    }
}

registry.category("actions").add("lark_table_view", LarkTableView);

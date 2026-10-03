app_name = "bk_account"
app_title = "BK Account"
app_publisher = "Bipin Kole"
app_description = "Accounting Management System"
app_email = "bipinkole0110@gmail.com"
app_license = "mit"


# =========================================================
# DOCUMENT EVENTS
# =========================================================

AI_INDEXER = "bk_account.api.ai.indexer.index_document"

doc_events = {
    "Sales Invoice": {
        "on_submit": "bk_account.tally.api.sales_invoice_on_submit",
        "on_cancel": "bk_account.tally.api.sales_invoice_on_cancel",
        "on_trash": "bk_account.tally.api.sales_invoice_on_trash",
        "after_insert": AI_INDEXER,
        "on_update": AI_INDEXER
    },

    "Purchase Invoice": {
        "on_submit": "bk_account.tally.api.purchase_invoice_on_submit",
        "on_cancel": "bk_account.tally.api.purchase_invoice_on_cancel",
        "on_trash": "bk_account.tally.api.purchase_invoice_on_trash",
        "after_insert": AI_INDEXER,
        "on_update": AI_INDEXER
    },

    "Payment Entry": {
        "on_submit": "bk_account.tally.api.payment_entry_on_submit",
        "on_cancel": "bk_account.tally.api.payment_entry_on_cancel",
        "on_trash": "bk_account.tally.api.payment_entry_on_trash",
        "after_insert": AI_INDEXER,
        "on_update": AI_INDEXER
    },

    "Journal Entry": {
        "on_submit": "bk_account.tally.api.journal_entry_on_submit",
        "on_cancel": "bk_account.tally.api.journal_entry_on_cancel",
        "on_trash": "bk_account.tally.api.journal_entry_on_trash",
        "after_insert": AI_INDEXER,
        "on_update": AI_INDEXER
    },

    "Customer": {
        "after_insert": [
            "bk_account.tally.api.customer_after_insert",
            AI_INDEXER
        ],
        "on_update": [
            "bk_account.tally.api.customer_after_update",
            AI_INDEXER
        ]
    },

    "Supplier": {
        "after_insert": [
            "bk_account.tally.api.supplier_after_insert",
            AI_INDEXER
        ],
        "on_update": [
            "bk_account.tally.api.supplier_after_update",
            AI_INDEXER
        ]
    },

    "Item": {
        "after_insert": [
            "bk_account.tally.api.item_after_insert",
            AI_INDEXER
        ],
        "on_update": [
            "bk_account.tally.api.item_after_update",
            AI_INDEXER
        ]
    },

    "Item Group": {
        "after_insert": [
            "bk_account.tally.api.item_group_after_insert",
            AI_INDEXER
        ],
        "on_update": [
            "bk_account.tally.api.item_group_after_update",
            AI_INDEXER
        ],
        "on_trash": "bk_account.tally.api.item_group_on_trash"
    },

    "Account": {
        "after_insert": [
            "bk_account.tally.api.account_after_insert",
            AI_INDEXER
        ],
        "on_update": [
            "bk_account.tally.api.account_after_update",
            AI_INDEXER
        ],
        "on_trash": "bk_account.tally.api.account_on_trash"
    },

    "Cost Center": {
        "after_insert": [
            "bk_account.tally.api.cost_center_after_insert",
            AI_INDEXER
        ],
        "on_update": [
            "bk_account.tally.api.cost_center_after_update",
            AI_INDEXER
        ],
        "on_trash": "bk_account.tally.api.cost_center_on_trash"
    },

    "Warehouse": {
        "after_insert": [
            "bk_account.tally.api.warehouse_after_insert",
            AI_INDEXER
        ],
        "on_update": [
            "bk_account.tally.api.warehouse_after_update",
            AI_INDEXER
        ],
        "on_trash": "bk_account.tally.api.warehouse_on_trash"
    },

    "UOM": {
        "after_insert": [
            "bk_account.tally.api.uom_after_insert",
            AI_INDEXER
        ],
        "on_update": [
            "bk_account.tally.api.uom_after_update",
            AI_INDEXER
        ],
        "on_trash": "bk_account.tally.api.uom_on_trash"
    }
}


# =========================================================
# ERP AI ASSISTANT
# =========================================================

app_include_js = "/assets/bk_account/js/erp_ai_assistant.js"
app_include_css = "/assets/bk_account/css/erp_ai_assistant.css"


import json
import frappe


INDEX_DOCTYPES = [
    "Customer",
    "Supplier",
    "Item",
    "Item Group",
    "Company",
    "Account",
    "Warehouse",
    "UOM",
    "Cost Center",
    "Employee",
    "Sales Invoice",
    "Purchase Invoice",
    "Payment Entry",
    "Journal Entry",
]


def build_searchable_data(doc):
    """Create a compact searchable snapshot of an ERPNext document."""
    data = {}

    meta = frappe.get_meta(doc.doctype)

    for field in meta.fields:
        fieldname = field.fieldname

        if not fieldname:
            continue

        if field.fieldtype == "Table":
            continue

        value = doc.get(fieldname)

        if value is None:
            continue

        if isinstance(value, (str, int, float, bool)):
            data[fieldname] = value
        else:
            data[fieldname] = str(value)

    return data


def index_document(doc):
    """
    Create or update the persistent ERP AI Index record
    for one ERPNext document.

    This function does not send ERP data to Ollama.
    """

    if not doc:
        return

    if doc.doctype not in INDEX_DOCTYPES:
        return

    searchable_data = build_searchable_data(doc)

    existing_name = frappe.db.exists(
        "ERP AI Index",
        {
            "source_doctype": doc.doctype,
            "document_name": doc.name,
        },
    )

    values = {
        "source_doctype": doc.doctype,
        "document_name": doc.name,
        "modified": doc.modified,
        "searchable_data": json.dumps(
            searchable_data,
            default=str,
            ensure_ascii=False,
        ),
    }

    if existing_name:
        frappe.db.set_value(
            "ERP AI Index",
            existing_name,
            values,
        )

        return existing_name

    index_doc = frappe.get_doc(
        {
            "doctype": "ERP AI Index",
            **values,
        }
    )

    index_doc.insert(ignore_permissions=True)

    return index_doc.name


def build_index():
    """
    Index all supported existing ERPNext records.

    Existing index records are updated.
    Missing index records are created.
    """

    indexed_count = 0

    for doctype in INDEX_DOCTYPES:

        records = frappe.get_list(
            doctype,
            fields=["name"],
            limit_page_length=0,
        )

        for record in records:

            doc = frappe.get_doc(
                doctype,
                record.name,
            )

            if index_document(doc):
                indexed_count += 1

    frappe.db.commit()

    return indexed_count


def search_index(search_text, limit=20):
    """
    Search the persistent ERP AI Index.

    The index is only a search layer.
    It never returns the full searchable_data to the AI.

    Read permission is checked on the original ERPNext document.
    """

    if not search_text:
        return []

    search_text = search_text.lower().strip()

    if limit < 1:
        limit = 1

    if limit > 20:
        limit = 20

    records = frappe.get_list(
        "ERP AI Index",
        fields=[
            "name",
            "source_doctype",
            "document_name",
            "modified",
            "searchable_data",
        ],
        limit_page_length=0,
    )

    results = []

    for record in records:

        source_doctype = record.source_doctype
        document_name = record.document_name

        # -------------------------------------------------
        # SECURITY CHECK
        # Check permission on the actual ERPNext document.
        # -------------------------------------------------

        try:
            if not frappe.has_permission(
                source_doctype,
                "read",
                document_name,
            ):
                continue
        except Exception:
            continue

        searchable_text = (
            str(source_doctype)
            + " "
            + str(document_name)
            + " "
            + str(record.searchable_data)
        ).lower()

        if search_text not in searchable_text:
            continue

        # -------------------------------------------------
        # SAFE RESULT
        # Do NOT return searchable_data.
        # It may contain sensitive ERP information.
        # -------------------------------------------------

        results.append(
            {
                "source_doctype": source_doctype,
                "document_name": document_name,
                "modified": record.modified,
            }
        )

        if len(results) >= limit:
            break

    return results
    
import json
import re

import frappe
import requests


# =========================================================
# CONFIGURATION
# =========================================================

OLLAMA_URL = "http://127.0.0.1:11434/api/generate"
OLLAMA_MODEL = "gemma3"

READ_OPERATIONS = {
    "count",
    "list",
    "sum",
    "average",
    "min",
    "max",
    "ranking",
}

MAX_LIST_LIMIT = 50
MAX_GROUP_LIMIT = 20
MAX_CANDIDATE_DOCTYPES = 25
MAX_FIELDS_FOR_PLANNER = 45

EXCLUDED_DOCTYPES = {
    "DocType",
    "DocField",
    "DocPerm",
    "Module Def",
    "Custom Field",
    "Property Setter",
    "Report",
    "Print Format",
    "Workflow",
    "Workflow State",
    "Workflow Action",
    "Workflow Action Master",
    "Role",
    "Has Role",
    "User",
    "Session Default",
    "DefaultValue",
    "Version",
    "Comment",
    "Communication",
    "Communication Link",
    "File",
    "Error Log",
    "Activity Log",
    "Access Log",
    "Scheduled Job Type",
    "Scheduled Job Log",
    "RQ Job",
    "RQ Worker",
    "Deleted Document",
    "System Settings",
    "Website Settings",
    "Singles",
}

IGNORED_FIELD_TYPES = {
    "Section Break",
    "Column Break",
    "Tab Break",
    "HTML",
    "Heading",
    "Button",
    "Table",
    "Table MultiSelect",
    "Fold",
}

NUMERIC_FIELD_TYPES = {
    "Int",
    "Float",
    "Currency",
    "Percent",
}

# Fields that can exist in ERPNext metadata but should not be exposed
# to the AI query planner/executor because they may be permission-restricted.
QUERY_EXCLUDED_FIELDS = {
    "last_scanned_warehouse",
    "ecommerce_supply_type",
}

# Common ERP language. This is not question-specific routing.
# It only helps rank real DocTypes before Gemma sees them.
TERM_ALIASES = {
    "sales": {"sales", "selling", "sell", "sold"},
    "purchase": {"purchase", "purchasing", "buy", "buying", "bought"},
    "order": {"order", "orders", "po", "so"},
    "invoice": {"invoice", "invoices", "bill", "bills"},
    "payment": {"payment", "payments", "receipt", "receipts", "paid", "received"},
    "customer": {"customer", "customers", "client", "clients", "buyer", "buyers"},
    "supplier": {"supplier", "suppliers", "vendor", "vendors"},
    "item": {"item", "items", "product", "products", "stock"},
    "quotation": {"quotation", "quotations", "quote", "quotes"},
    "delivery": {"delivery", "deliveries", "shipment", "shipments"},
    "request": {"request", "requests"},
    "expense": {"expense", "expenses"},
    "journal": {"journal", "journals", "journalentry", "journalentries"},
    "account": {"account", "accounts", "ledger", "ledgers"},
    "warehouse": {"warehouse", "warehouses", "godown", "godowns"},
    "employee": {"employee", "employees", "staff"},
    "project": {"project", "projects"},
    "asset": {"asset", "assets"},
    "stock": {"stock", "inventory", "inventories"},
}

# =========================================================
# OLLAMA
# =========================================================


def ask_gemma(prompt, timeout=60, json_mode=True):
    payload = {
        "model": OLLAMA_MODEL,
        "prompt": prompt,
        "stream": False,
        "options": {
            "temperature": 0,
            "num_predict": 256,
        },
    }

    if json_mode:
        payload["format"] = "json"

    response = requests.post(
        OLLAMA_URL,
        json=payload,
        timeout=timeout,
    )
    response.raise_for_status()

    data = response.json()
    return data.get("response", "").strip()


# =========================================================
# JSON
# =========================================================


def extract_json(text):
    if not text:
        return None

    text = text.strip()

    try:
        return json.loads(text)
    except Exception:
        pass

    match = re.search(
        r"```(?:json)?\s*(.*?)\s*```",
        text,
        re.DOTALL | re.IGNORECASE,
    )

    if match:
        try:
            return json.loads(match.group(1))
        except Exception:
            pass

    start = text.find("{")
    end = text.rfind("}")

    if start != -1 and end != -1 and end > start:
        try:
            return json.loads(text[start : end + 1])
        except Exception:
            pass

    return None


# =========================================================
# DOCTYPE DISCOVERY
# =========================================================


def get_available_doctypes():
    """Return real, non-single, non-child business DocTypes dynamically."""

    try:
        records = frappe.get_all(
            "DocType",
            filters={
                "istable": 0,
                "issingle": 0,
            },
            fields=["name", "module", "custom"],
            order_by="name asc",
            limit_page_length=0,
        )
    except Exception:
        return []

    result = []

    for record in records:
        name = record.get("name")

        if not name:
            continue

        if name in EXCLUDED_DOCTYPES:
            continue

        if name.startswith("Error") or name.startswith("RQ "):
            continue

        result.append(name)

    return result


def get_doctype_module(doctype):
    try:
        value = frappe.db.get_value("DocType", doctype, "module")
        return value or ""
    except Exception:
        return ""


def get_doctype_fields(doctype):
    """Return actual fields from Frappe metadata."""

    try:
        meta = frappe.get_meta(doctype)
    except Exception:
        return []

    fields = []

    for field in meta.fields:
        if not field.fieldname:
            continue

        if field.fieldtype in IGNORED_FIELD_TYPES:
            continue

        if field.fieldname in QUERY_EXCLUDED_FIELDS:
            continue

        fields.append(
            {
                "fieldname": field.fieldname,
                "label": field.label or field.fieldname,
                "fieldtype": field.fieldtype,
                "options": field.options or "",
            }
        )

    return fields


def get_numeric_fields(doctype):
    try:
        meta = frappe.get_meta(doctype)
    except Exception:
        return set()

    return {
        field.fieldname
        for field in meta.fields
        if (
            field.fieldname
            and field.fieldname not in QUERY_EXCLUDED_FIELDS
            and field.fieldtype in NUMERIC_FIELD_TYPES
        )
    }


def get_valid_fields(doctype):
    """Return explicit and standard Frappe document fields."""

    meta = frappe.get_meta(doctype)

    fields = {
        "name",
        "creation",
        "modified",
        "owner",
        "modified_by",
        "docstatus",
    }

    for field in meta.fields:
        if (
            field.fieldname
            and field.fieldname not in QUERY_EXCLUDED_FIELDS
        ):
            fields.add(field.fieldname)

    return fields


def get_doctype_info(doctype):
    if not doctype:
        return None

    try:
        meta = frappe.get_meta(doctype)
    except Exception:
        return None

    fields = get_doctype_fields(doctype)

    return {
        "doctype": doctype,
        "module": get_doctype_module(doctype),
        "istable": bool(meta.istable),
        "fields": fields,
    }


# =========================================================
# DYNAMIC DOCTYPE ROUTING
# =========================================================


def _tokens(text):
    return set(re.findall(r"[a-z0-9_]+", (text or "").lower()))


def _doctype_tokens(doctype):
    words = re.findall(r"[a-z0-9]+", (doctype or "").lower())
    expanded = set(words)

    for word in words:
        for canonical, aliases in TERM_ALIASES.items():
            if word in aliases:
                expanded.add(canonical)

    return expanded


def _lexical_doctype_candidates(question, doctypes, limit=MAX_CANDIDATE_DOCTYPES):
    """
    Rank real ERPNext DocTypes using names and natural-language aliases.
    Gemma receives only the strongest real candidates.
    """

    q_tokens = _tokens(question)
    q_text = (question or "").lower()

    scored = []

    for doctype in doctypes:
        d_lower = doctype.lower()
        d_tokens = _doctype_tokens(doctype)
        score = 0

        # Exact DocType phrase is a very strong signal.
        if d_lower in q_text:
            score += 100

        # Singular/plural phrase handling.
        singular = d_lower[:-1] if d_lower.endswith("s") else d_lower
        if singular in q_text:
            score += 80

        # Token overlap.
        overlap = q_tokens & d_tokens
        score += len(overlap) * 12

        # Alias-aware overlap.
        for canonical, aliases in TERM_ALIASES.items():
            if q_tokens & aliases and canonical in d_tokens:
                score += 25

        # Business noun combinations.
        if "sales" in q_tokens and "sales" in d_tokens:
            score += 35
        if "purchase" in q_tokens and "purchase" in d_tokens:
            score += 35
        if "invoice" in q_tokens and "invoice" in d_tokens:
            score += 45
        if "order" in q_tokens and "order" in d_tokens:
            score += 45
        if "payment" in q_tokens and "payment" in d_tokens:
            score += 40
        if "customer" in q_tokens and "customer" in d_tokens:
            score += 35
        if "supplier" in q_tokens and "supplier" in d_tokens:
            score += 35
        if "item" in q_tokens and "item" in d_tokens:
            score += 35

        # Prefer shorter exact business names when otherwise tied.
        score -= max(0, len(d_tokens) - 3)

        if score > 0:
            scored.append((score, doctype))

    scored.sort(key=lambda x: (-x[0], x[1].lower()))

    candidates = [doctype for _, doctype in scored[:limit]]

    # Always give Gemma a reasonable fallback set if lexical matching is weak.
    if len(candidates) < min(8, len(doctypes)):
        for doctype in doctypes:
            if doctype not in candidates:
                candidates.append(doctype)
            if len(candidates) >= limit:
                break

    return candidates[:limit]


def _gemma_select_doctype(question, candidates):
    if not candidates:
        return None

    candidate_text = "\n".join(f"- {name}" for name in candidates)

    prompt = f"""
You are an ERPNext DocType selector.

User question:
{question}

Choose exactly ONE DocType from this REAL candidate list.

REAL CANDIDATES:
{candidate_text}

Rules:
- Choose only an exact candidate from the list.
- Understand singular/plural wording.
- "purchase order" means the candidate "Purchase Order" when present.
- "sales order" means the candidate "Sales Order" when present.
- "purchase invoice" means the candidate "Purchase Invoice" when present.
- "sales invoice" means the candidate "Sales Invoice" when present.
- Do not choose a module name.
- Do not invent a DocType.
- Return ONLY JSON.

Return:
{{"doctype":"Exact Candidate Name"}}
"""

    try:
        response = ask_gemma(
            prompt,
            timeout=60,
            json_mode=True,
        )
    except requests.RequestException:
        return None

    result = extract_json(response)

    if not isinstance(result, dict):
        return None

    selected = result.get("doctype")

    if not isinstance(selected, str):
        return None

    selected = selected.strip()

    for candidate in candidates:
        if candidate == selected:
            return candidate

    selected_lower = selected.casefold()

    for candidate in candidates:
        if candidate.casefold() == selected_lower:
            return candidate

    return None

def _is_generic_item_question(question):
    """
    Detect generic item-related questions where the user did not
    explicitly select the Item or Items DocType.

    Examples:
      - Show latest 5 items.
      - How many items are there?
      - List items.
      - Show item records.

    Explicit DocType wording such as:
      - Item records
      - Items records
    is intentionally excluded.
    """
    q = " ".join(
        (question or "").strip().split()
    ).casefold()

    if not q:
        return False

    explicit_item_doc_type = (
        re.search(
            r"\bitem\s+records?\b",
            q,
        )
        or re.search(
            r"\bitems\s+records?\b",
            q,
        )
        or re.search(
            r"\bitem\s+doctype\b",
            q,
        )
        or re.search(
            r"\bitems\s+doctype\b",
            q,
        )
    )

    if explicit_item_doc_type:
        return False

    return bool(
        re.search(
            r"\bitems?\b",
            q,
        )
    )


def choose_doctype(question):
    """
    Select a real DocType directly.

    Important:
    We do NOT ask Gemma to select a module first. That previous
    two-stage design caused questions such as Purchase Order to be
    routed to Accounts. The candidates below are real DocTypes
    discovered from ERPNext itself.
    """

    doctypes = get_available_doctypes()

    if not doctypes:
        return None

    candidates = _lexical_doctype_candidates(
        question,
        doctypes,
    )

    if not candidates:
        return None

    # Deterministic exact phrase handling before AI.
    q = (question or "").casefold()

    exact_phrases = [

        ("purchase order", "Purchase Order"),

        ("sales order", "Sales Order"),

        ("purchase invoice", "Purchase Invoice"),

        ("sales invoice", "Sales Invoice"),

        ("payment entry", "Payment Entry"),

        ("payment entries", "Payment Entry"),

        ("journal entry", "Journal Entry"),

        ("journal entries", "Journal Entry"),

        ("supplier quotation", "Supplier Quotation"),

        ("request for quotation", "Request for Quotation"),

        ("delivery note", "Delivery Note"),

        ("stock entry", "Stock Entry"),

    ]

    for phrase, expected in exact_phrases:
        if phrase in q and expected in doctypes:
            return expected

    selected = _gemma_select_doctype(question, candidates)

    if selected:
        return selected

    # If the top lexical candidate is strongly obvious, use it.
    ranked = _lexical_doctype_candidates(
        question,
        doctypes,
        limit=1,
    )

    return ranked[0] if ranked else None


# Backward-compatible helper. It is no longer used for routing.
def get_doctypes_by_module(module):
    if not module:
        return []

    try:
        rows = frappe.get_all(
            "DocType",
            filters={
                "module": module,
                "istable": 0,
                "issingle": 0,
            },
            fields=["name"],
            order_by="name asc",
            limit_page_length=0,
        )
    except Exception:
        return []

    return [
        row["name"]
        for row in rows
        if row.get("name") and row["name"] not in EXCLUDED_DOCTYPES
    ]


def choose_module(question):
    """
    Compatibility helper only.

    Module is informational now. DocType selection is performed
    directly from all real ERPNext DocTypes.
    """

    if (
        _is_generic_item_question(question)
        and frappe.db.exists("DocType", "Item")
        and frappe.db.exists("DocType", "Items")
    ):
        q = " ".join(
            (question or "").strip().split()
        ).casefold()

        operation = "list"

        if re.search(
            r"\bhow\s+many\b|\bcount\b|\bnumber\s+of\b",
            q,
        ):
            operation = "count"

        limit = 20

        match = re.search(
            r"\b(?:latest|last|top)\s+(\d+)\b",
            q,
        )

        if not match:
            match = re.search(
                r"\b(\d+)\s+(?:items?|item\s+records?)\b",
                q,
            )

        if match:
            try:
                limit = max(
                    1,
                    min(
                        int(match.group(1)),
                        MAX_LIST_LIMIT,
                    ),
                )
            except (TypeError, ValueError):
                limit = 20

        return {
            "doctype": "__combined_item__",
            "operation": operation,
            "filters": {},
            "fields": [
                "name",
                "item_name",
                "item_code",
                "creation",
                "_source_doctype",
            ],
            "limit": limit,
            "order_by": "creation desc",
            "group_by": None,
            "numeric_field": None,
        }

    doctype = choose_doctype(question)

    if not doctype:
        return None

    return get_doctype_module(doctype) or None


# =========================================================
# FIELD / QUERY PLANNING
# =========================================================


def _score_relevant_fields(question, fields):
    q_tokens = _tokens(question)
    q_text = (question or "").lower()

    semantic_groups = {
        "customer": {"customer", "client", "buyer"},
        "supplier": {"supplier", "vendor"},
        "item": {"item", "product"},
        "company": {"company"},
        "date": {"date", "day", "month", "year", "recent", "latest"},
        "amount": {
            "amount",
            "total",
            "value",
            "price",
            "cost",
            "sales",
            "purchase",
            "revenue",
        },
        "status": {"status", "state"},
        "quantity": {"quantity", "qty"},
        "warehouse": {"warehouse", "godown"},
        "project": {"project"},
        "currency": {"currency"},
        "account": {"account", "ledger"},
        "payment": {"payment", "paid", "received"},
    }

    matched_groups = {
        group
        for group, terms in semantic_groups.items()
        if q_tokens & terms
    }

    scored = []

    for field in fields:
        fieldname = str(field.get("fieldname") or "").lower()
        label = str(field.get("label") or "").lower()
        field_tokens = set(re.findall(r"[a-z0-9_]+", fieldname + " " + label))

        score = 0

        if fieldname == "name":
            score += 5

        for word in q_tokens:
            if len(word) < 3:
                continue

            if word == fieldname:
                score += 20
            elif word in fieldname:
                score += 7
            elif word in label:
                score += 5

        if "customer" in matched_groups:
            if "customer" in fieldname or "customer" in label:
                score += 20

        if "supplier" in matched_groups:
            if "supplier" in fieldname or "supplier" in label:
                score += 20

        if "item" in matched_groups:
            if "item" in fieldname or "item" in label:
                score += 15

        if "company" in matched_groups:
            if "company" in fieldname or "company" in label:
                score += 15

        if "date" in matched_groups:
            if "date" in fieldname or "date" in label:
                score += 12

        if "status" in matched_groups:
            if "status" in fieldname or "status" in label:
                score += 15

        if "quantity" in matched_groups:
            if (
                "qty" in fieldname
                or "quantity" in fieldname
                or "qty" in label
                or "quantity" in label
            ):
                score += 15

        if "warehouse" in matched_groups:
            if "warehouse" in fieldname or "warehouse" in label:
                score += 15

        if "project" in matched_groups:
            if "project" in fieldname or "project" in label:
                score += 15

        if "currency" in matched_groups:
            if "currency" in fieldname or "currency" in label:
                score += 15

        if "account" in matched_groups:
            if "account" in fieldname or "account" in label:
                score += 15

        if "payment" in matched_groups:
            if any(
                word in fieldname
                for word in ("payment", "paid", "received")
            ):
                score += 15

        if "amount" in matched_groups:
            if field.get("fieldtype") in NUMERIC_FIELD_TYPES:
                score += 10

            if any(
                word in fieldname
                for word in (
                    "total",
                    "amount",
                    "rate",
                    "price",
                    "cost",
                    "value",
                    "grand",
                )
            ):
                score += 8

        # Useful fields for list answers.
        if fieldname in {
            "customer_name",
            "supplier_name",
            "transaction_date",
            "posting_date",
            "status",
        }:
            score += 3

        scored.append((score, field))

    scored.sort(
        key=lambda x: (-x[0], str(x[1].get("fieldname") or "")),
    )

    return [field for score, field in scored if score > 0]


def _compact_fields_for_prompt(question, fields):
    scored = _score_relevant_fields(question, fields)

    selected = []

    for field in scored:
        if field not in selected:
            selected.append(field)

    # Include key transactional fields when available.
    preferred = [
        "name",
        "customer",
        "customer_name",
        "supplier",
        "supplier_name",
        "company",
        "transaction_date",
        "posting_date",
        "status",
        "grand_total",
        "base_grand_total",
        "total",
        "net_total",
        "amount",
        "paid_amount",
        "received_amount",
        "qty",
        "total_qty",
        "item_code",
        "item_name",
    ]

    by_name = {
        str(field.get("fieldname")): field
        for field in fields
    }

    for fieldname in preferred:
        field = by_name.get(fieldname)
        if field and field not in selected:
            selected.append(field)

    return selected[:MAX_FIELDS_FOR_PLANNER]


def _build_filter_value_examples(fields):
    links = [
        field
        for field in fields
        if field.get("fieldtype") == "Link"
        and field.get("options")
    ]

    data_fields = [
        field
        for field in fields
        if field.get("fieldtype") == "Data"
        and field.get("fieldname")
        and field.get("fieldname") not in {
            "scan_barcode",
            "last_scanned_warehouse",
            "in_words",
            "base_in_words",
            "utm_content",
        }
    ]

    lines = []

    for field in links[:20]:
        lines.append(
            f"- {field.get('fieldname')} -> "
            f"{field.get('options')} [Link]"
        )

    for field in data_fields[:15]:
        lines.append(
            f"- {field.get('fieldname')} -> "
            f"{field.get('label')} [Data]"
        )

    return "\n".join(lines)


def _infer_operation(question, current=None):
    """Infer a read-only operation from generic natural-language wording."""
    q = (question or "").casefold()
    current = current if current in READ_OPERATIONS else None

    if re.search(r"\b(how many|count|number of)\b", q):
        return "count"
    if re.search(r"\b(average|avg|mean)\b", q):
        return "average"
    if re.search(r"\b(highest|maximum|max)\b", q):
        return "max"
    if re.search(r"\b(lowest|minimum|min)\b", q):
        return "min"
    if re.search(r"\b(total|sum|sum of)\b", q):
        return "sum"
    if re.search(r"\b(top|biggest|largest|ranking|ranked)\b", q):
        return "ranking"
    if re.search(r"\b(list|show|give me|display|which|what are|all)\b", q):
        return "list"

    return current or "list"


def _choose_numeric_field(question, fields):
    """Choose a real numeric field using generic wording and metadata."""
    numeric = [
        field for field in fields
        if field.get("fieldtype") in NUMERIC_FIELD_TYPES
        and field.get("fieldname")
    ]

    if not numeric:
        return None

    q = (question or "").casefold()

    scored = []
    for field in numeric:
        name = str(field.get("fieldname") or "").casefold()
        label = str(field.get("label") or "").casefold()
        score = 0

        if "grand_total" in name:
            score += 30
        if "base_grand_total" in name:
            score += 25
        if "total" in name:
            score += 12
        if "amount" in name:
            score += 10
        if "rate" in name:
            score += 6
        if "qty" in name or "quantity" in name:
            score += 6

        for token in _tokens(q):
            if token in name:
                score += 8
            elif token in label:
                score += 4

        if "quantity" in q or "qty" in q:
            if "qty" in name or "quantity" in name:
                score += 20

        if any(word in q for word in ("amount", "value", "sales", "purchase", "revenue", "total")):
            if any(word in name for word in ("total", "amount", "value")):
                score += 15

        scored.append((score, name, field.get("fieldname")))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored[0][2]


def _choose_date_field(question, fields):
    """Choose the most relevant real Date/Datetime field."""
    date_fields = [
        field for field in fields
        if field.get("fieldtype") in {"Date", "Datetime"}
        and field.get("fieldname")
    ]

    if not date_fields:
        return None

    q = (question or "").casefold()
    scored = []

    for field in date_fields:
        name = str(field.get("fieldname") or "").casefold()
        label = str(field.get("label") or "").casefold()
        score = 0

        if name == "transaction_date":
            score += 35
        elif name == "posting_date":
            score += 32
        elif name == "date":
            score += 25
        elif "date" in name:
            score += 8

        if "posting" in q and "posting" in name:
            score += 25
        if "transaction" in q and "transaction" in name:
            score += 25
        if "due" in q and "due" in name:
            score += 25
        if "schedule" in q and "schedule" in name:
            score += 20

        for token in _tokens(q):
            if token in name:
                score += 6
            elif token in label.casefold():
                score += 3

        scored.append((score, name, field.get("fieldname")))

    scored.sort(key=lambda item: (-item[0], item[1]))
    return scored[0][2]


def _month_range(year, month):
    from datetime import date
    import calendar

    start = date(year, month, 1)
    end = date(year, month, calendar.monthrange(year, month)[1])
    return start.isoformat(), end.isoformat()


def _extract_date_range(question, today):
    """
    Return (start, end) for common natural-language date ranges.
    No DocType-specific rules are used.
    """
    from datetime import date, timedelta

    q = (question or "").casefold()
    today_date = date.fromisoformat(str(today))

    month_names = {
        "january": 1, "jan": 1,
        "february": 2, "feb": 2,
        "march": 3, "mar": 3,
        "april": 4, "apr": 4,
        "may": 5,
        "june": 6, "jun": 6,
        "july": 7, "jul": 7,
        "august": 8, "aug": 8,
        "september": 9, "sep": 9, "sept": 9,
        "october": 10, "oct": 10,
        "november": 11, "nov": 11,
        "december": 12, "dec": 12,
    }

    month_pattern = (
        r"\b("
        + "|".join(sorted(month_names, key=len, reverse=True))
        + r")\s+(20\d{2})\b"
    )

    match = re.search(month_pattern, q)
    if match:
        month = month_names[match.group(1)]
        year = int(match.group(2))
        return _month_range(year, month)

    if re.search(r"\btoday\b", q):
        value = today_date.isoformat()
        return value, value

    if re.search(r"\byesterday\b", q):
        value = (today_date - timedelta(days=1)).isoformat()
        return value, value

    if re.search(r"\btomorrow\b", q):
        value = (today_date + timedelta(days=1)).isoformat()
        return value, value

    if re.search(r"\bthis month\b", q):
        return _month_range(today_date.year, today_date.month)

    if re.search(r"\blast month\b", q):
        first = today_date.replace(day=1)
        last_day_previous = first - timedelta(days=1)
        return _month_range(last_day_previous.year, last_day_previous.month)

    if re.search(r"\bthis year\b", q):
        return (
            date(today_date.year, 1, 1).isoformat(),
            date(today_date.year, 12, 31).isoformat(),
        )

    if re.search(r"\blast year\b", q):
        year = today_date.year - 1
        return (
            date(year, 1, 1).isoformat(),
            date(year, 12, 31).isoformat(),
        )

    # Explicit ISO date.
    match = re.search(r"\b(20\d{2}-\d{2}-\d{2})\b", q)
    if match:
        value = match.group(1)
        return value, value

    return None


def _normalize_filter_operator(operator):
    if not isinstance(operator, str):
        return None

    aliases = {
        "=": "=",
        "==": "=",
        "equals": "=",
        "equal": "=",
        "is": "=",
        "!=": "!=",
        "<>": "!=",
        "not equals": "!=",
        "not_equal": "!=",
        "not_equals": "!=",
        "contains": "like",
        "like": "like",
        "not contains": "not like",
        "not_contains": "not like",
        "not like": "not like",
        "after": ">",
        "greater than": ">",
        "gt": ">",
        ">": ">",
        "before": "<",
        "less than": "<",
        "lt": "<",
        "<": "<",
        "on or after": ">=",
        "on_or_after": ">=",
        "gte": ">=",
        ">=": ">=",
        "on or before": "<=",
        "on_or_before": "<=",
        "lte": "<=",
        "<=": "<=",
        "in": "in",
        "not in": "not in",
        "between": "between",
    }

    return aliases.get(operator.strip().casefold())


def _canonicalize_gemma_filters(raw_filters, valid_fields=None):
    """
    Convert common LLM filter shapes into one safe Frappe filter dict.

    Accepted examples:
      {"customer": "ABC"}
      [{"field": "customer", "operator": "equals", "value": "ABC"}]
      {"transaction_date": {"operator": "between", "value": ["2026-08-01", "2026-08-31"]}}
    """
    valid_fields = valid_fields or set()
    output = {}

    if isinstance(raw_filters, dict):
        items = list(raw_filters.items())
    elif isinstance(raw_filters, list):
        items = []

        for item in raw_filters:
            if not isinstance(item, dict):
                continue

            field = item.get("field") or item.get("fieldname")
            operator = item.get("operator")
            value = item.get("value")

            if not isinstance(field, str):
                continue

            canonical_operator = _normalize_filter_operator(operator)

            if canonical_operator is None:
                # A plain field/value object can still be accepted.
                if operator in (None, ""):
                    items.append((field, value))
                continue

            if (
                canonical_operator == "="
                and isinstance(value, str)
                and "/" in value
            ):
                parts = [part.strip() for part in value.split("/", 1)]
                if (
                    len(parts) == 2
                    and re.fullmatch(r"\d{4}-\d{2}-\d{2}", parts[0])
                    and re.fullmatch(r"\d{4}-\d{2}-\d{2}", parts[1])
                ):
                    canonical_operator = "between"
                    value = parts

            items.append(
                (
                    field,
                    {
                        "operator": canonical_operator,
                        "value": value,
                    },
                )
            )
    else:
        return {}

    for field, value in items:
        if not isinstance(field, str):
            continue

        field = field.strip()

        if not field or (valid_fields and field not in valid_fields):
            continue

        if isinstance(value, dict):
            operator = _normalize_filter_operator(
                value.get("operator")
            )
            operand = value.get("value")

            if operator is None:
                continue

            if (
                operator == "="
                and isinstance(operand, str)
                and "/" in operand
            ):
                parts = [part.strip() for part in operand.split("/", 1)]
                if (
                    len(parts) == 2
                    and all(
                        re.fullmatch(r"\d{4}-\d{2}-\d{2}", part)
                        for part in parts
                    )
                ):
                    operator = "between"
                    operand = parts

            output[field] = [operator, operand]
            continue

        output[field] = value

    return output


def _extract_entity_filter(question, doctype, fields):
    """
    Extract customer/supplier/company/item filters from natural language.

    Supports:
      - customer West View Software Ltd.
      - supplier MA Inc.
      - company ABC Parent Pvt Ltd.
      - item SKU010
      - for West View Software Ltd.
      - combined with date phrases such as:
        "for West View Software Ltd. in September 2026"

    Date-only phrases and generic record-count phrases such as:
      "How many Item records are there?"
    are not treated as entity filters.
    """
    q = " ".join((question or "").strip().split())

    if not q:
        return None

    keyword_patterns = [
        (
            "customer",
            r"\bcustomer\s+(?:is\s+)?(.+?)(?=\s+(?:in|from|on|for|with|where|having|and)\b|[?.!,;]|$)",
        ),
        (
            "supplier",
            r"\bsupplier\s+(?:is\s+)?(.+?)(?=\s+(?:in|from|on|for|with|where|having|and)\b|[?.!,;]|$)",
        ),
        (
            "company",
            r"\bcompany\s+(?:is\s+)?(.+?)(?=\s+(?:in|from|on|for|with|where|having|and)\b|[?.!,;]|$)",
        ),
        (
            "item",
            r"\bitem\s+(?:is\s+)?(.+?)(?=\s+(?:in|from|on|for|with|where|having|and)\b|[?.!,;]|$)",
        ),
        (
            "vendor",
            r"\bvendor\s+(?:is\s+)?(.+?)(?=\s+(?:in|from|on|for|with|where|having|and)\b|[?.!,;]|$)",
        ),
        (
            "client",
            r"\bclient\s+(?:is\s+)?(.+?)(?=\s+(?:in|from|on|for|with|where|having|and)\b|[?.!,;]|$)",
        ),
    ]

    extracted = []

    # ---------------------------------------------------------
    # 1. Explicit entity keywords
    # ---------------------------------------------------------
    for entity_type, pattern in keyword_patterns:
        match = re.search(
            pattern,
            q,
            re.IGNORECASE,
        )

        if match:
            extracted.append(
                (
                    entity_type,
                    match.group(1).strip(),
                )
            )

    # ---------------------------------------------------------
    # 2. Date detection
    # ---------------------------------------------------------
    date_range = _extract_date_range(
        q,
        frappe.utils.nowdate(),
    )

    # ---------------------------------------------------------
    # 3. Generic "for X" entity extraction
    # ---------------------------------------------------------
    if not extracted:
        match = re.search(
            r"\bfor\s+(.+?)(?=\s+(?:in|from|on|with|where|having|and)\b|[?.!,;]|$)",
            q,
            re.IGNORECASE,
        )

        if match:
            value = match.group(1).strip()

            if value:
                value_date_range = _extract_date_range(
                    value,
                    frappe.utils.nowdate(),
                )

                if not value_date_range:
                    extracted.append(
                        (
                            "generic",
                            value,
                        )
                    )

    # Nothing to extract.
    if not extracted:
        return None

    entity_type, value = extracted[0]

    # ---------------------------------------------------------
    # 4. Ignore phrases that are not actual entity values.
    # ---------------------------------------------------------
    normalized_value = " ".join(
        str(value or "").strip().split()
    ).casefold()

    non_entity_values = {
        "customer",
        "supplier",
        "company",
        "item",
        "vendor",
        "client",
        "the customer",
        "the supplier",
        "the company",
        "the item",
        "the vendor",
        "the client",
        "records",
        "record",
        "records are there",
        "record is there",
        "records are available",
        "records available",
        "record is available",
        "record available",
        "records in erpnext",
        "record in erpnext",
    }

    if normalized_value in non_entity_values:
        return None

    # Generic "record(s) are there/available" wording should never
    # become an entity filter.
    if re.fullmatch(
        r"(?:the\s+)?(?:records?|entries?)"
        r"(?:\s+(?:are|is))?"
        r"(?:\s+(?:there|available))?",
        normalized_value,
        re.IGNORECASE,
    ):
        return None

    # Explicit entity keywords without an actual value.
    if normalized_value in {
        "customer",
        "supplier",
        "company",
        "item",
        "vendor",
        "client",
    }:
        return None

    # ---------------------------------------------------------
    # 5. Find suitable entity fields
    # ---------------------------------------------------------
    candidates = []

    for field in fields:
        fieldname = str(
            field.get("fieldname") or ""
        )

        label = str(
            field.get("label") or ""
        )

        fieldtype = field.get("fieldtype")

        if fieldtype not in {
            "Link",
            "Data",
        }:
            continue

        text = f"{fieldname} {label}".casefold()

        score = 0

        if entity_type in {
            "customer",
            "client",
        }:
            if (
                "customer" in text
                or "client" in text
            ):
                score += 50

        elif entity_type in {
            "supplier",
            "vendor",
        }:
            if (
                "supplier" in text
                or "vendor" in text
            ):
                score += 50

        elif entity_type == "company":
            if "company" in text:
                score += 50

        elif entity_type == "item":
            if (
                "item" in text
                or "product" in text
            ):
                score += 50

        else:
            if any(
                word in text
                for word in (
                    "customer",
                    "supplier",
                    "company",
                    "item",
                    "vendor",
                    "client",
                )
            ):
                score += 30

        if fieldtype == "Link":
            score += 8

        if fieldname.endswith("_name"):
            score += 4

        if score > 0:
            candidates.append(
                (
                    score,
                    field,
                )
            )

    candidates.sort(
        key=lambda item: (
            -item[0],
            str(
                item[1].get("fieldname") or ""
            ),
        )
    )

    # ---------------------------------------------------------
    # 6. Preferred business fields for generic "for X"
    # ---------------------------------------------------------
    if entity_type == "generic":
        preferred_fields = {
            "Sales Invoice": [
                "customer",
                "customer_name",
            ],
            "Sales Order": [
                "customer",
                "customer_name",
            ],
            "Delivery Note": [
                "customer",
                "customer_name",
            ],
            "Purchase Invoice": [
                "supplier",
                "supplier_name",
            ],
            "Purchase Order": [
                "supplier",
                "supplier_name",
            ],
            "Purchase Receipt": [
                "supplier",
                "supplier_name",
            ],
            "Payment Entry": [
                "company",
                "party_name",
                "party",
            ],
            "Stock Entry": [
                "company",
            ],
        }

        preferred = preferred_fields.get(
            doctype,
            [],
        )

        if preferred:
            candidates.sort(
                key=lambda item: (
                    preferred.index(
                        item[1].get("fieldname")
                    )
                    if item[1].get("fieldname")
                    in preferred
                    else len(preferred),
                    -item[0],
                    str(
                        item[1].get("fieldname") or ""
                    ),
                )
            )

    # ---------------------------------------------------------
    # 7. Resolve actual ERPNext entity value
    # ---------------------------------------------------------
    for _, field in candidates:
        fieldname = field.get("fieldname")
        fieldtype = field.get("fieldtype")
        options = field.get("options")

        if not fieldname:
            continue

        # Link field
        if (
            fieldtype == "Link"
            and options
        ):
            actual = resolve_exact_name(
                options,
                value,
            )

            if actual != value:
                return {
                    fieldname: actual
                }

            try:
                rows = frappe.get_list(
                    options,
                    filters={
                        "name": [
                            "like",
                            f"%{value}%",
                        ]
                    },
                    fields=["name"],
                    limit_page_length=10,
                )
            except Exception:
                rows = []

            if (
                len(rows) == 1
                and rows[0].get("name")
            ):
                return {
                    fieldname: rows[0]["name"]
                }

            return {
                fieldname: value
            }

        # Data field
        elif fieldtype == "Data":
            try:
                rows = frappe.get_list(
                    doctype,
                    fields=[fieldname],
                    filters={
                        fieldname: [
                            "like",
                            f"%{value}%",
                        ]
                    },
                    limit_page_length=50,
                )
            except Exception:
                rows = []

            target = " ".join(
                value.strip().split()
            ).casefold()

            target = (
                target
                .replace(".", "")
                .replace(",", "")
                .replace("-", " ")
            )

            target = " ".join(
                target.split()
            )

            exact_matches = []

            for row in rows:
                actual = row.get(
                    fieldname
                )

                if not isinstance(
                    actual,
                    str,
                ):
                    continue

                normalized = " ".join(
                    actual.strip().split()
                ).casefold()

                normalized = (
                    normalized
                    .replace(".", "")
                    .replace(",", "")
                    .replace("-", " ")
                )

                normalized = " ".join(
                    normalized.split()
                )

                if normalized == target:
                    if (
                        actual
                        not in exact_matches
                    ):
                        exact_matches.append(
                            actual
                        )

            if len(exact_matches) == 1:
                return {
                    fieldname: exact_matches[0]
                }

            if len(rows) == 1:
                actual = rows[0].get(
                    fieldname
                )

                if (
                    isinstance(
                        actual,
                        str,
                    )
                    and actual.strip()
                ):
                    return {
                        fieldname: actual
                    }

            return {
                fieldname: value
            }

    return None

def _detect_grouping_field(question, fields):
    """
    Detect explicit group-wise wording such as:
    - for each customer
    - by customer
    - per customer
    - customer-wise
    - top customers
    """

    q_lower = (question or "").casefold()

    valid_fields = {
        str(field.get("fieldname"))
        for field in fields
        if field.get("fieldname")
    }

    grouping_requested = bool(
        re.search(r"\bfor\s+each\b", q_lower)
        or re.search(r"\bper\b", q_lower)
        or re.search(
            r"\bby\s+(customers?|suppliers?|compan(?:y|ies)|items?|"
            r"products?|warehouses?|projects?)\b",
            q_lower,
        )
        or re.search(
            r"\b(customer|supplier|compan(?:y|ies)|item|product|warehouse|project)"
            r"[-\s]?wise\b",
            q_lower,
        )
        or re.search(
            r"\b(each|every)\s+(customer|supplier|compan(?:y|ies)|item|"
            r"product|warehouse|project)s?\b",
            q_lower,
        )
    )

    if not grouping_requested:
        ranking_requested = bool(
            re.search(
                r"\b(highest|maximum|max|lowest|minimum|min|top|"
                r"biggest|largest|ranking|ranked)\b",
                q_lower,
            )
        )

        grouping_requested = ranking_requested and bool(
            re.search(
                r"\b(customers?|suppliers?|compan(?:y|ies)|items?|products?|"
                r"warehouses?|projects?)\b",
                q_lower,
            )
        )

    if not grouping_requested:
        return None

    patterns = [
        (r"\bcustomers?\b", ("customer_name", "customer")),
        (r"\bclients?\b", ("customer_name", "customer")),
        (r"\bsuppliers?\b", ("supplier_name", "supplier")),
        (r"\bvendors?\b", ("supplier_name", "supplier")),
        (r"\bcompan(?:y|ies)\b", ("company",)),
        (r"\bitems?\b", ("item_name", "item_code", "item")),
        (r"\bproducts?\b", ("item_name", "item_code", "item")),
        (r"\bwarehouses?\b", ("warehouse",)),
        (r"\bgodowns?\b", ("warehouse",)),
        (r"\bprojects?\b", ("project",)),
    ]

    for pattern, candidates in patterns:
        if not re.search(pattern, q_lower):
            continue

        for candidate in candidates:
            if candidate in valid_fields:
                return candidate

    return None

def understand_question(question):
    """
    Convert natural language into a safe structured read-only plan.

    The AI is used to interpret the request, but deterministic
    normalization fills common gaps so simple questions do not depend
    on one exact Gemma output format.
    """

    q = " ".join(
        (question or "").strip().split()
    ).casefold()

    # -----------------------------------------------------
    # TOP ITEM / TOP SELLING ITEM QUERY
    # -----------------------------------------------------

    is_top_item_query = bool(
        re.search(
            r"\b(?:top|best[- ]selling|highest[- ]selling|"
            r"most[- ]sold|best|highest|largest|biggest)\b",
            q,
        )
        and re.search(
            r"\bitems?\b|\bproducts?\b",
            q,
        )
    )

    is_quantity_ranking = bool(
        re.search(
            r"\b(?:by|based\s+on|according\s+to)\s+"
            r"(?:quantity|qty|units?|number\s+sold)\b",
            q,
        )
        or re.search(
            r"\b(?:most|highest|largest)\s+"
            r"(?:quantity|qty|units?)\b",
            q,
        )
        or re.search(
            r"\b(?:most|highest)\s+"
            r"(?:sold|selling)\b",
            q,
        )
    )

    if (
        is_top_item_query
        and frappe.db.exists(
            "DocType",
            "Sales Invoice Item",
        )
        and frappe.db.exists(
            "DocType",
            "Sales Invoice",
        )
    ):
        limit = 1

        match = re.search(
            r"\b(?:top|best|highest|largest|biggest)"
            r"\s+(\d+)\s+"
            r"(?:items?|products?)\b",
            q,
        )

        if match:
            try:
                limit = max(
                    1,
                    min(
                        int(match.group(1)),
                        MAX_GROUP_LIMIT,
                    ),
                )
            except (TypeError, ValueError):
                limit = 1

        if is_quantity_ranking:
            return {
                "doctype": "__item_sales_ranking__",
                "operation": "ranking",
                "filters": {},
                "fields": [
                    "item_code",
                    "item_name",
                    "qty",
                    "amount",
                ],
                "limit": limit,
                "order_by": "total_qty desc",
                "group_by": "item_code",
                "numeric_field": "qty",
                "ranking_metric": "quantity",
            }

        return {
            "doctype": "__item_sales_ranking__",
            "operation": "ranking",
            "filters": {},
            "fields": [
                "item_code",
                "item_name",
                "qty",
                "amount",
            ],
            "limit": limit,
            "order_by": "total_sales desc",
            "group_by": "item_code",
            "numeric_field": "amount",
            "ranking_metric": "sales",
        }

    # -----------------------------------------------------
    # GENERIC ITEM / ITEMS QUERY
    # -----------------------------------------------------

    if (
        _is_generic_item_question(question)
        and frappe.db.exists("DocType", "Item")
        and frappe.db.exists("DocType", "Items")
    ):
        operation = "list"

        if re.search(
            r"\bhow\s+many\b|\bcount\b|\bnumber\s+of\b",
            q,
        ):
            operation = "count"

        limit = 20

        match = re.search(
            r"\b(?:latest|last|top)\s+(\d+)\b",
            q,
        )

        if not match:
            match = re.search(
                r"\b(\d+)\s+(?:items?|item\s+records?)\b",
                q,
            )

        if match:
            try:
                limit = max(
                    1,
                    min(
                        int(match.group(1)),
                        MAX_LIST_LIMIT,
                    ),
                )
            except (TypeError, ValueError):
                limit = 20

        # -----------------------------------------------------
        # GENERIC ITEM NAME FILTER
        # -----------------------------------------------------

        item_name_filter = None

        # -----------------------------------------------------
        # ITEM RATE QUERY
        # -----------------------------------------------------

        item_rate_match = re.search(
            r"\b(?:rate|price)\s+"
            r"(?:of|for)\s+"
            r"(?:item|items)\s+"
            r"['\"]?([a-z0-9][a-z0-9 ._-]*)['\"]?"
            r"\s*[\?\.]?$",
            q,
            re.IGNORECASE,
        )

        if not item_rate_match:
            item_rate_match = re.search(
                r"\b(?:item|items)\s+"
                r"(?:rate|price)\s+"
                r"(?:for|of)\s+"
                r"['\"]?([a-z0-9][a-z0-9 ._-]*)['\"]?"
                r"\s*[\?\.]?$",
                q,
                re.IGNORECASE,
            )

        if item_rate_match:
            item_name_filter = (
                item_rate_match.group(1)
                .strip()
                .rstrip("?.!,")
            )

            name_match = None
            item_code_match = None

        else:
            # -------------------------------------------------
            # ITEM CODE QUERY
            # -------------------------------------------------

            item_code_match = re.search(
                r"\b(?:item|items)\s+"
                r"(?:code|codes)\s+"
                r"(?:for|of)\s+"
                r"['\"]?([a-z0-9][a-z0-9 ._-]*)['\"]?"
                r"\s*[\?\.]?$",
                q,
                re.IGNORECASE,
            )

            if item_code_match:
                item_name_filter = (
                    item_code_match.group(1)
                    .strip()
                    .rstrip("?.!,")
                )

                name_match = None

            else:
                if operation == "count":
                    name_match = re.search(
                        r"\b(?:item|items)\s+"
                        r"(?:named|called|with\s+name)\s+"
                        r"['\"]?([a-z0-9][a-z0-9 ._-]*)['\"]?"
                        r"(?:\s+(?:are|is|were|was)\b.*)?$",
                        q,
                        re.IGNORECASE,
                    )
                else:
                    output_name_phrase = re.search(
                        r"\bwith\s+(?:their\s+)?item\s+names?\b",
                        q,
                        re.IGNORECASE,
                    )

                    if output_name_phrase:
                        name_match = None
                    else:
                        name_match = re.search(
                            r"\b(?:item|items)\s+"
                            r"(?:named|called|with\s+name)?\s*"
                            r"['\"]?([a-z0-9][a-z0-9 ._-]*)['\"]?"
                            r"\s*[\?\.]?$",
                            q,
                            re.IGNORECASE,
                        )

        if name_match:
            candidate = (
                name_match.group(1)
                .strip()
                .rstrip("?.!,")
            )

            ignored_values = {
                "records",
                "record",
                "items",
                "item",
                "latest",
                "last",
                "top",
                "are",
                "there",
                "is",
                "was",
                "were",
                "how",
                "many",
                "count",
                "number",
                "of",
            }

            if candidate.casefold() not in ignored_values:
                item_name_filter = candidate

        filters = {}

        if item_name_filter:
            filters["item_name"] = item_name_filter

        rate_query = bool(
            re.search(
                r"\b(?:rate|price)\b",
                q,
                re.IGNORECASE,
            )
        )

        if rate_query:
            requested_fields = [
                "name",
                "item_name",
                "item_code",
                "creation",
                "standard_rate",
                "standard_selling_rate",
                "_source_doctype",
            ]
        else:
            requested_fields = [
                "name",
                "item_name",
                "item_code",
                "creation",
                "_source_doctype",
            ]

        return {
            "doctype": "__combined_item__",
            "operation": operation,
            "filters": filters,
            "fields": requested_fields,
            "limit": limit,
            "order_by": "creation desc",
            "group_by": None,
            "numeric_field": None,
        }

    doctype = choose_doctype(question)

    if not doctype:
        return None

    info = get_doctype_info(doctype)

    if not info:
        return None

    fields = info.get("fields", [])
    valid_fields = get_valid_fields(doctype)

    selected_fields = _compact_fields_for_prompt(
        question,
        fields,
    )

    fields_text = "\n".join(
        (
            f"- {field.get('fieldname')} | "
            f"{field.get('label')} | "
            f"{field.get('fieldtype')} | "
            f"{field.get('options')}"
        )
        for field in selected_fields
    )

    filter_examples = _build_filter_value_examples(fields)
    today = frappe.utils.nowdate()

    prompt = f"""
You are a strict ERPNext READ-ONLY query planner.

User question:
{question}

Selected REAL ERPNext DocType:
{doctype}

Today:
{today}

REAL FIELDS:
{fields_text}

REAL FILTERABLE LINK/DATA FIELDS:
{filter_examples}

Return ONLY JSON in exactly this shape:
{{
  "doctype": "{doctype}",
  "operation": "list",
  "filters": {{}},
  "fields": ["name"],
  "limit": 20,
  "order_by": "creation desc",
  "group_by": null,
  "numeric_field": null
}}

Allowed operations:
count, list, sum, average, min, max, ranking

FILTER FORMAT:
"filters" must normally be a JSON object:
{{"fieldname": "value"}}

For an operator use:
{{"fieldname": {{"operator": "=", "value": "value"}}}}

For a date range use:
{{"date_field": {{"operator": "between", "value": ["YYYY-MM-DD", "YYYY-MM-DD"]}}}}

Important:
- Use ONLY the selected DocType.
- Use ONLY real fields shown above.
- Never invent field names.
- Never generate SQL or Python.
- Never modify ERPNext.
- This is READ-ONLY.
- Preserve explicit user values exactly when possible.
- If the user asks for a specific customer, supplier, company, item, vendor, or client, put the corresponding REAL field in filters.
- If the user asks for a month/year, put the appropriate REAL Date field in filters.
- "how many" means count.
- "list/show/give me/display/which" means list.
- "total/sum" means sum.
- "average/avg" means average.
- "highest/max" means max.
- "lowest/min" means min.
- "top/biggest/largest/ranking" means ranking.
- Maximum limit is 50.
- For list, always include "name" in fields.
- For ranking, group_by and numeric_field must be real fields.
"""

    try:
        response = ask_gemma(
            prompt,
            timeout=60,
            json_mode=True,
        )
    except requests.RequestException:
        response = ""

    plan = extract_json(response)

    if not isinstance(plan, dict):
        plan = {}

    plan["doctype"] = doctype

    plan["filters"] = _canonicalize_gemma_filters(
        plan.get("filters", {}),
        valid_fields,
    )

    plan["operation"] = _infer_operation(
        question,
        plan.get("operation"),
    )

    date_range = _extract_date_range(
        question,
        today,
    )

    if date_range:
        date_field = _choose_date_field(
            question,
            fields,
        )

        if date_field:
            start_date, end_date = date_range

            if start_date == end_date:
                plan["filters"].setdefault(
                    date_field,
                    start_date,
                )
            else:
                plan["filters"].setdefault(
                    date_field,
                    ["between", [start_date, end_date]],
                )

    entity_filter = _extract_entity_filter(
        question,
        doctype,
        fields,
    )

    if entity_filter:
        for field, value in entity_filter.items():
            plan["filters"][field] = value

        if (
            doctype == "Payment Entry"
            and "company" in entity_filter
        ):
            plan["filters"].pop(
                "party_name",
                None,
            )
            plan["filters"].pop(
                "party",
                None,
            )

        if (
            doctype == "Stock Entry"
            and "company" in entity_filter
        ):
            plan["filters"].pop(
                "supplier_name",
                None,
            )
            plan["filters"].pop(
                "supplier",
                None,
            )
            plan["filters"].pop(
                "customer",
                None,
            )
            plan["filters"].pop(
                "customer_name",
                None,
            )

    if not plan.get("fields"):
        plan["fields"] = ["name"]

    if not isinstance(plan.get("fields"), list):
        plan["fields"] = ["name"]

    if plan["operation"] == "list":
        for field in list(plan["filters"].keys()):
            if field in valid_fields and field not in plan["fields"]:
                plan["fields"].append(field)

    numeric_field = plan.get("numeric_field")

    if isinstance(numeric_field, list):
        numeric_field = (
            numeric_field[0]
            if numeric_field
            else None
        )

    if (
        plan["operation"] in {
            "sum",
            "average",
            "min",
            "max",
            "ranking",
        }
        and (
            not isinstance(numeric_field, str)
            or numeric_field not in get_numeric_fields(doctype)
        )
    ):
        numeric_field = _choose_numeric_field(
            question,
            fields,
        )

    plan["numeric_field"] = numeric_field

    if plan["operation"] in {
        "sum",
        "average",
        "min",
        "max",
        "ranking",
    }:
        group_by = plan.get("group_by")

        if isinstance(group_by, list):
            group_by = group_by[0] if group_by else None

        if not isinstance(group_by, str) or group_by not in valid_fields:
            group_by = _detect_grouping_field(
                question,
                fields,
            )

        if not isinstance(group_by, str) or group_by not in valid_fields:
            if plan["operation"] == "ranking":
                scored = _score_relevant_fields(
                    question,
                    fields,
                )

                group_candidates = [
                    field.get("fieldname")
                    for field in scored
                    if field.get("fieldname") in valid_fields
                    and field.get("fieldname") != numeric_field
                ]

                group_by = (
                    group_candidates[0]
                    if group_candidates
                    else None
                )

        plan["group_by"] = group_by

    if not plan.get("limit"):
        plan["limit"] = 20

    if not plan.get("order_by"):
        plan["order_by"] = "creation desc"

    return plan


# =========================================================
# SAFE NAME / FILTER HANDLING
# =========================================================


def resolve_exact_name(doctype, value):
    if not isinstance(value, str):
        return value

    value = value.strip()

    if not value:
        return value

    def normalize_name(text):
        if not isinstance(text, str):
            return ""

        text = " ".join(text.strip().split())
        text = text.casefold()

        # Ignore common punctuation differences.
        text = text.replace(".", "")
        text = text.replace(",", "")
        text = text.replace("-", " ")
        text = " ".join(text.split())

        return text

    # 1. Exact ERPNext name
    try:
        if frappe.db.exists(doctype, value):
            return value
    except Exception:
        pass

    # 2. Case-insensitive / punctuation-insensitive match
    try:
        rows = frappe.get_list(
            doctype,
            fields=["name"],
            filters={"name": ["like", f"%{value}%"]},
            limit_page_length=50,
        )
    except Exception:
        return value

    target = normalize_name(value)

    matches = []

    for row in rows:
        name = row.get("name")

        if not isinstance(name, str):
            continue

        if normalize_name(name) == target:
            matches.append(name)

    return matches[0] if len(matches) == 1 else value


def normalize_filters(doctype, filters):
    """
    Normalize filters from either the canonical dict form or common
    LLM list/operator forms, then resolve actual ERPNext values.
    """
    valid_fields = get_valid_fields(doctype)

    filters = _canonicalize_gemma_filters(
        filters,
        valid_fields,
    )

    if not isinstance(filters, dict):
        return {}

    normalized = {}

    placeholder_values = {
        "customer name",
        "supplier name",
        "company name",
        "item name",
        "customer",
        "supplier",
        "company",
        "item",
        "name",
        "the customer",
        "the supplier",
        "the company",
        "the item",
    }

    try:
        meta = frappe.get_meta(doctype)
    except Exception:
        meta = None

    def normalize_text(text):
        if not isinstance(text, str):
            return ""

        text = " ".join(text.strip().split()).casefold()
        text = text.replace(".", "")
        text = text.replace(",", "")
        text = text.replace("-", " ")
        text = " ".join(text.split())

        return text

    for field, value in filters.items():
        if field not in valid_fields:
            continue

        # Operator form: [operator, operand]
        operator = None
        operand = None

        if (
            isinstance(value, list)
            and len(value) == 2
            and isinstance(value[0], str)
            and value[0] in {
                "=",
                "!=",
                ">",
                "<",
                ">=",
                "<=",
                "like",
                "not like",
                "in",
                "not in",
                "between",
                "is",
            }
        ):
            operator = value[0]
            operand = value[1]

        if operator == "between":
            if isinstance(operand, list):
                normalized[field] = [
                    "between",
                    operand,
                ]
            continue

        if operator in {
            "in",
            "not in",
        }:
            if isinstance(operand, list):
                normalized[field] = [
                    operator,
                    [
                        resolve_exact_name(
                            (
                                meta.get_field(field).options
                                if meta
                                and meta.get_field(field)
                                and meta.get_field(field).fieldtype == "Link"
                                and meta.get_field(field).options
                                else ""
                            ),
                            item,
                        )
                        if (
                            isinstance(item, str)
                            and meta
                            and meta.get_field(field)
                            and meta.get_field(field).fieldtype == "Link"
                            and meta.get_field(field).options
                        )
                        else item
                        for item in operand
                    ],
                ]
            continue

        if operator:
            value = operand

        if isinstance(value, str):
            clean_value = value.strip()

            if clean_value.casefold() in placeholder_values:
                continue

            if meta:
                try:
                    df = meta.get_field(field)

                    if df:
                        # Link fields: resolve against linked DocType.
                        if (
                            df.fieldtype == "Link"
                            and df.options
                        ):
                            value = resolve_exact_name(
                                df.options,
                                clean_value,
                            )

                        # Data fields: resolve minor punctuation/case
                        # differences against actual ERPNext values.
                        elif df.fieldtype == "Data":
                            target = normalize_text(clean_value)

                            try:
                                rows = frappe.get_list(
                                    doctype,
                                    fields=[field],
                                    filters={
                                        field: [
                                            "like",
                                            f"%{clean_value}%",
                                        ]
                                    },
                                    limit_page_length=50,
                                )

                                matches = []

                                for row in rows:
                                    actual_value = row.get(field)

                                    if not isinstance(
                                        actual_value,
                                        str,
                                    ):
                                        continue

                                    if (
                                        normalize_text(actual_value)
                                        == target
                                    ):
                                        if (
                                            actual_value
                                            not in matches
                                        ):
                                            matches.append(
                                                actual_value
                                            )

                                if len(matches) == 1:
                                    value = matches[0]

                            except Exception:
                                pass

                except Exception:
                    pass

        if operator:
            normalized[field] = [
                operator,
                value,
            ]
        else:
            normalized[field] = value

    return normalized



def validate_filters(doctype, filters):
    if not isinstance(filters, dict):
        return {}

    valid_fields = get_valid_fields(doctype)
    safe_filters = {}

    allowed_operators = {
        "=",
        "!=",
        ">",
        "<",
        ">=",
        "<=",
        "like",
        "not like",
        "in",
        "not in",
        "between",
        "is",
    }

    for field, value in filters.items():
        if not isinstance(field, str):
            continue

        if field not in valid_fields:
            continue

        if isinstance(value, (str, int, float, bool)):
            safe_filters[field] = value
            continue

        # Frappe operator format:
        # ["between", ["2026-09-01", "2026-09-30"]]
        if (
            isinstance(value, list)
            and len(value) == 2
            and value[0] in allowed_operators
        ):
            operator = value[0]
            operand = value[1]

            if isinstance(
                operand,
                (str, int, float, bool),
            ):
                safe_filters[field] = [
                    operator,
                    operand,
                ]
                continue

            if isinstance(operand, list):
                safe_operand = [
                    item
                    for item in operand
                    if isinstance(
                        item,
                        (str, int, float, bool),
                    )
                ]

                if safe_operand:
                    safe_filters[field] = [
                        operator,
                        safe_operand,
                    ]

                continue

        # Simple list values:
        # ["Customer A", "Customer B"]
        if isinstance(value, list):
            safe_values = [
                item
                for item in value
                if isinstance(
                    item,
                    (str, int, float, bool),
                )
            ]

            if safe_values:
                safe_filters[field] = safe_values

            continue

        # JSON operator format:
        # {"operator": "between", "value": [...]}
        if isinstance(value, dict):
            operator = value.get("operator")
            operand = value.get("value")

            if operator not in allowed_operators:
                continue

            if isinstance(
                operand,
                (str, int, float, bool),
            ):
                safe_filters[field] = [
                    operator,
                    operand,
                ]
                continue

            if isinstance(operand, list):
                safe_operand = [
                    item
                    for item in operand
                    if isinstance(
                        item,
                        (str, int, float, bool),
                    )
                ]

                if safe_operand:
                    safe_filters[field] = [
                        operator,
                        safe_operand,
                    ]

    return safe_filters

def validate_order_by(doctype, order_by):
    valid_fields = get_valid_fields(doctype)

    if not isinstance(order_by, str):
        return "creation desc"

    parts = order_by.strip().split()

    if len(parts) != 2:
        return "creation desc"

    field = parts[0]
    direction = parts[1].lower()

    if field not in valid_fields:
        return "creation desc"

    if direction not in {"asc", "desc"}:
        return "creation desc"

    return f"{field} {direction}"


def validate_limit(limit, default=20):
    try:
        limit = int(limit)
    except Exception:
        limit = default

    if limit < 1:
        limit = 1

    return min(limit, MAX_LIST_LIMIT)


def validate_fields(doctype, fields):
    valid_fields = get_valid_fields(doctype)

    if not isinstance(fields, list):
        fields = []

    result = []

    for field in fields:
        if not isinstance(field, str):
            continue

        field = field.strip()

        # Parent-prefixed fields are handled separately for child tables.
        if "." in field:
            continue

        if field in valid_fields and field not in result:
            result.append(field)

    if "name" not in result:
        result.insert(0, "name")

    return result[:20]


# =========================================================
# CHILD TABLE SUPPORT
# =========================================================


def is_child_doctype(doctype):
    try:
        return bool(frappe.get_meta(doctype).istable)
    except Exception:
        return False


def get_child_parent_doctype(child_doctype):
    if not is_child_doctype(child_doctype):
        return None

    try:
        rows = frappe.get_all(
            "DocField",
            filters={
                "fieldtype": "Table",
                "options": child_doctype,
            },
            fields=["parent"],
            limit_page_length=50,
        )
    except Exception:
        return None

    for row in rows:
        parent = row.get("parent")

        if not parent:
            continue

        try:
            if not frappe.get_meta(parent).istable:
                return parent
        except Exception:
            continue

    return None


def get_permissioned_child_rows(
    child_doctype,
    filters=None,
    fields=None,
    limit=20,
    order_by="creation desc",
):
    """
    Child rows are exposed only when the parent DocType is readable.
    """

    parent_doctype = get_child_parent_doctype(child_doctype)

    if not parent_doctype:
        return []

    try:
        parent_rows = frappe.get_list(
            parent_doctype,
            fields=["name"],
            limit_page_length=0,
        )
    except frappe.PermissionError:
        return []
    except Exception:
        return []

    parent_names = [
        row.get("name")
        for row in parent_rows
        if row.get("name")
    ]

    if not parent_names:
        return []

    child_filters = dict(filters or {})
    child_filters["parent"] = ["in", parent_names]

    safe_fields = validate_fields(
        child_doctype,
        fields or [],
    )

    if "parent" not in safe_fields:
        safe_fields.append("parent")

    try:
        return frappe.get_list(
            child_doctype,
            filters=child_filters,
            fields=safe_fields,
            order_by=order_by,
            limit_page_length=limit,
        )
    except Exception:
        return []


def enrich_child_rows(
    child_doctype,
    rows,
    requested_fields,
):
    parent_doctype = get_child_parent_doctype(child_doctype)

    if not parent_doctype:
        return rows

    parent_fields = get_valid_fields(parent_doctype)

    wanted = {"name"}
    mapping = {}

    for requested in requested_fields:
        if not isinstance(requested, str):
            continue

        if "." not in requested:
            continue

        prefix, fieldname = requested.split(".", 1)

        if prefix not in {
            "parent",
            "invoice",
            "document",
        }:
            continue

        if fieldname in parent_fields:
            wanted.add(fieldname)
            mapping[requested] = fieldname

    if len(wanted) == 1:
        return rows

    parent_names = list(
        {
            row.get("parent")
            for row in rows
            if row.get("parent")
        }
    )

    if not parent_names:
        return rows

    try:
        parent_rows = frappe.get_list(
            parent_doctype,
            filters={"name": ["in", parent_names]},
            fields=list(wanted),
            limit_page_length=0,
        )
    except Exception:
        return rows

    parent_map = {
        row.get("name"): row
        for row in parent_rows
    }

    enriched = []

    for row in rows:
        new_row = dict(row)
        parent_row = parent_map.get(
            row.get("parent"),
            {},
        )

        for requested, fieldname in mapping.items():
            new_row[requested] = parent_row.get(fieldname)

        enriched.append(new_row)

    return enriched


# =========================================================
# AGGREGATION / RANKING
# =========================================================


def _get_permissioned_rows(
    doctype,
    filters,
    fields,
    limit_page_length=0,
    order_by=None,
):
    if is_child_doctype(doctype):
        return get_permissioned_child_rows(
            doctype,
            filters=filters,
            fields=fields,
            limit=limit_page_length or 50000,
            order_by=order_by or "creation desc",
        )

    kwargs = {
        "filters": filters,
        "fields": fields,
        "limit_page_length": limit_page_length,
    }

    if order_by:
        kwargs["order_by"] = order_by

    return frappe.get_list(
        doctype,
        **kwargs,
    )


def aggregate_numeric(
    doctype,
    filters,
    field,
    operation,
):
    numeric_fields = get_numeric_fields(doctype)

    if field not in numeric_fields:
        return {
            "success": False,
            "error": (
                f"'{field}' is not a valid numeric "
                f"field for {doctype}."
            ),
        }

    try:
        rows = _get_permissioned_rows(
            doctype,
            filters,
            [field],
            limit_page_length=0,
        )
    except frappe.PermissionError:
        return {
            "success": False,
            "error": (
                "You do not have permission to "
                "read this ERPNext data."
            ),
        }
    except Exception:
        return {
            "success": False,
            "error": (
                "The ERPNext data could not be read."
            ),
        }

    values = []

    for row in rows:
        value = row.get(field)

        try:
            if value is not None:
                values.append(float(value))
        except Exception:
            continue

    if not values:
        result = 0
    elif operation == "sum":
        result = sum(values)
    elif operation == "average":
        result = sum(values) / len(values)
    elif operation == "min":
        result = min(values)
    elif operation == "max":
        result = max(values)
    else:
        return {
            "success": False,
            "error": "Unsupported numeric operation.",
        }

    return {
        "success": True,
        "operation": operation,
        "doctype": doctype,
        "field": field,
        "value": result,
        "record_count": len(values),
        "filters": filters,
    }



def group_and_aggregate(
    doctype,
    filters,
    group_by,
    numeric_field,
    operation,
    limit,
):
    valid_fields = get_valid_fields(doctype)
    numeric_fields = get_numeric_fields(doctype)

    if group_by not in valid_fields:
        return {
            "success": False,
            "error": f"Invalid grouping field: {group_by}",
        }

    if numeric_field not in numeric_fields:
        return {
            "success": False,
            "error": f"Invalid numeric field: {numeric_field}",
        }

    limit = min(
        validate_limit(limit, MAX_GROUP_LIMIT),
        MAX_GROUP_LIMIT,
    )

    try:
        rows = _get_permissioned_rows(
            doctype,
            filters,
            [group_by, numeric_field],
            limit_page_length=0,
        )
    except frappe.PermissionError:
        return {
            "success": False,
            "error": (
                "You do not have permission "
                "to read this ERPNext data."
            ),
        }
    except Exception:
        return {
            "success": False,
            "error": "The ERPNext data could not be read.",
        }

    groups = {}

    for row in rows:
        key = row.get(group_by)

        if key in (None, ""):
            continue

        try:
            value = float(row.get(numeric_field) or 0)
        except Exception:
            value = 0.0

        group = groups.setdefault(
            key,
            {
                "group": key,
                "total": 0.0,
                "count": 0,
                "min": None,
                "max": None,
            },
        )

        group["total"] += value
        group["count"] += 1

        if group["min"] is None or value < group["min"]:
            group["min"] = value

        if group["max"] is None or value > group["max"]:
            group["max"] = value

    result = []

    for group in groups.values():
        if operation == "sum":
            metric = group["total"]
        elif operation == "average":
            metric = (
                group["total"] / group["count"]
                if group["count"]
                else 0
            )
        elif operation == "min":
            metric = group["min"] if group["min"] is not None else 0
        elif operation == "max":
            metric = group["max"] if group["max"] is not None else 0
        else:
            metric = group["total"]

        group["value"] = metric
        result.append(group)

    if operation == "min":
        result.sort(key=lambda row: row["value"])
    else:
        result.sort(key=lambda row: row["value"], reverse=True)

    return {
        "success": True,
        "operation": operation,
        "doctype": doctype,
        "group_by": group_by,
        "numeric_field": numeric_field,
        "results": result[:limit],
        "filters": filters,
    }


def group_and_rank(
    doctype,
    filters,
    group_by,
    numeric_field,
    operation,
    limit,
):
    valid_fields = get_valid_fields(doctype)
    numeric_fields = get_numeric_fields(doctype)

    if group_by not in valid_fields:
        return {
            "success": False,
            "error": f"Invalid grouping field: {group_by}",
        }

    if numeric_field not in numeric_fields:
        return {
            "success": False,
            "error": f"Invalid numeric field: {numeric_field}",
        }

    limit = min(
        validate_limit(limit, MAX_GROUP_LIMIT),
        MAX_GROUP_LIMIT,
    )

    try:
        rows = _get_permissioned_rows(
            doctype,
            filters,
            [group_by, numeric_field],
            limit_page_length=0,
        )
    except frappe.PermissionError:
        return {
            "success": False,
            "error": (
                "You do not have permission "
                "to read this ERPNext data."
            ),
        }
    except Exception:
        return {
            "success": False,
            "error": "The ERPNext data could not be read.",
        }

    groups = {}

    for row in rows:
        key = row.get(group_by)

        if key in (None, ""):
            continue

        try:
            value = float(row.get(numeric_field) or 0)
        except Exception:
            value = 0

        if key not in groups:
            groups[key] = {
                "group": key,
                "total": 0,
                "count": 0,
            }

        groups[key]["count"] += 1

        if operation in {
            "ranking",
            "sum",
            "max",
            "min",
            "average",
        }:
            groups[key]["total"] += value

    result = list(groups.values())

    result.sort(
        key=lambda row: row["total"],
        reverse=True,
    )

    return {
        "success": True,
        "operation": "ranking",
        "doctype": doctype,
        "group_by": group_by,
        "numeric_field": numeric_field,
        "results": result[:limit],
        "filters": filters,
    }


# =========================================================
# RESULT FORMATTING
# =========================================================


def _human_label(field):
    if not isinstance(field, str):
        return str(field)

    return field.replace("_", " ").strip().title()


def format_simple_answer(question, result):
    operation = result.get("operation")
    doctype = result.get("doctype", "ERPNext")

    if operation == "count":
        count = result.get("count", 0)
        noun = doctype

        return f"There are {count} {noun} records in ERPNext."

    if operation in {
        "sum",
        "average",
        "min",
        "max",
    }:
        if result.get("group_by"):
            rows = result.get("results", [])

            if not rows:
                return "No matching ERPNext records were found."

            group_label = _human_label(
                result.get("group_by")
            )

            metric_labels = {
                "sum": "total",
                "average": "average",
                "min": "minimum",
                "max": "maximum",
            }

            metric_label = metric_labels.get(
                operation,
                operation,
            )

            lines = [
                f"Here are the {group_label.lower()}-wise "
                f"{metric_label} values:"
            ]

            for index, row in enumerate(rows, start=1):
                group = row.get("group", "")
                value = row.get(
                    "value",
                    row.get("total", 0),
                )

                try:
                    value_text = f"{float(value):,.2f}"
                except Exception:
                    value_text = str(value)

                lines.append(
                    f"{index}. {group}: {value_text}"
                )

            return "\n".join(lines)

    if operation in {
        "sum",
        "average",
        "min",
        "max",
    }:
        value = result.get("value", 0)
        field = result.get("field", "value")

        try:
            formatted = f"{float(value):,.2f}"
        except Exception:
            formatted = str(value)

        labels = {
            "sum": "total",
            "average": "average",
            "min": "minimum",
            "max": "maximum",
        }

        return (
            f"The {labels[operation]} "
            f"{_human_label(field)} for "
            f"{doctype} is {formatted}."
        )

    if operation == "ranking":
        rows = result.get("results", [])

        if not rows:
            return "No matching ERPNext records were found."

        q = " ".join(
            (question or "").strip().split()
        ).casefold()

        # -------------------------------------------------
        # SINGLE TOP ITEM
        # -------------------------------------------------

        single_top_item_request = bool(
            re.search(
                r"\bwho\s+is\s+the\s+top\s+item\b",
                q,
            )
            or re.search(
                r"\btop\s+item\b",
                q,
            )
            or re.search(
                r"\btop\s+items?\b",
                q,
            )
            or re.search(
                r"\btop\s+selling\s+item\b",
                q,
            )
            or re.search(
                r"\btop\s+selling\s+items?\b",
                q,
            )
        )

        if single_top_item_request:
            row = rows[0]

            # -------------------------------------------------
            # TOP ITEM BY QUANTITY
            # -------------------------------------------------

            if result.get("ranking_metric") == "quantity":
                item_name = (
                    row.get("item_name")
                    or row.get("group")
                    or row.get("item_code")
                    or "Unknown item"
                )

                item_code = row.get("item_code")
                total_qty = row.get("total_qty", 0)

                try:
                    total_qty_text = f"{float(total_qty):,.0f}"
                except Exception:
                    total_qty_text = str(total_qty)

                if item_code and item_name != item_code:
                    item_label = (
                        f"{item_name} ({item_code})"
                    )
                else:
                    item_label = item_name

                return (
                    f"The top selling item by quantity is "
                    f"{item_label} with {total_qty_text} "
                    f"units sold."
                )

            item_name = (
                row.get("item_name")
                or row.get("group")
                or row.get("item_code")
                or "Unknown item"
            )

            item_code = row.get("item_code")

            total_sales = row.get(
                "total_sales",
                row.get("total", 0),
            )

            try:
                total_sales_text = (
                    f"{float(total_sales):,.2f}"
                )
            except Exception:
                total_sales_text = str(total_sales)

            if item_code and item_name != item_code:
                item_label = (
                    f"{item_name} ({item_code})"
                )
            else:
                item_label = item_name

            return (
                f"The top item is {item_label} "
                f"with total sales of "
                f"{total_sales_text}."
            )

        # -------------------------------------------------
        # SINGLE TOP CUSTOMER / SUPPLIER
        # -------------------------------------------------

        single_top_request = bool(
            re.search(
                r"\bwho\s+is\s+the\s+top\s+"
                r"(customer|supplier)\b",
                q,
            )
            or re.search(
                r"\btop\s+(customer|supplier)\b",
                q,
            )
        )

        if single_top_request and rows:
            row = rows[0]

            group = row.get("group", "")
            total = row.get("total", 0)

            try:
                total_text = f"{float(total):,.2f}"
            except Exception:
                total_text = str(total)

            if doctype == "Customer":
                return (
                    f"The top customer is {group} "
                    f"with total sales of {total_text}."
                )

            if doctype == "Supplier":
                return (
                    f"The top supplier is {group} "
                    f"with total purchases of {total_text}."
                )

        # -------------------------------------------------
        # NORMAL RANKING LIST
        # -------------------------------------------------

        lines = []

        for index, row in enumerate(rows, start=1):
            group = row.get("group", "")
            total = row.get("total", 0)
            count = row.get("count", 0)

            try:
                total_text = f"{float(total):,.2f}"
            except Exception:
                total_text = str(total)

            lines.append(
                f"{index}. {group}: "
                f"{total_text} ({count} records)"
            )

        return (
            "Here are the matching ERPNext results:\n"
            + "\n".join(lines)
        )


def _format_value(value):
    if value is None:
        return None

    if hasattr(value, "strftime"):
        return value.strftime("%d %b %Y")

    if isinstance(value, float):
        return f"{value:,.2f}"

    return str(value)


def format_list_answer(question, result):
    rows = result.get("records", [])
    doctype = result.get("doctype", "ERPNext")

    if not rows:
        return "No matching ERPNext records were found."

    q = " ".join(
        (question or "").strip().split()
    ).casefold()

    # -----------------------------------------------------
    # RATE / PRICE QUERY
    # -----------------------------------------------------

    is_rate_query = bool(
        re.search(
            r"\b(?:rate|price)\b",
            q,
            re.IGNORECASE,
        )
    )

    if is_rate_query:
        rate_rows = []

        for row in rows:
            rate = row.get("standard_selling_rate")

            if rate in (None, ""):
                rate = row.get("standard_rate")

            if rate in (None, ""):
                continue

            try:
                numeric_rate = float(rate)

                # Ignore zero rates when another real rate exists.
                if numeric_rate == 0:
                    continue

            except (TypeError, ValueError):
                pass

            rate_rows.append(
                {
                    "row": row,
                    "rate": rate,
                }
            )

        if not rate_rows:
            return "The matching item does not have a rate."

        if len(rate_rows) == 1:
            row = rate_rows[0]["row"]
            rate = rate_rows[0]["rate"]

            item_name = (
                row.get("item_name")
                or row.get("name")
                or "the item"
            )

            try:
                rate_text = f"{float(rate):.2f}"
            except (TypeError, ValueError):
                rate_text = str(rate)

            return (
                f"The rate for {item_name} "
                f"is {rate_text}."
            )

        # If multiple matching records have rates,
        # prefer the first non-zero rate.
        selected = rate_rows[0]

        row = selected["row"]
        rate = selected["rate"]

        item_name = (
            row.get("item_name")
            or row.get("name")
            or "the item"
        )

        try:
            rate_text = f"{float(rate):.2f}"
        except (TypeError, ValueError):
            rate_text = str(rate)

        return (
            f"The rate for {item_name} "
            f"is {rate_text}."
        )

    # -----------------------------------------------------
    # ITEM CODE QUERY
    # -----------------------------------------------------

    if (
        "item code" in q
        or "item codes" in q
    ):
        code_rows = [
            row
            for row in rows
            if row.get("item_code") not in {
                None,
                "",
            }
        ]

        if not code_rows:
            return (
                "The matching item does not have "
                "an item code."
            )

        if len(code_rows) == 1:
            row = code_rows[0]

            item_name = (
                row.get("item_name")
                or row.get("name")
                or "the item"
            )

            item_code = row.get("item_code")

            return (
                f"The item code for {item_name} "
                f"is {item_code}."
            )

        lines = [
            "Here are the matching item codes:"
        ]

        for index, row in enumerate(
            code_rows,
            start=1,
        ):
            item_name = (
                row.get("item_name")
                or row.get("name")
                or "Item"
            )

            item_code = row.get("item_code")

            lines.append(
                f"{index}. {item_name} — "
                f"Item Code: {item_code}"
            )

        return "\n".join(lines)

    # -----------------------------------------------------
    # ITEM NAME QUERY
    # -----------------------------------------------------

    is_item_name_query = (
        "item name" in q
        or "item names" in q
        or "name of item" in q
        or "name of items" in q
    )

    if is_item_name_query:
        name_rows = [
            row
            for row in rows
            if row.get("item_name") not in {
                None,
                "",
            }
        ]

        if not name_rows:
            return (
                "The matching item does not have "
                "an item name."
            )

        requested_name = None

        name_match = re.search(
            r"\bname\s+of\s+"
            r"(?:item|items)\s+"
            r"['\"]?([a-z0-9][a-z0-9 ._-]*)['\"]?"
            r"\s*[\?\.]?$",
            q,
            re.IGNORECASE,
        )

        if not name_match:
            name_match = re.search(
                r"\b(?:item|items)\s+"
                r"(?:name|names)\s+"
                r"(?:for|of)\s+"
                r"['\"]?([a-z0-9][a-z0-9 ._-]*)['\"]?"
                r"\s*[\?\.]?$",
                q,
                re.IGNORECASE,
            )

        if name_match:
            requested_name = (
                name_match.group(1)
                .strip()
                .rstrip("?.!,")
            )

        selected_row = None

        if requested_name:
            exact_rows = [
                row
                for row in name_rows
                if str(
                    row.get("item_name") or ""
                ).casefold()
                == requested_name.casefold()
            ]

            if exact_rows:
                selected_row = exact_rows[0]

        if selected_row is None:
            selected_row = name_rows[0]

        item_name = selected_row.get("item_name")

        if item_name:
            return (
                f"The item name is {item_name}."
            )

        return (
            "The matching item does not have "
            "an item name."
        )

    # -----------------------------------------------------
    # NORMAL LIST QUERY
    # -----------------------------------------------------

    lines = [
        f"Here are the matching {doctype} records:"
    ]

    for index, row in enumerate(
        rows,
        start=1,
    ):
        parts = []

        for field, value in row.items():
            value = _format_value(value)

            if value is None:
                continue

            parts.append(
                f"{_human_label(field)}: {value}"
            )

        if parts:
            lines.append(
                f"{index}. " + " — ".join(parts)
            )

    return "\n".join(lines)
    
# =========================================================
# SAFE QUERY EXECUTION
# =========================================================


def execute_erp_query(intent):
    if not isinstance(intent, dict):
        return {
            "success": False,
            "error": (
                "Could not understand "
                "the ERPNext question."
            ),
        }

    doctype = intent.get("doctype")
    operation = intent.get("operation")

    if not isinstance(doctype, str) or not doctype.strip():
        return {
            "success": False,
            "error": "No valid ERPNext DocType was identified.",
        }

    doctype = doctype.strip()

    # -----------------------------------------------------
    # TOP ITEM SALES RANKING
    # -----------------------------------------------------

    if doctype == "__item_sales_ranking__":

        limit = min(
            validate_limit(
                intent.get("limit", 1),
                MAX_GROUP_LIMIT,
            ),
            MAX_GROUP_LIMIT,
        )

        ranking_metric = intent.get(
            "ranking_metric",
            "sales",
        )

        if ranking_metric == "quantity":
            order_by_sql = "total_qty DESC"
        else:
            order_by_sql = "total_sales DESC"

        try:
            rows = frappe.db.sql(
                f"""
                SELECT
                    sii.item_code,
                    sii.item_name,
                    SUM(sii.qty) AS total_qty,
                    SUM(sii.amount) AS total_sales,
                    COUNT(*) AS invoice_item_count
                FROM `tabSales Invoice Item` sii
                INNER JOIN `tabSales Invoice` si
                    ON si.name = sii.parent
                WHERE si.docstatus = 1
                  AND sii.item_code IS NOT NULL
                  AND sii.item_code != ''
                GROUP BY
                    sii.item_code,
                    sii.item_name
                ORDER BY
                    {order_by_sql}
                LIMIT %s
                """,
                (limit,),
                as_dict=True,
            )

        except frappe.PermissionError:
            return {
                "success": False,
                "error": (
                    "You do not have permission "
                    "to read Sales Invoice item data."
                ),
            }

        except Exception:
            return {
                "success": False,
                "error": (
                    "The item sales data "
                    "could not be read."
                ),
            }

        results = []

        for row in rows:
            try:
                total_qty = float(
                    row.get("total_qty") or 0
                )
            except Exception:
                total_qty = 0

            try:
                total_sales = float(
                    row.get("total_sales") or 0
                )
            except Exception:
                total_sales = 0

            try:
                invoice_item_count = int(
                    row.get("invoice_item_count") or 0
                )
            except Exception:
                invoice_item_count = 0

            results.append(
                {
                    "group": (
                        row.get("item_name")
                        or row.get("item_code")
                    ),
                    "item_code": row.get(
                        "item_code"
                    ),
                    "item_name": row.get(
                        "item_name"
                    ),
                    "total": (
                        total_qty
                        if ranking_metric == "quantity"
                        else total_sales
                    ),
                    "total_sales": total_sales,
                    "total_qty": total_qty,
                    "count": invoice_item_count,
                }
            )

        return {
            "success": True,
            "operation": "ranking",
            "doctype": "Item",
            "group_by": "item_code",
            "numeric_field": (
                "Sales Invoice Item.qty"
                if ranking_metric == "quantity"
                else "Sales Invoice Item.amount"
            ),
            "ranking_metric": ranking_metric,
            "results": results,
            "filters": {
                "Sales Invoice": {
                    "docstatus": 1,
                }
            },
        }

    # -----------------------------------------------------
    # COMBINED GENERIC ITEM QUERY
    # -----------------------------------------------------

    if doctype == "__combined_item__":
        filters = intent.get("filters", {})

        if not isinstance(filters, dict):
            filters = {}

        item_name = filters.get("item_name")

        if isinstance(item_name, str):
            item_name = item_name.strip()

        if not item_name:
            item_name = None

        if operation == "count":
            try:
                if item_name:
                    item_filters = {
                        "item_name": ["like", f"%{item_name}%"]
                    }

                    items_filters = {
                        "item_name": ["like", f"%{item_name}%"]
                    }

                    item_count = frappe.db.count(
                        "Item",
                        filters=item_filters,
                    )

                    items_count = frappe.db.count(
                        "Items",
                        filters=items_filters,
                    )
                else:
                    item_count = frappe.db.count(
                        "Item"
                    )

                    items_count = frappe.db.count(
                        "Items"
                    )

                return {
                    "success": True,
                    "operation": "count",
                    "doctype": "Item + Items",
                    "count": (
                        item_count
                        + items_count
                    ),
                    "filters": filters,
                    "sources": {
                        "Item": item_count,
                        "Items": items_count,
                    },
                }

            except Exception:
                return {
                    "success": False,
                    "error": (
                        "The item data "
                        "could not be read."
                    ),
                }

        if operation == "list":
            limit = validate_limit(
                intent.get("limit", 20),
                20,
            )

            requested_fields = intent.get("fields", [])
            if not isinstance(requested_fields, list):
                requested_fields = []

            rate_query = (
                "standard_rate" in requested_fields
                or "standard_selling_rate" in requested_fields
            )

            try:
                item_fields = [
                    "name",
                    "item_name",
                    "creation",
                ]

                items_fields = [
                    "name",
                    "item_code",
                    "item_name",
                    "creation",
                ]

                if rate_query:
                    item_fields.append("standard_rate")
                    items_fields.append("standard_selling_rate")

                item_kwargs = {
                    "fields": item_fields,
                    "order_by": "creation desc",
                    "limit_page_length": limit,
                }

                items_kwargs = {
                    "fields": items_fields,
                    "order_by": "creation desc",
                    "limit_page_length": limit,
                }

                if item_name:
                    item_kwargs["filters"] = {
                        "item_name": [
                            "like",
                            f"%{item_name}%",
                        ]
                    }

                    items_kwargs["filters"] = {
                        "item_name": [
                            "like",
                            f"%{item_name}%",
                        ]
                    }

                item_rows = frappe.get_list(
                    "Item",
                    **item_kwargs,
                )

                items_rows = frappe.get_list(
                    "Items",
                    **items_kwargs,
                )

            except frappe.PermissionError:
                return {
                    "success": False,
                    "error": (
                        "You do not have permission "
                        "to read this item data."
                    ),
                }

            except Exception:
                return {
                    "success": False,
                    "error": (
                        "The item data "
                        "could not be read."
                    ),
                }

            combined = []

            for row in item_rows:
                combined.append(
                    {
                        "name": row.get("name"),
                        "item_name": row.get(
                            "item_name"
                        ),
                        "item_code": None,
                        "creation": row.get(
                            "creation"
                        ),
                        "standard_rate": row.get(
                            "standard_rate"
                        ),
                        "standard_selling_rate": None,
                        "_source_doctype": "Item",
                    }
                )

            for row in items_rows:
                combined.append(
                    {
                        "name": row.get("name"),
                        "item_name": row.get(
                            "item_name"
                        ),
                        "item_code": row.get(
                            "item_code"
                        ),
                        "creation": row.get(
                            "creation"
                        ),
                        "standard_rate": None,
                        "standard_selling_rate": row.get(
                            "standard_selling_rate"
                        ),
                        "_source_doctype": "Items",
                    }
                )

            combined.sort(
                key=lambda row: (
                    row.get("creation")
                    or frappe.utils.get_datetime(
                        "1900-01-01"
                    )
                ),
                reverse=True,
            )

            combined = combined[:limit]

            return {
                "success": True,
                "operation": "list",
                "doctype": "Item + Items",
                "records": combined,
                "limit": limit,
                "order_by": "creation desc",
                "filters": filters,
            }

        return {
            "success": False,
            "error": (
                "This generic item question "
                "supports count and list operations."
            ),
        }

    try:
        if not frappe.db.exists("DocType", doctype):
            return {
                "success": False,
                "error": (
                    "The requested ERPNext "
                    "DocType does not exist."
                ),
            }
    except Exception:
        return {
            "success": False,
            "error": "The ERPNext DocType could not be verified.",
        }

    if doctype in EXCLUDED_DOCTYPES:
        return {
            "success": False,
            "error": "This ERPNext data request is not supported.",
        }

    if operation not in READ_OPERATIONS:
        return {
            "success": False,
            "error": (
                "Only read-only ERPNext "
                "operations are supported."
            ),
        }

    filters = normalize_filters(
        doctype,
        intent.get("filters", {}),
    )

    filters = validate_filters(
        doctype,
        filters,
    )

    # -----------------------------------------------------
    # COUNT
    # -----------------------------------------------------

    if operation == "count":
        try:
            rows = _get_permissioned_rows(
                doctype,
                filters,
                ["name"],
                limit_page_length=0,
            )
        except frappe.PermissionError:
            return {
                "success": False,
                "error": (
                    "You do not have permission "
                    "to read this ERPNext data."
                ),
            }
        except Exception:
            return {
                "success": False,
                "error": "The ERPNext data could not be read.",
            }

        return {
            "success": True,
            "operation": "count",
            "doctype": doctype,
            "count": len(rows),
            "filters": filters,
        }

    # -----------------------------------------------------
    # LIST
    # -----------------------------------------------------

    if operation == "list":
        requested_fields = intent.get("fields", [])

        if not isinstance(requested_fields, list):
            requested_fields = []

        direct_fields = []
        parent_fields = []

        for field in requested_fields:
            if not isinstance(field, str):
                continue

            if "." in field:
                prefix, fieldname = field.split(".", 1)

                if prefix in {
                    "parent",
                    "invoice",
                    "document",
                }:
                    parent_fields.append(field)

                continue

            if (
                is_child_doctype(doctype)
                and field in {
                    "customer",
                    "supplier",
                    "company",
                }
            ):
                parent_fields.append(field)
            else:
                direct_fields.append(field)

        direct_fields = validate_fields(
            doctype,
            direct_fields,
        )

        limit = validate_limit(
            intent.get("limit", 20),
            20,
        )

        order_by = validate_order_by(
            doctype,
            intent.get("order_by"),
        )

        try:
            if is_child_doctype(doctype):
                rows = get_permissioned_child_rows(
                    doctype,
                    filters=filters,
                    fields=direct_fields,
                    limit=limit,
                    order_by=order_by,
                )

                rows = enrich_child_rows(
                    doctype,
                    rows,
                    direct_fields + parent_fields,
                )
            else:
                rows = frappe.get_list(
                    doctype,
                    filters=filters,
                    fields=direct_fields,
                    order_by=order_by,
                    limit_page_length=limit,
                )
        except frappe.PermissionError:
            return {
                "success": False,
                "error": (
                    "You do not have permission "
                    "to read this ERPNext data."
                ),
            }
        except Exception:
            return {
                "success": False,
                "error": "The ERPNext data could not be read.",
            }

        return {
            "success": True,
            "operation": "list",
            "doctype": doctype,
            "records": rows,
            "limit": limit,
            "order_by": order_by,
            "filters": filters,
        }

    # -----------------------------------------------------
    # NUMERIC OPERATIONS
    # -----------------------------------------------------

    if operation in {
        "sum",
        "average",
        "min",
        "max",
    }:
        numeric_field = intent.get("numeric_field")

        if isinstance(numeric_field, list):
            numeric_field = (
                numeric_field[0]
                if numeric_field
                else None
            )

        if not isinstance(numeric_field, str):
            return {
                "success": False,
                "error": (
                    "No valid numeric field "
                    "was identified."
                ),
            }

        group_by = intent.get("group_by")

        if isinstance(group_by, list):
            group_by = group_by[0] if group_by else None

        if isinstance(group_by, str) and group_by:
            return group_and_aggregate(
                doctype,
                filters,
                group_by,
                numeric_field,
                operation,
                intent.get("limit", 10),
            )

        return aggregate_numeric(
            doctype,
            filters,
            numeric_field,
            operation,
        )

        # -----------------------------------------------------
    # RANKING
    # -----------------------------------------------------

    if operation == "ranking":
        group_by = intent.get("group_by")
        numeric_field = intent.get("numeric_field")

        if isinstance(group_by, list):
            group_by = group_by[0] if group_by else None

        if isinstance(numeric_field, list):
            numeric_field = (
                numeric_field[0]
                if numeric_field
                else None
            )

        # -------------------------------------------------
        # CUSTOMER SALES RANKING
        # -------------------------------------------------

        if doctype == "Customer":
            try:
                sales_rows = _get_permissioned_rows(
                    "Sales Invoice",
                    {"docstatus": 1},
                    [
                        "customer",
                        "grand_total",
                    ],
                    limit_page_length=0,
                )
            except frappe.PermissionError:
                return {
                    "success": False,
                    "error": (
                        "You do not have permission "
                        "to read Sales Invoice data."
                    ),
                }
            except Exception:
                return {
                    "success": False,
                    "error": (
                        "The Sales Invoice data "
                        "could not be read."
                    ),
                }

            customer_totals = {}

            for row in sales_rows:
                customer = row.get("customer")

                if customer in (None, ""):
                    continue

                try:
                    amount = float(
                        row.get("grand_total") or 0
                    )
                except Exception:
                    amount = 0

                if customer not in customer_totals:
                    customer_totals[customer] = {
                        "group": customer,
                        "total": 0,
                        "count": 0,
                    }

                customer_totals[customer]["total"] += amount
                customer_totals[customer]["count"] += 1

            results = list(
                customer_totals.values()
            )

            results.sort(
                key=lambda row: row["total"],
                reverse=True,
            )

            limit = min(
                validate_limit(
                    intent.get("limit", 10),
                    MAX_GROUP_LIMIT,
                ),
                MAX_GROUP_LIMIT,
            )

            return {
                "success": True,
                "operation": "ranking",
                "doctype": "Customer",
                "group_by": "customer",
                "numeric_field": "Sales Invoice.grand_total",
                "results": results[:limit],
                "filters": {
                    "Sales Invoice": {
                        "docstatus": 1,
                    }
                },
            }

        # -------------------------------------------------
        # SUPPLIER PURCHASE RANKING
        # -------------------------------------------------

        if doctype == "Supplier":
            try:
                purchase_rows = _get_permissioned_rows(
                    "Purchase Invoice",
                    {"docstatus": 1},
                    [
                        "supplier",
                        "grand_total",
                    ],
                    limit_page_length=0,
                )
            except frappe.PermissionError:
                return {
                    "success": False,
                    "error": (
                        "You do not have permission "
                        "to read Purchase Invoice data."
                    ),
                }
            except Exception:
                return {
                    "success": False,
                    "error": (
                        "The Purchase Invoice data "
                        "could not be read."
                    ),
                }

            supplier_totals = {}

            for row in purchase_rows:
                supplier = row.get("supplier")

                if supplier in (None, ""):
                    continue

                try:
                    amount = float(
                        row.get("grand_total") or 0
                    )
                except Exception:
                    amount = 0

                if supplier not in supplier_totals:
                    supplier_totals[supplier] = {
                        "group": supplier,
                        "total": 0,
                        "count": 0,
                    }

                supplier_totals[supplier]["total"] += amount
                supplier_totals[supplier]["count"] += 1

            results = list(
                supplier_totals.values()
            )

            results.sort(
                key=lambda row: row["total"],
                reverse=True,
            )

            limit = min(
                validate_limit(
                    intent.get("limit", 10),
                    MAX_GROUP_LIMIT,
                ),
                MAX_GROUP_LIMIT,
            )

            return {
                "success": True,
                "operation": "ranking",
                "doctype": "Supplier",
                "group_by": "supplier",
                "numeric_field": "Purchase Invoice.grand_total",
                "results": results[:limit],
                "filters": {
                    "Purchase Invoice": {
                        "docstatus": 1,
                    }
                },
            }

        # -------------------------------------------------
        # GENERIC RANKING
        # -------------------------------------------------

        if not isinstance(group_by, str):
            return {
                "success": False,
                "error": "No grouping field was identified.",
            }

        if not isinstance(numeric_field, str):
            return {
                "success": False,
                "error": "No numeric field was identified.",
            }

        return group_and_rank(
            doctype,
            filters,
            group_by,
            numeric_field,
            operation,
            intent.get("limit", 10),
        )

    return {
        "success": False,
        "error": "The ERPNext query could not be executed.",
    }


# =========================================================
# NATURAL LANGUAGE ANSWER
# =========================================================


def generate_answer(question, result):
    if result.get("operation") == "list":
        return format_list_answer(
            question,
            result,
        )

    simple_answer = format_simple_answer(
        question,
        result,
    )

    if simple_answer:
        return simple_answer

    # Keep Gemma as a final formatter only. It never gets
    # database access and only sees the already-authorized result.
    prompt = f"""
You are an ERPNext assistant.

Answer the user's question using ONLY this ERPNext result.

User question:
{question}

ERPNext result:
{json.dumps(result, ensure_ascii=False, default=str)}

Rules:
- Do not invent information.
- Do not mention SQL.
- Do not mention internal code.
- Do not claim an action was performed.
- Be concise.
- If there are no records, say so clearly.
"""

    try:
        return ask_gemma(
            prompt,
            timeout=60,
            json_mode=False,
        )
    except requests.RequestException:
        return format_simple_answer(
            question,
            result,
        ) or "The ERPNext data was retrieved successfully."


# =========================================================
# MAIN API
# =========================================================

@frappe.whitelist()
def ask_erp(question):
    if not question:
        return {
            "success": False,
            "answer": "Please enter a question.",
        }

    question = str(question).strip()

    if not question:
        return {
            "success": False,
            "answer": "Please enter a question.",
        }

    try:
        intent = understand_question(question)

        if not intent:
            return {
                "success": False,
                "answer": (
                    "I could not identify the relevant "
                    "ERPNext record type for that question."
                ),
            }

        # Pseudo-doctypes are already handled specially
        # inside execute_erp_query().
        if intent.get("doctype") not in {
            "__combined_item__",
            "__item_sales_ranking__",
        }:
            intent["filters"] = normalize_filters(
                intent.get("doctype"),
                intent.get("filters", {}),
            )

        result = execute_erp_query(intent)

        if not result.get("success"):
            return {
                "success": False,
                "answer": result.get(
                    "error",
                    "I could not answer that ERPNext question.",
                ),
                "intent": intent,
            }

        answer = generate_answer(
            question,
            result,
        )

        return {
            "success": True,
            "answer": answer,
            "intent": intent,
            "result": result,
        }

    except requests.RequestException:
        frappe.log_error(
            frappe.get_traceback(),
            "ERP AI - Ollama Connection Error",
        )

        return {
            "success": False,
            "answer": (
                "ERP AI could not connect "
                "to the local AI model."
            ),
        }

    except frappe.PermissionError:
        return {
            "success": False,
            "answer": (
                "You do not have permission "
                "to read this ERPNext data."
            ),
        }

    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "ERP AI Error",
        )

        return {
            "success": False,
            "answer": (
                "An error occurred while "
                "processing the ERPNext question."
            ),
        }

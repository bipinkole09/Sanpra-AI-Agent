import frappe
import requests
from frappe.utils import getdate
from xml.sax.saxutils import escape


# =========================================================
# TALLY CONFIGURATION
# =========================================================

TALLY_URL = "http://100.101.213.122:9000"


# =========================================================
# HELPER - SEND XML TO TALLY
# =========================================================

def send_to_tally(xml, title):

    print("\n========================================")
    print(title)
    print("========================================")

    try:

        response = requests.post(
            TALLY_URL,
            data=xml.encode("utf-8"),
            headers={
                "Content-Type": "text/xml; charset=utf-8"
            },
            timeout=30
        )

        print("TALLY RESPONSE:")
        print(response.text)

        return response.text

    except Exception as e:

        print("TALLY ERROR:", e)

        return None

def create_tally_ledger(ledger_name, company_name, parent):
    
    ledger_xml_name = escape(str(ledger_name))
    company_xml = escape(str(company_name))
    parent_xml = escape(str(parent))

    ledger_xml = f"""
<ENVELOPE>
<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>
<DESC>
<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>
</DESC>

<DATA>
<TALLYMESSAGE xmlns:UDF="TallyUDF">

<LEDGER NAME="{ledger_xml_name}" ACTION="Create">
<NAME>{ledger_xml_name}</NAME>
<PARENT>{parent_xml}</PARENT>
<ISBILLWISEON>Yes</ISBILLWISEON>
<AFFECTSSTOCK>No</AFFECTSSTOCK>
</LEDGER>

</TALLYMESSAGE>
</DATA>
</BODY>
</ENVELOPE>
"""

    return send_to_tally(
        ledger_xml,
        f"LEDGER - {ledger_name}"
    )

def create_tally_customer(customer_name, company_name):

    customer_xml_name = escape(str(customer_name))
    company_xml = escape(str(company_name))

    customer_xml = f"""
<ENVELOPE>
<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>
<DESC>
<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>
</DESC>

<DATA>
<TALLYMESSAGE xmlns:UDF="TallyUDF">

<LEDGER NAME="{customer_xml_name}" ACTION="Create">
<NAME>{customer_xml_name}</NAME>
<PARENT>Sundry Debtors</PARENT>
<ISBILLWISEON>Yes</ISBILLWISEON>
<AFFECTSSTOCK>No</AFFECTSSTOCK>
</LEDGER>

</TALLYMESSAGE>
</DATA>
</BODY>
</ENVELOPE>
"""

    return send_to_tally(
        customer_xml,
        f"CUSTOMER - {customer_name}"
    )

def customer_after_insert(doc, method=None):

    customer_name = doc.name

    if not doc.accounts:
        print(
            f"AUTO CUSTOMER SYNC SKIPPED: {customer_name} - "
            "No Company found in Customer Accounts"
        )
        return

    for row in doc.accounts:

        if not row.company:
            continue

        company_name = row.company

        print(
            f"AUTO CUSTOMER SYNC: "
            f"{customer_name} -> {company_name}"
        )

        return create_tally_customer(
            customer_name,
            company_name
        )

    print(
        f"AUTO CUSTOMER SYNC SKIPPED: {customer_name} - "
        "No valid Company found"
    )

def customer_after_update(doc, method=None):

    customer_name = doc.name

    if not doc.accounts:
        print(
            f"AUTO CUSTOMER UPDATE SKIPPED: {customer_name} - "
            "No Company found in Customer Accounts"
        )
        return

    for row in doc.accounts:

        if not row.company:
            continue

        company_name = row.company

        print(
            f"AUTO CUSTOMER UPDATE: "
            f"{customer_name} -> {company_name}"
        )

        return create_tally_customer(
            customer_name,
            company_name
        )

    print(
        f"AUTO CUSTOMER UPDATE SKIPPED: {customer_name} - "
        "No valid Company found"
    )

def create_tally_supplier(supplier_name, company_name):

    supplier_xml_name = escape(str(supplier_name))
    company_xml = escape(str(company_name))

    supplier_xml = f"""
<ENVELOPE>
<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>
<DESC>
<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>
</DESC>

<DATA>
<TALLYMESSAGE xmlns:UDF="TallyUDF">

<LEDGER NAME="{supplier_xml_name}" ACTION="Create">
<NAME>{supplier_xml_name}</NAME>
<PARENT>Sundry Creditors</PARENT>
<ISBILLWISEON>Yes</ISBILLWISEON>
<AFFECTSSTOCK>No</AFFECTSSTOCK>
</LEDGER>

</TALLYMESSAGE>
</DATA>
</BODY>
</ENVELOPE>
"""

    return send_to_tally(
        supplier_xml,
        f"SUPPLIER - {supplier_name}"
    )

def supplier_after_insert(doc, method=None):

    supplier_name = doc.name

    if not doc.accounts:
        print(
            f"AUTO SUPPLIER SYNC SKIPPED: {supplier_name} - "
            "No Company found in Supplier Accounts"
        )
        return

    for row in doc.accounts:

        if not row.company:
            continue

        company_name = row.company

        print(
            f"AUTO SUPPLIER SYNC: "
            f"{supplier_name} -> {company_name}"
        )

        return create_tally_supplier(
            supplier_name,
            company_name
        )

    print(
        f"AUTO SUPPLIER SYNC SKIPPED: {supplier_name} - "
        "No valid Company found"
    )


def supplier_after_update(doc, method=None):

    supplier_name = doc.name

    if not doc.accounts:
        print(
            f"AUTO SUPPLIER UPDATE SKIPPED: {supplier_name} - "
            "No Company found in Supplier Accounts"
        )
        return

    for row in doc.accounts:

        if not row.company:
            continue

        company_name = row.company

        print(
            f"AUTO SUPPLIER UPDATE: "
            f"{supplier_name} -> {company_name}"
        )

        return create_tally_supplier(
            supplier_name,
            company_name
        )

    print(
        f"AUTO SUPPLIER UPDATE SKIPPED: {supplier_name} - "
        "No valid Company found"
    )

def create_tally_item(item_name, company_name, item_group, uom):

    item_xml_name = escape(str(item_name))
    company_xml = escape(str(company_name))
    item_group_xml = escape(str(item_group))
    uom_xml = escape(str(uom))

    item_xml = f"""
<ENVELOPE>
<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>
<DESC>
<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>
</DESC>

<DATA>
<TALLYMESSAGE xmlns:UDF="TallyUDF">

<STOCKITEM NAME="{item_xml_name}" ACTION="Create">
<NAME>{item_xml_name}</NAME>
<PARENT>ERPNext Items</PARENT>
<BASEUNITS>{uom_xml}</BASEUNITS>
</STOCKITEM>

</TALLYMESSAGE>
</DATA>
</BODY>
</ENVELOPE>
"""

    return send_to_tally(
        item_xml,
        f"ITEM - {item_name}"
    )

def item_after_insert(doc, method=None):

    item_name = doc.name
    item_group = doc.item_group or "ERPNext Items"
    uom = doc.stock_uom or "Nos"

    company_name = "ABC Parent Pvt Ltd"

    print(
        f"AUTO ITEM SYNC: {item_name} -> {company_name}"
    )

    return create_tally_item(
        item_name,
        company_name,
        item_group,
        uom
    )


def item_after_update(doc, method=None):

    item_name = doc.name
    item_group = doc.item_group or "ERPNext Items"
    uom = doc.stock_uom or "Nos"

    company_name = "ABC Parent Pvt Ltd"

    print(
        f"AUTO ITEM UPDATE: {item_name} -> {company_name}"
    )

    return create_tally_item(
        item_name,
        company_name,
        item_group,
        uom
    )

def create_tally_unit(unit_name, symbol, company_name):

    unit_xml_name = escape(str(unit_name))
    unit_xml_symbol = escape(str(symbol or unit_name))
    company_xml = escape(str(company_name))

    unit_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<UNIT NAME="{unit_xml_symbol}" ACTION="Create">

<NAME>{unit_xml_symbol}</NAME>

<ISSIMPLEUNIT>Yes</ISSIMPLEUNIT>

<ORIGINALNAME>{unit_xml_name}</ORIGINALNAME>

<DECIMALPLACES>0</DECIMALPLACES>

</UNIT>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    return send_to_tally(
        unit_xml,
        f"UNIT - {unit_name}"
    )

def create_tally_stock_group(group_name, company_name, parent_group="ERPNext Items"):

    group_xml_name = escape(str(group_name))
    company_xml = escape(str(company_name))
    parent_xml = escape(str(parent_group))

    stock_group_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<STOCKGROUP NAME="{group_xml_name}" ACTION="Create">

<NAME>{group_xml_name}</NAME>

<PARENT>{parent_xml}</PARENT>

</STOCKGROUP>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    return send_to_tally(
        stock_group_xml,
        f"STOCK GROUP - {group_name}"
    )

def item_group_after_insert(doc, method=None):

    # Root group Tally मध्ये manually mapped आहे
    if doc.name == "All Item Groups":
        print(
            f"AUTO ITEM GROUP SYNC SKIPPED: "
            f"{doc.name} - Root Group"
        )
        return

    group_name = doc.name
    company_name = "ABC Parent Pvt Ltd"

    # ERPNext root -> Tally ERPNext Items
    if doc.parent_item_group == "All Item Groups":
        parent_group = "ERPNext Items"
    else:
        parent_group = doc.parent_item_group or "ERPNext Items"

    print(
        f"AUTO ITEM GROUP SYNC: "
        f"{group_name} -> {company_name} -> {parent_group}"
    )

    return create_tally_stock_group(
        group_name,
        company_name,
        parent_group
    )


def item_group_after_update(doc, method=None):

    if doc.name == "All Item Groups":
        print(
            f"AUTO ITEM GROUP UPDATE SKIPPED: "
            f"{doc.name} - Root Group"
        )
        return

    group_name = doc.name
    company_name = "ABC Parent Pvt Ltd"

    if doc.parent_item_group == "All Item Groups":
        parent_group = "ERPNext Items"
    else:
        parent_group = doc.parent_item_group or "ERPNext Items"

    print(
        f"AUTO ITEM GROUP UPDATE: "
        f"{group_name} -> {company_name} -> {parent_group}"
    )

    # create_tally_stock_group uses Create.
    # For update we need Alter, so send direct XML.

    group_xml_name = escape(str(group_name))
    company_xml = escape(str(company_name))
    parent_xml = escape(str(parent_group))

    stock_group_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<STOCKGROUP NAME="{group_xml_name}" ACTION="Alter">

<NAME>{group_xml_name}</NAME>

<PARENT>{parent_xml}</PARENT>

</STOCKGROUP>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    return send_to_tally(
        stock_group_xml,
        f"UPDATE STOCK GROUP - {group_name}"
    )


def item_group_on_trash(doc, method=None):

    if doc.name == "All Item Groups":
        print(
            f"AUTO ITEM GROUP DELETE SKIPPED: "
            f"{doc.name} - Root Group"
        )
        return

    group_name = escape(str(doc.name))
    company_name = escape("ABC Parent Pvt Ltd")

    delete_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<STOCKGROUP NAME="{group_name}" ACTION="Delete">

<NAME>{group_name}</NAME>

</STOCKGROUP>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    print(
        f"AUTO ITEM GROUP DELETE: "
        f"{doc.name} -> ABC Parent Pvt Ltd"
    )

    return send_to_tally(
        delete_xml,
        f"DELETE STOCK GROUP - {doc.name}"
    )



def create_tally_stock_item(item_name, company_name, item_group="ERPNext Items", uom="Nos"):

    item_xml_name = escape(str(item_name))
    company_xml = escape(str(company_name))
    group_xml = escape(str(item_group))
    uom_xml = escape(str(uom))

    stock_item_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<STOCKITEM NAME="{item_xml_name}" ACTION="Create">

<NAME>{item_xml_name}</NAME>

<PARENT>{group_xml}</PARENT>

<BASEUNITS>{uom_xml}</BASEUNITS>

</STOCKITEM>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    return send_to_tally(
        stock_item_xml,
        f"STOCK ITEM - {item_name}"
    )

# =========================================================
# CHECK TALLY RESPONSE
# =========================================================

def tally_response_success(response):

    if not response:
        return False

    if (
        "<ERRORS>0</ERRORS>" in response
        and "<EXCEPTIONS>0</EXCEPTIONS>" in response
        and "<LINEERROR>" not in response
    ):
        return True

    return False


# =========================================================
# SEND SALES INVOICE TO TALLY
# =========================================================

@frappe.whitelist()
def send_sales_invoice_to_tally(invoice_name):

    invoice = frappe.get_doc(
        "Sales Invoice",
        invoice_name
    )

    company_name = invoice.company
    customer_name = invoice.customer

    # =====================================================
    # DATE
    # =====================================================

    posting_date = getdate(
        invoice.posting_date
    )

    tally_date = posting_date.strftime(
        "%Y%m%d"
    )


    voucher_number = invoice.name

    if invoice.custom_tally_voucher_no:
        voucher_number = invoice.custom_tally_voucher_no

    if invoice.custom_tally_voucher_no:
        return {
            "success": True,
            "invoice": invoice_name,
            "message": "Already synced to Tally",
            "tally_voucher_no": invoice.custom_tally_voucher_no
        }

    # =====================================================
    # AMOUNTS
    # =====================================================

    sales_amount = float(
        invoice.net_total or 0
    )

    tax_amount = float(
        invoice.total_taxes_and_charges or 0
    )

    total_amount = float(
        invoice.grand_total or 0
    )

    # =====================================================
    # TALLY LEDGER NAMES
    # =====================================================

    sales_ledger = "Goods Sales"
    tax_ledger = "Output Tax"

    # =====================================================
    # XML ESCAPE
    # =====================================================

    company_xml = escape(
        str(company_name)
    )

    customer_xml_name = escape(
        str(customer_name)
    )

    sales_ledger_xml = escape(
        str(sales_ledger)
    )

    tax_ledger_xml = escape(
        str(tax_ledger)
    )

    voucher_number_xml = escape(
        str(voucher_number)
    )

    # =====================================================
    # LOG
    # =====================================================

    print("\n========================================")
    print("AUTO TALLY SYNC")
    print("ACTION          : CREATE")
    print("TALLY URL       :", TALLY_URL)
    print("ERP INVOICE     :", invoice_name)
    print("ERP DATE        :", invoice.posting_date)
    print("TALLY DATE      :", tally_date)
    print("CUSTOMER        :", customer_name)
    print("COMPANY         :", company_name)
    print("SALES AMOUNT    :", sales_amount)
    print("TAX AMOUNT      :", tax_amount)
    print("TOTAL AMOUNT    :", total_amount)
    print("========================================")

    # =====================================================
    # 1. CUSTOMER LEDGER
    # =====================================================

    customer_master_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<LEDGER NAME="{customer_xml_name}" ACTION="Create">

<NAME>{customer_xml_name}</NAME>
<PARENT>Sundry Debtors</PARENT>
<ISBILLWISEON>Yes</ISBILLWISEON>
<AFFECTSSTOCK>No</AFFECTSSTOCK>

</LEDGER>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    send_to_tally(
        customer_master_xml,
        "CUSTOMER LEDGER"
    )

    # =====================================================
    # 2. STOCK GROUP
    # =====================================================

    stock_group_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<STOCKGROUP NAME="ERPNext Items" ACTION="Create">

<NAME>ERPNext Items</NAME>
<PARENT></PARENT>

</STOCKGROUP>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    send_to_tally(
        stock_group_xml,
        "STOCK GROUP"
    )

    # =====================================================
    # 3. UNIT
    # =====================================================

    unit_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<UNIT NAME="Nos" ACTION="Create">

<NAME>Nos</NAME>
<ISSIMPLEUNIT>Yes</ISSIMPLEUNIT>
<DECIMALPLACES>0</DECIMALPLACES>

</UNIT>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    send_to_tally(
        unit_xml,
        "UNIT"
    )

    # =====================================================
    # 4. SALES LEDGER
    # =====================================================

    sales_ledger_master_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<LEDGER NAME="{sales_ledger_xml}" ACTION="Create">

<NAME>{sales_ledger_xml}</NAME>
<PARENT>Sales Accounts</PARENT>
<AFFECTSSTOCK>Yes</AFFECTSSTOCK>

</LEDGER>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    send_to_tally(
        sales_ledger_master_xml,
        "SALES LEDGER"
    )

    # =====================================================
    # 5. TAX LEDGER
    # =====================================================

    tax_ledger_master_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<LEDGER NAME="{tax_ledger_xml}" ACTION="Create">

<NAME>{tax_ledger_xml}</NAME>
<PARENT>Duties &amp; Taxes</PARENT>
<AFFECTSSTOCK>No</AFFECTSSTOCK>

</LEDGER>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    send_to_tally(
        tax_ledger_master_xml,
        "TAX LEDGER"
    )

    # =====================================================
    # 6. STOCK ITEMS + INVENTORY ENTRIES
    # =====================================================

    inventory_entries = ""

    for item in invoice.items:

        item_name = str(
            item.item_code
        )

        uom = str(
            item.uom or item.stock_uom or "Nos"
        )

        uom_xml = escape(
            uom
        )

        item_name_xml = escape(
            item_name
        )

        qty = float(
            item.qty or 0
        )

        rate = float(
            item.rate or 0
        )

        amount = float(
            item.amount or 0
        )

        # =================================================
        # STOCK ITEM
        # =================================================


        stock_item_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<STOCKITEM NAME="{item_name_xml}" ACTION="Create">

<NAME>{item_name_xml}</NAME>
<PARENT>ERPNext Items</PARENT>
<BASEUNITS>{uom_xml}</BASEUNITS>

</STOCKITEM>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

        send_to_tally(
            stock_item_xml,
            "STOCK ITEM"
        )

        # =================================================
        # INVENTORY ENTRY
        # =================================================

        inventory_entries += f"""
<ALLINVENTORYENTRIES.LIST>

<STOCKITEMNAME>{item_name_xml}</STOCKITEMNAME>

<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>

<RATE>{rate:.2f}/Nos</RATE>

<DISCOUNT>0</DISCOUNT>

<AMOUNT>{amount:.2f}</AMOUNT>

<ACTUALQTY>{qty:g} Nos</ACTUALQTY>

<BILLEDQTY>{qty:g} Nos</BILLEDQTY>

<BATCHALLOCATIONS.LIST>

<GODOWNNAME>Main Location</GODOWNNAME>

<BATCHNAME>Primary Batch</BATCHNAME>

<DESTINATIONGODOWNNAME>Main Location</DESTINATIONGODOWNNAME>

<AMOUNT>{amount:.2f}</AMOUNT>

<ACTUALQTY>{qty:g} Nos</ACTUALQTY>

<BILLEDQTY>{qty:g} Nos</BILLEDQTY>

</BATCHALLOCATIONS.LIST>

<ACCOUNTINGALLOCATIONS.LIST>

<LEDGERNAME>{sales_ledger_xml}</LEDGERNAME>

<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>

<AMOUNT>{amount:.2f}</AMOUNT>

</ACCOUNTINGALLOCATIONS.LIST>

</ALLINVENTORYENTRIES.LIST>
"""

    # =====================================================
    # 7. SALES VOUCHER
    # =====================================================

    voucher_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>Vouchers</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>

<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>

</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<VOUCHER
VCHTYPE="Sales"
ACTION="Create"
OBJVIEW="Invoice Voucher View">

<DATE>{tally_date}</DATE>

<VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>

<VOUCHERNUMBER>{voucher_number_xml}</VOUCHERNUMBER>

<PERSISTEDVIEW>Invoice Voucher View</PERSISTEDVIEW>

<VCHENTRYMODE>Item Invoice</VCHENTRYMODE>

<ISINVOICE>Yes</ISINVOICE>

<LEDGERENTRIES.LIST>

<LEDGERNAME>{customer_xml_name}</LEDGERNAME>

<ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>

<ISPARTYLEDGER>Yes</ISPARTYLEDGER>

<ISLASTDEEMEDPOSITIVE>Yes</ISLASTDEEMEDPOSITIVE>

<AMOUNT>-{total_amount:.2f}</AMOUNT>

<BILLALLOCATIONS.LIST>

<NAME>{invoice.name}</NAME>

<BILLTYPE>New Ref</BILLTYPE>

<AMOUNT>-{total_amount:.2f}</AMOUNT>

</BILLALLOCATIONS.LIST>

</LEDGERENTRIES.LIST>


{f'''
<LEDGERENTRIES.LIST>
<LEDGERNAME>{tax_ledger_xml}</LEDGERNAME>
<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
<AMOUNT>{tax_amount:.2f}</AMOUNT>
</LEDGERENTRIES.LIST>
''' if tax_amount > 0 else ''}
{inventory_entries}

</VOUCHER>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    # =====================================================
    # PRINT XML
    # =====================================================

    print("\n=========================================================")
    print("              ACTUAL TALLY SALES XML")
    print("=========================================================")

    print(voucher_xml)

    print("=========================================================")

    # =====================================================
    # SEND SALES VOUCHER
    # =====================================================

    response = send_to_tally(
        voucher_xml,
        "SALES VOUCHER"
    )

    success = tally_response_success(
        response
    )

    if success:
        import re

        tally_voucher_no = None

        match = re.search(
            r"<VCHNUMBER>\s*(.*?)\s*</VCHNUMBER>",
            response or "",
            re.IGNORECASE
        )

        if match:
            candidate = match.group(1).strip()

            if candidate and candidate != invoice.name:
                tally_voucher_no = candidate

        if success:
            invoice.db_set(
                "custom_tally_voucher_no",
                voucher_number
            )

            print(
                "TALLY VOUCHER NUMBER SAVED:",
                voucher_number
            )
            
        else:
            print(
                "WARNING: Tally voucher created, "
                "but actual voucher number was not returned."
            )

    # =====================================================
    # RESULT
    # =====================================================

    print("\n========================================")
    print("AUTO TALLY SYNC RESULT:", success)
    print("ERP INVOICE:", invoice_name)
    print("========================================")

    return {
        "success": success,
        "invoice": invoice_name,
        "erp_date": str(invoice.posting_date),
        "tally_date": tally_date,
        "voucher_number": voucher_number,
        "customer": customer_name,
        "sales_amount": sales_amount,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "tally_response": response
    }


# =========================================================
# AUTOMATIC SALES INVOICE SUBMIT TRIGGER
# =========================================================

def sales_invoice_on_submit(doc, method=None):

    print("\n========================================")
    print("AUTO TALLY SYNC TRIGGERED")
    print("ACTION: CREATE")
    print("Sales Invoice:", doc.name)
    print("========================================")

    return send_sales_invoice_to_tally(
        doc.name
    )

@frappe.whitelist()
def cancel_sales_invoice_in_tally(invoice_name):

    invoice = frappe.get_doc(
        "Sales Invoice",
        invoice_name
    )

    company_name = invoice.company

    posting_date = getdate(
        invoice.posting_date
    )

    tally_date = posting_date.strftime(
        "%Y%m%d"
    )

    # ERPNext stores the ERP invoice reference.
    # Tally voucher number must be resolved separately.
    voucher_number = invoice.custom_tally_voucher_no or invoice.name

    company_xml = escape(
        str(company_name)
    )

    voucher_number_xml = escape(
        str(voucher_number)
    )

    print("\n========================================")
    print("AUTO TALLY CANCEL SYNC")
    print("ACTION          : CANCEL")
    print("TALLY URL       :", TALLY_URL)
    print("ERP INVOICE     :", invoice_name)
    print("ERP DATE        :", invoice.posting_date)
    print("TALLY DATE      :", tally_date)
    print("COMPANY         :", company_name)
    print("REFERENCE       :", voucher_number)
    print("========================================")

    # =====================================================
    # IMPORTANT:
    # Tally cancellation needs an identifier.
    #
    # We identify the existing voucher using:
    # Date + Reference + Voucher Type
    #
    # The TAGNAME/TAGVALUE is placed on VOUCHER itself.
    # This prevents Tally from treating the request as
    # a brand-new voucher.
    # =====================================================

    cancel_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>Vouchers</ID>
</HEADER>

<BODY>

<DESC>
</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<VOUCHER
DATE="{tally_date}"
TAGNAME="Voucher Number"
TAGVALUE="{voucher_number_xml}"
VCHTYPE="Sales"
ACTION="Cancel">

<DATE>{tally_date}</DATE>

<VOUCHERTYPENAME>Sales</VOUCHERTYPENAME>

<VOUCHERNUMBER>{voucher_number_xml}</VOUCHERNUMBER>

<REFERENCE>{invoice.name}</REFERENCE>

</VOUCHER>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    print("\n=========================================================")
    print("              ACTUAL TALLY CANCEL XML")
    print("=========================================================")

    print(cancel_xml)

    print("=========================================================")

    response = send_to_tally(
        cancel_xml,
        "CANCEL SALES VOUCHER"
    )

    success = tally_response_success(
        response
    )

    print("\n========================================")
    print("AUTO TALLY CANCEL RESULT:", success)
    print("ERP INVOICE:", invoice_name)
    print("========================================")

    return {
        "success": success,
        "invoice": invoice_name,
        "erp_date": str(invoice.posting_date),
        "tally_date": tally_date,
        "voucher_number": voucher_number,
        "company": company_name,
        "tally_response": response
    }


# =========================================================
# AUTOMATIC SALES INVOICE CANCEL TRIGGER
# =========================================================

def sales_invoice_on_cancel(doc, method=None):

    print("\n========================================")
    print("AUTO TALLY SYNC TRIGGERED")
    print("ACTION: CANCEL")
    print("Sales Invoice:", doc.name)
    print("========================================")

    return cancel_sales_invoice_in_tally(
        doc.name
    )


# =========================================================
# DELETE SALES INVOICE IN TALLY
# =========================================================

@frappe.whitelist()
def delete_sales_invoice_in_tally(invoice_name):

    invoice = frappe.get_doc(
        "Sales Invoice",
        invoice_name
    )

    company_name = invoice.company

    posting_date = getdate(
        invoice.posting_date
    )

    tally_date = posting_date.strftime(
        "%Y%m%d"
    )

    voucher_number = invoice.custom_tally_voucher_no or invoice.name
    
    # =====================================================
    # XML ESCAPE
    # =====================================================

    company_xml = escape(
        str(company_name)
    )

    voucher_number_xml = escape(
        str(voucher_number)
    )

    # =====================================================
    # LOG
    # =====================================================

    print("\n========================================")
    print("AUTO TALLY DELETE SYNC")
    print("ACTION          : DELETE")
    print("TALLY URL       :", TALLY_URL)
    print("ERP INVOICE     :", invoice_name)
    print("ERP DATE        :", invoice.posting_date)
    print("TALLY DATE      :", tally_date)
    print("COMPANY         :", company_name)
    print("VOUCHER NUMBER  :", voucher_number)
    print("========================================")

    # =====================================================
    # TALLY DELETE VOUCHER XML
    # =====================================================

    delete_xml = f"""
<ENVELOPE>

<HEADER>

<VERSION>1</VERSION>

<TALLYREQUEST>Import</TALLYREQUEST>

<TYPE>Data</TYPE>

<ID>Vouchers</ID>

</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>

<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>

<SVFROMDATE>{tally_date}</SVFROMDATE>

<SVTODATE>{tally_date}</SVTODATE>

</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<VOUCHER

DATE="{tally_date}"

TAGNAME="Voucher Number"

TAGVALUE="{voucher_number_xml}"

VCHTYPE="Sales"

ACTION="Delete">

</VOUCHER>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    # =====================================================
    # PRINT DELETE XML
    # =====================================================

    print("\n=========================================================")
    print("              ACTUAL TALLY DELETE XML")
    print("=========================================================")

    print(delete_xml)

    print("=========================================================")

    # =====================================================
    # SEND DELETE
    # =====================================================

    response = send_to_tally(
        delete_xml,
        "DELETE SALES VOUCHER"
    )

    success = tally_response_success(
        response
    )

    # =====================================================
    # RESULT
    # =====================================================

    print("\n========================================")
    print("AUTO TALLY DELETE RESULT:", success)
    print("ERP INVOICE:", invoice_name)
    print("========================================")

    return {
        "success": success,
        "invoice": invoice_name,
        "erp_date": str(invoice.posting_date),
        "tally_date": tally_date,
        "voucher_number": voucher_number,
        "company": company_name,
        "tally_response": response
    }


# =========================================================
# AUTOMATIC SALES INVOICE DELETE TRIGGER
# =========================================================

def sales_invoice_on_trash(doc, method=None):

    print("\n========================================")
    print("AUTO TALLY SYNC TRIGGERED")
    print("ACTION: DELETE")
    print("Sales Invoice:", doc.name)
    print("========================================")

    return delete_sales_invoice_in_tally(
        doc.name
    )

# =========================================================
# SEND PURCHASE INVOICE TO TALLY
# =========================================================

@frappe.whitelist()
def send_purchase_invoice_to_tally(invoice_name):

    invoice = frappe.get_doc(
        "Purchase Invoice",
        invoice_name
    )

    company_name = invoice.company
    supplier_name = invoice.supplier

    # =====================================================
    # DATE
    # =====================================================

    posting_date = getdate(
        invoice.posting_date
    )

    tally_date = posting_date.strftime(
        "%Y%m%d"
    )

    voucher_number = invoice.name

    if invoice.custom_tally_voucher_no:
        return {
            "success": True,
            "invoice": invoice_name,
            "message": "Already synced to Tally",
            "tally_voucher_no": invoice.custom_tally_voucher_no
        }

    # =====================================================
    # AMOUNTS
    # =====================================================

    purchase_amount = float(
        invoice.net_total or 0
    )

    tax_amount = float(
        invoice.total_taxes_and_charges or 0
    )

    total_amount = float(
        invoice.grand_total or 0
    )

    # =====================================================
    # TALLY LEDGER NAMES
    # =====================================================

    purchase_ledger = "Goods Purchase"

    tax_ledgers = []

    for tax in invoice.taxes:
        if tax.account_head and tax.tax_amount:
            tax_ledgers.append({
                "account_head": str(tax.account_head),
                "tax_amount": float(tax.tax_amount or 0)
            })

    if not tax_ledgers:
        tax_ledgers = [
            {
                "account_head": "Input Tax",
                "tax_amount": tax_amount
            }
        ]

    # =====================================================
    # XML ESCAPE
    # =====================================================

    company_xml = escape(
        str(company_name)
    )

    supplier_xml_name = escape(
        str(supplier_name)
    )

    purchase_ledger_xml = escape(
        str(purchase_ledger)
    )

    tax_ledger_xml = None

    voucher_number_xml = escape(
        str(voucher_number)
    )

    # =====================================================
    # LOG
    # =====================================================

    print("\n========================================")
    print("AUTO TALLY PURCHASE SYNC")
    print("ACTION          : CREATE")
    print("TALLY URL       :", TALLY_URL)
    print("ERP INVOICE     :", invoice_name)
    print("ERP DATE        :", invoice.posting_date)
    print("TALLY DATE      :", tally_date)
    print("SUPPLIER        :", supplier_name)
    print("COMPANY         :", company_name)
    print("PURCHASE AMOUNT :", purchase_amount)
    print("TAX AMOUNT      :", tax_amount)
    print("TOTAL AMOUNT    :", total_amount)
    print("========================================")

    # =====================================================
    # 1. SUPPLIER LEDGER
    # =====================================================

    supplier_master_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<LEDGER NAME="{supplier_xml_name}" ACTION="Create">

<NAME>{supplier_xml_name}</NAME>
<PARENT>Sundry Creditors</PARENT>
<ISBILLWISEON>Yes</ISBILLWISEON>
<AFFECTSSTOCK>No</AFFECTSSTOCK>

</LEDGER>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    send_to_tally(
        supplier_master_xml,
        "SUPPLIER LEDGER"
    )

    # =====================================================
    # 2. STOCK GROUP
    # =====================================================

    stock_group_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<STOCKGROUP NAME="ERPNext Items" ACTION="Create">

<NAME>ERPNext Items</NAME>
<PARENT></PARENT>

</STOCKGROUP>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    send_to_tally(
        stock_group_xml,
        "PURCHASE STOCK GROUP"
    )

    # =====================================================
    # 3. UNIT
    # =====================================================

    unit_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<UNIT NAME="Nos" ACTION="Create">

<NAME>Nos</NAME>
<ISSIMPLEUNIT>Yes</ISSIMPLEUNIT>
<DECIMALPLACES>0</DECIMALPLACES>

</UNIT>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    send_to_tally(
        unit_xml,
        "PURCHASE UNIT"
    )

    # =====================================================
    # 4. PURCHASE LEDGER
    # =====================================================

    purchase_ledger_master_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<LEDGER NAME="{purchase_ledger_xml}" ACTION="Create">

<NAME>{purchase_ledger_xml}</NAME>
<PARENT>Purchase Accounts</PARENT>
<AFFECTSSTOCK>Yes</AFFECTSSTOCK>

</LEDGER>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    send_to_tally(
        purchase_ledger_master_xml,
        "PURCHASE LEDGER"
    )

        # =====================================================
    # 5. TAX LEDGERS
    # =====================================================

    for tax_info in tax_ledgers:

        tax_account = tax_info["account_head"]
        tax_account_xml = escape(tax_account)

        tax_ledger_master_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<LEDGER NAME="{tax_account_xml}" ACTION="Create">

<NAME>{tax_account_xml}</NAME>
<PARENT>Duties &amp; Taxes</PARENT>
<AFFECTSSTOCK>No</AFFECTSSTOCK>

</LEDGER>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

        send_to_tally(
            tax_ledger_master_xml,
            "PURCHASE TAX LEDGER"
        )

    # =====================================================
    # 6. STOCK ITEMS + INVENTORY ENTRIES
    # =====================================================

    inventory_entries = ""

    for item in invoice.items:

        item_name = str(
            item.item_code
        )

        uom = str(
            item.uom or item.stock_uom or "Nos"
        )

        uom_xml = escape(
            uom
        )

        item_name_xml = escape(
            item_name
        )

        qty = float(
            item.qty or 0
        )

        rate = float(
            item.rate or 0
        )

        amount = float(
            item.amount or 0
        )

        # =================================================
        # STOCK ITEM
        # =================================================

        stock_item_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<STOCKITEM NAME="{item_name_xml}" ACTION="Create">

<NAME>{item_name_xml}</NAME>
<PARENT>ERPNext Items</PARENT>
<BASEUNITS>{uom_xml}</BASEUNITS>

</STOCKITEM>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

        send_to_tally(
            stock_item_xml,
            "PURCHASE STOCK ITEM"
        )

        # =================================================
        # INVENTORY ENTRY
        # =================================================

        inventory_entries += f"""
<ALLINVENTORYENTRIES.LIST>

<STOCKITEMNAME>{item_name_xml}</STOCKITEMNAME>

<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>

<RATE>{rate:.2f}/Nos</RATE>

<AMOUNT>{amount:.2f}</AMOUNT>

<ACTUALQTY>{qty:g} Nos</ACTUALQTY>

<BILLEDQTY>{qty:g} Nos</BILLEDQTY>

<BATCHALLOCATIONS.LIST>

<GODOWNNAME>Main Location</GODOWNNAME>

<BATCHNAME>Primary Batch</BATCHNAME>

<DESTINATIONGODOWNNAME>Main Location</DESTINATIONGODOWNNAME>

<AMOUNT>{amount:.2f}</AMOUNT>

<ACTUALQTY>{qty:g} Nos</ACTUALQTY>

<BILLEDQTY>{qty:g} Nos</BILLEDQTY>

</BATCHALLOCATIONS.LIST>

<ACCOUNTINGALLOCATIONS.LIST>

<LEDGERNAME>{purchase_ledger_xml}</LEDGERNAME>

<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>

<AMOUNT>{amount:.2f}</AMOUNT>

</ACCOUNTINGALLOCATIONS.LIST>

</ALLINVENTORYENTRIES.LIST>
"""
    tax_ledger_entries = ""

    for tax_info in tax_ledgers:
        tax_account_xml = escape(
            str(tax_info["account_head"])
        )

        tax_amount_value = float(
            tax_info["tax_amount"] or 0
        )

        if tax_amount_value > 0:
            tax_ledger_entries += f"""
<LEDGERENTRIES.LIST>
<LEDGERNAME>{tax_account_xml}</LEDGERNAME>
<ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
<AMOUNT>-{tax_amount_value:.2f}</AMOUNT>
</LEDGERENTRIES.LIST>
"""

    # =====================================================
    # 7. PURCHASE VOUCHER
    # =====================================================

    voucher_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>Vouchers</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>

<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>

</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<VOUCHER
VCHTYPE="Purchase"
ACTION="Create"
OBJVIEW="Accounting Voucher View">

<DATE>{tally_date}</DATE>

<VOUCHERTYPENAME>Purchase</VOUCHERTYPENAME>

<VOUCHERNUMBER>{voucher_number_xml}</VOUCHERNUMBER>

<PERSISTEDVIEW>Accounting Voucher View</PERSISTEDVIEW>

<ISINVOICE>No</ISINVOICE>

<LEDGERENTRIES.LIST>

<LEDGERNAME>{supplier_xml_name}</LEDGERNAME>

<ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>

<ISPARTYLEDGER>Yes</ISPARTYLEDGER>

<ISLASTDEEMEDPOSITIVE>No</ISLASTDEEMEDPOSITIVE>

<AMOUNT>{total_amount:.2f}</AMOUNT>

</LEDGERENTRIES.LIST>

<LEDGERENTRIES.LIST>

<LEDGERNAME>{purchase_ledger_xml}</LEDGERNAME>

<ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>

<AMOUNT>-{purchase_amount:.2f}</AMOUNT>

</LEDGERENTRIES.LIST>

{tax_ledger_entries}

</VOUCHER>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    # =====================================================
    # PRINT XML
    # =====================================================

    print("\n=========================================================")
    print("              ACTUAL TALLY PURCHASE XML")
    print("=========================================================")

    print(voucher_xml)

    print("=========================================================")

    # =====================================================
    # SEND PURCHASE VOUCHER
    # =====================================================

    response = send_to_tally(
        voucher_xml,
        "PURCHASE VOUCHER"
    )

    success = tally_response_success(
        response
    )

    # =====================================================
    # SAVE TALLY VOUCHER NUMBER
    # =====================================================

    if success:

        import re

        tally_voucher_no = voucher_number

        match = re.search(
            r"<VCHNUMBER>(.*?)</VCHNUMBER>",
            response or ""
        )

        if match:
            tally_voucher_no = match.group(1).strip()

        invoice.db_set(
            "custom_tally_voucher_no",
            tally_voucher_no
        )

        print(
            "TALLY VOUCHER NUMBER SAVED:",
            tally_voucher_no
        )

    # =====================================================
    # RESULT
    # =====================================================

    print("\n========================================")
    print("AUTO TALLY PURCHASE RESULT:", success)
    print("ERP INVOICE:", invoice_name)
    print("========================================")

    return {
        "success": success,
        "invoice": invoice_name,
        "erp_date": str(invoice.posting_date),
        "tally_date": tally_date,
        "voucher_number": voucher_number,
        "supplier": supplier_name,
        "purchase_amount": purchase_amount,
        "tax_amount": tax_amount,
        "total_amount": total_amount,
        "tally_response": response
    }


# =========================================================
# AUTOMATIC PURCHASE INVOICE SUBMIT TRIGGER
# =========================================================

def purchase_invoice_on_submit(doc, method=None):

    print("\n========================================")
    print("AUTO TALLY SYNC TRIGGERED")
    print("ACTION: CREATE")
    print("Purchase Invoice:", doc.name)
    print("========================================")

    return send_purchase_invoice_to_tally(
        doc.name
    )
    
# =========================================================
# CANCEL PURCHASE INVOICE IN TALLY
# =========================================================

@frappe.whitelist()
def cancel_purchase_invoice_in_tally(invoice_name):

    invoice = frappe.get_doc(
        "Purchase Invoice",
        invoice_name
    )

    company_name = invoice.company

    posting_date = getdate(
        invoice.posting_date
    )

    tally_date = posting_date.strftime(
        "%Y%m%d"
    )

    voucher_number = (
        invoice.custom_tally_voucher_no
        or invoice.name
    )

    company_xml = escape(
        str(company_name)
    )

    voucher_number_xml = escape(
        str(voucher_number)
    )

    print("\n========================================")
    print("AUTO TALLY PURCHASE CANCEL")
    print("ACTION          : CANCEL")
    print("TALLY URL       :", TALLY_URL)
    print("ERP INVOICE     :", invoice_name)
    print("ERP DATE        :", invoice.posting_date)
    print("TALLY DATE      :", tally_date)
    print("COMPANY         :", company_name)
    print("VOUCHER NUMBER  :", voucher_number)
    print("========================================")

    cancel_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>Vouchers</ID>
</HEADER>

<BODY>

<DESC>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<VOUCHER
DATE="{tally_date}"
TAGNAME="Voucher Number"
TAGVALUE="{voucher_number_xml}"
VCHTYPE="Purchase"
ACTION="Cancel">

<DATE>{tally_date}</DATE>

<VOUCHERTYPENAME>Purchase</VOUCHERTYPENAME>

<VOUCHERNUMBER>{voucher_number_xml}</VOUCHERNUMBER>

<REFERENCE>{invoice.name}</REFERENCE>

</VOUCHER>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    print("\n=========================================================")
    print("              ACTUAL TALLY PURCHASE CANCEL XML")
    print("=========================================================")

    print(cancel_xml)

    print("=========================================================")

    response = send_to_tally(
        cancel_xml,
        "CANCEL PURCHASE VOUCHER"
    )

    success = tally_response_success(
        response
    )

    print("\n========================================")
    print("AUTO TALLY PURCHASE CANCEL RESULT:", success)
    print("ERP INVOICE:", invoice_name)
    print("========================================")

    return {
        "success": success,
        "invoice": invoice_name,
        "erp_date": str(invoice.posting_date),
        "tally_date": tally_date,
        "voucher_number": voucher_number,
        "company": company_name,
        "tally_response": response
    }


# =========================================================
# AUTOMATIC PURCHASE INVOICE CANCEL TRIGGER
# =========================================================

def purchase_invoice_on_cancel(doc, method=None):

    print("\n========================================")
    print("AUTO TALLY SYNC TRIGGERED")
    print("ACTION: CANCEL")
    print("Purchase Invoice:", doc.name)
    print("========================================")

    return cancel_purchase_invoice_in_tally(
        doc.name
    )


# =========================================================
# DELETE PURCHASE INVOICE IN TALLY
# =========================================================

@frappe.whitelist()
def delete_purchase_invoice_in_tally(invoice_name):

    invoice = frappe.get_doc(
        "Purchase Invoice",
        invoice_name
    )

    company_name = invoice.company

    posting_date = getdate(
        invoice.posting_date
    )

    tally_date = posting_date.strftime(
        "%Y%m%d"
    )

    voucher_number = (
        invoice.custom_tally_voucher_no
        or invoice.name
    )

    company_xml = escape(
        str(company_name)
    )

    voucher_number_xml = escape(
        str(voucher_number)
    )

    print("\n========================================")
    print("AUTO TALLY PURCHASE DELETE")
    print("ACTION          : DELETE")
    print("TALLY URL       :", TALLY_URL)
    print("ERP INVOICE     :", invoice_name)
    print("ERP DATE        :", invoice.posting_date)
    print("TALLY DATE      :", tally_date)
    print("COMPANY         :", company_name)
    print("VOUCHER NUMBER  :", voucher_number)
    print("========================================")

    delete_xml = f"""
<ENVELOPE>

<HEADER>

<VERSION>1</VERSION>

<TALLYREQUEST>Import</TALLYREQUEST>

<TYPE>Data</TYPE>

<ID>Vouchers</ID>

</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>

<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>

<SVFROMDATE>{tally_date}</SVFROMDATE>

<SVTODATE>{tally_date}</SVTODATE>

</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<VOUCHER

DATE="{tally_date}"

TAGNAME="Voucher Number"

TAGVALUE="{voucher_number_xml}"

VCHTYPE="Purchase"

ACTION="Delete">

</VOUCHER>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    print("\n=========================================================")
    print("              ACTUAL TALLY PURCHASE DELETE XML")
    print("=========================================================")

    print(delete_xml)

    print("=========================================================")

    response = send_to_tally(
        delete_xml,
        "DELETE PURCHASE VOUCHER"
    )

    success = tally_response_success(
        response
    )

    print("\n========================================")
    print("AUTO TALLY PURCHASE DELETE RESULT:", success)
    print("ERP INVOICE:", invoice_name)
    print("========================================")

    return {
        "success": success,
        "invoice": invoice_name,
        "erp_date": str(invoice.posting_date),
        "tally_date": tally_date,
        "voucher_number": voucher_number,
        "company": company_name,
        "tally_response": response
    }


# =========================================================
# AUTOMATIC PURCHASE INVOICE DELETE TRIGGER
# =========================================================

def purchase_invoice_on_trash(doc, method=None):

    print("\n========================================")
    print("AUTO TALLY SYNC TRIGGERED")
    print("ACTION: DELETE")
    print("Purchase Invoice:", doc.name)
    print("========================================")

    return delete_purchase_invoice_in_tally(
        doc.name
    )


def send_payment_entry_to_tally(payment_name):
    payment = frappe.get_doc("Payment Entry", payment_name)

    tally_date = getdate(payment.posting_date).strftime("%Y%m%d")
    voucher_number = payment.name
    company_name = payment.company

    paid_amount = float(payment.paid_amount or 0)

    paid_from = payment.paid_from
    paid_to = payment.paid_to
    party = payment.party

    xml = f"""
<ENVELOPE>
    <HEADER>
        <VERSION>1</VERSION>
        <TALLYREQUEST>Import</TALLYREQUEST>
        <TYPE>Data</TYPE>
        <ID>Vouchers</ID>
    </HEADER>
    <BODY>
        <DESC>
            <STATICVARIABLES>
                <SVCURRENTCOMPANY>{escape(company_name)}</SVCURRENTCOMPANY>
            </STATICVARIABLES>
        </DESC>
        <DATA>
            <TALLYMESSAGE>
                <VOUCHER
                    VCHTYPE="Payment"
                    ACTION="Create">

                    <DATE>{tally_date}</DATE>
                    <VOUCHERTYPENAME>Payment</VOUCHERTYPENAME>
                    <VOUCHERNUMBER>{escape(voucher_number)}</VOUCHERNUMBER>
                    <REFERENCE>{escape(voucher_number)}</REFERENCE>

                    <PARTYLEDGERNAME>{escape(party)}</PARTYLEDGERNAME>
                    <PERSISTEDVIEW>Accounting Voucher View</PERSISTEDVIEW>
                    <VCHENTRYMODE>As Voucher</VCHENTRYMODE>

                    <LEDGERENTRIES.LIST>
                        <LEDGERNAME>{escape(paid_to)}</LEDGERNAME>
                        <ISDEEMEDPOSITIVE>No</ISDEEMEDPOSITIVE>
                        <AMOUNT>{paid_amount:.2f}</AMOUNT>
                    </LEDGERENTRIES.LIST>

                    <LEDGERENTRIES.LIST>
                        <LEDGERNAME>{escape(paid_from)}</LEDGERNAME>
                        <ISDEEMEDPOSITIVE>Yes</ISDEEMEDPOSITIVE>
                        <AMOUNT>-{paid_amount:.2f}</AMOUNT>
                    </LEDGERENTRIES.LIST>

                </VOUCHER>
            </TALLYMESSAGE>
        </DATA>
    </BODY>
</ENVELOPE>
"""

    response = send_to_tally(
        xml,
        f"PAYMENT ENTRY CREATE: {payment_name}"
    )

    return response


def payment_entry_on_submit(doc, method=None):
    return send_payment_entry_to_tally(doc.name)

# =========================================================
# CANCEL PAYMENT ENTRY IN TALLY
# =========================================================

@frappe.whitelist()
def cancel_payment_entry_in_tally(payment_name):

    payment = frappe.get_doc(
        "Payment Entry",
        payment_name
    )

    company_name = payment.company

    posting_date = getdate(
        payment.posting_date
    )

    tally_date = posting_date.strftime(
        "%Y%m%d"
    )

    voucher_number = payment.name

    company_xml = escape(
        str(company_name)
    )

    voucher_number_xml = escape(
        str(voucher_number)
    )

    print("\n========================================")
    print("AUTO TALLY PAYMENT CANCEL")
    print("ACTION          : CANCEL")
    print("TALLY URL       :", TALLY_URL)
    print("ERP PAYMENT     :", payment_name)
    print("ERP DATE        :", payment.posting_date)
    print("TALLY DATE      :", tally_date)
    print("COMPANY         :", company_name)
    print("VOUCHER NUMBER  :", voucher_number)
    print("========================================")

    cancel_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>Vouchers</ID>
</HEADER>

<BODY>

<DESC>
<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>
</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<VOUCHER
DATE="{tally_date}"
TAGNAME="Voucher Number"
TAGVALUE="{voucher_number_xml}"
VCHTYPE="Payment"
ACTION="Cancel">

<DATE>{tally_date}</DATE>

<VOUCHERTYPENAME>Payment</VOUCHERTYPENAME>

<VOUCHERNUMBER>{voucher_number_xml}</VOUCHERNUMBER>

</VOUCHER>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    print("\n=========================================================")
    print("              ACTUAL TALLY PAYMENT CANCEL XML")
    print("=========================================================")

    print(cancel_xml)

    print("=========================================================")

    response = send_to_tally(
        cancel_xml,
        "CANCEL PAYMENT VOUCHER"
    )

    success = tally_response_success(
        response
    )

    print("\n========================================")
    print("AUTO TALLY PAYMENT CANCEL RESULT:", success)
    print("ERP PAYMENT:", payment_name)
    print("========================================")

    return {
        "success": success,
        "payment": payment_name,
        "erp_date": str(payment.posting_date),
        "tally_date": tally_date,
        "voucher_number": voucher_number,
        "company": company_name,
        "tally_response": response
    }


# =========================================================
# AUTOMATIC PAYMENT ENTRY CANCEL TRIGGER
# =========================================================

def payment_entry_on_cancel(doc, method=None):

    print("\n========================================")
    print("AUTO TALLY SYNC TRIGGERED")
    print("ACTION: CANCEL")
    print("Payment Entry:", doc.name)
    print("========================================")

    return cancel_payment_entry_in_tally(
        doc.name
    )


# =========================================================
# DELETE PAYMENT ENTRY IN TALLY
# =========================================================

@frappe.whitelist()
def delete_payment_entry_in_tally(payment_name):

    payment = frappe.get_doc(
        "Payment Entry",
        payment_name
    )

    company_name = payment.company

    posting_date = getdate(
        payment.posting_date
    )

    tally_date = posting_date.strftime(
        "%Y%m%d"
    )

    voucher_number = payment.name

    company_xml = escape(
        str(company_name)
    )

    voucher_number_xml = escape(
        str(voucher_number)
    )

    print("\n========================================")
    print("AUTO TALLY PAYMENT DELETE")
    print("ACTION          : DELETE")
    print("TALLY URL       :", TALLY_URL)
    print("ERP PAYMENT     :", payment_name)
    print("ERP DATE        :", payment.posting_date)
    print("TALLY DATE      :", tally_date)
    print("COMPANY         :", company_name)
    print("VOUCHER NUMBER  :", voucher_number)
    print("========================================")

    delete_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>Vouchers</ID>
</HEADER>

<BODY>

<DESC>
<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>
</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<VOUCHER
DATE="{tally_date}"
TAGNAME="Voucher Number"
TAGVALUE="{voucher_number_xml}"
VCHTYPE="Payment"
ACTION="Delete">

<DATE>{tally_date}</DATE>

<VOUCHERTYPENAME>Payment</VOUCHERTYPENAME>

<VOUCHERNUMBER>{voucher_number_xml}</VOUCHERNUMBER>

</VOUCHER>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    print("\n=========================================================")
    print("              ACTUAL TALLY PAYMENT DELETE XML")
    print("=========================================================")

    print(delete_xml)

    print("=========================================================")

    response = send_to_tally(
        delete_xml,
        "DELETE PAYMENT VOUCHER"
    )

    success = tally_response_success(
        response
    )

    print("\n========================================")
    print("AUTO TALLY PAYMENT DELETE RESULT:", success)
    print("ERP PAYMENT:", payment_name)
    print("========================================")

    return {
        "success": success,
        "payment": payment_name,
        "erp_date": str(payment.posting_date),
        "tally_date": tally_date,
        "voucher_number": voucher_number,
        "company": company_name,
        "tally_response": response
    }


# =========================================================
# AUTOMATIC PAYMENT ENTRY DELETE TRIGGER
# =========================================================

def payment_entry_on_trash(doc, method=None):

    print("\n========================================")
    print("AUTO TALLY SYNC TRIGGERED")
    print("ACTION: DELETE")
    print("Payment Entry:", doc.name)
    print("========================================")

    return delete_payment_entry_in_tally(
        doc.name
    )


# =========================================================
# SEND JOURNAL ENTRY TO TALLY
# =========================================================

@frappe.whitelist()
def send_journal_entry_to_tally(journal_name):

    journal = frappe.get_doc(
        "Journal Entry",
        journal_name
    )

    company_name = journal.company

    posting_date = getdate(
        journal.posting_date
    )

    tally_date = posting_date.strftime(
        "%Y%m%d"
    )

    voucher_number = journal.name

    company_xml = escape(
        str(company_name)
    )

    voucher_number_xml = escape(
        str(voucher_number)
    )

    print("\n========================================")
    print("AUTO TALLY JOURNAL CREATE")
    print("ACTION          : CREATE")
    print("TALLY URL       :", TALLY_URL)
    print("ERP JOURNAL     :", journal_name)
    print("ERP DATE        :", journal.posting_date)
    print("TALLY DATE      :", tally_date)
    print("COMPANY         :", company_name)
    print("VOUCHER NUMBER  :", voucher_number)
    print("========================================")

    ledger_entries = ""

    for row in journal.accounts:

        account_name = escape(
            str(row.account)
        )

        # AUTO CREATE LEDGER IN TALLY
        if row.account:
            account_doc = frappe.get_doc(
                "Account",
                row.account
            )

            if account_doc.account_type == "Receivable":
                tally_parent = "Sundry Debtors"

            elif account_doc.account_type == "Payable":
                tally_parent = "Sundry Creditors"

            elif account_doc.root_type == "Expense":
                tally_parent = "Indirect Expenses"

            elif account_doc.root_type == "Income":
                tally_parent = "Sales Accounts"

            elif account_doc.root_type == "Asset":
                tally_parent = "Current Assets"

            elif account_doc.root_type == "Liability":
                tally_parent = "Current Liabilities"

            else:
                tally_parent = "Primary"

            print(
                f"AUTO MASTER SYNC: {row.account} -> {tally_parent}"
            )

            create_tally_ledger(
                row.account,
                company_name,
                tally_parent
            )

        debit = float(row.debit or 0)
        credit = float(row.credit or 0)

        if debit:
            amount = debit
            is_deemed_positive = "Yes"

        elif credit:
            amount = -credit
            is_deemed_positive = "No"

        else:
            continue

        ledger_entries += f"""
<LEDGERENTRIES.LIST>

<LEDGERNAME>{account_name}</LEDGERNAME>

<ISDEEMEDPOSITIVE>{is_deemed_positive}</ISDEEMEDPOSITIVE>

<AMOUNT>{amount:.2f}</AMOUNT>

</LEDGERENTRIES.LIST>
"""

    journal_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>Vouchers</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<VOUCHER
VCHTYPE="Journal"
ACTION="Create">

<DATE>{tally_date}</DATE>

<VOUCHERTYPENAME>Journal</VOUCHERTYPENAME>

<VOUCHERNUMBER>{voucher_number_xml}</VOUCHERNUMBER>

<REFERENCE>{voucher_number_xml}</REFERENCE>

<PERSISTEDVIEW>Accounting Voucher View</PERSISTEDVIEW>

<VCHENTRYMODE>As Voucher</VCHENTRYMODE>

{ledger_entries}

</VOUCHER>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    print("\n=========================================================")
    print("              ACTUAL TALLY JOURNAL CREATE XML")
    print("=========================================================")

    print(journal_xml)

    print("=========================================================")

    response = send_to_tally(
        journal_xml,
        "CREATE JOURNAL VOUCHER"
    )

    success = tally_response_success(
        response
    )

    print("\n========================================")
    print("AUTO TALLY JOURNAL CREATE RESULT:", success)
    print("ERP JOURNAL:", journal_name)
    print("========================================")

    return {
        "success": success,
        "journal": journal_name,
        "erp_date": str(journal.posting_date),
        "tally_date": tally_date,
        "voucher_number": voucher_number,
        "company": company_name,
        "tally_response": response
    }


# =========================================================
# AUTOMATIC JOURNAL ENTRY SUBMIT TRIGGER
# =========================================================

def journal_entry_on_submit(doc, method=None):

    print("\n========================================")
    print("AUTO TALLY SYNC TRIGGERED")
    print("ACTION: CREATE")
    print("Journal Entry:", doc.name)
    print("========================================")

    return send_journal_entry_to_tally(
        doc.name
    )

# =========================================================
# CANCEL JOURNAL ENTRY IN TALLY
# =========================================================

@frappe.whitelist()
def cancel_journal_entry_in_tally(journal_name):

    journal = frappe.get_doc(
        "Journal Entry",
        journal_name
    )

    company_name = journal.company

    posting_date = getdate(
        journal.posting_date
    )

    tally_date = posting_date.strftime(
        "%Y%m%d"
    )

    voucher_number = journal.name

    company_xml = escape(
        str(company_name)
    )

    voucher_number_xml = escape(
        str(voucher_number)
    )

    print("\n========================================")
    print("AUTO TALLY JOURNAL CANCEL")
    print("ACTION          : CANCEL")
    print("TALLY URL       :", TALLY_URL)
    print("ERP JOURNAL     :", journal_name)
    print("ERP DATE        :", journal.posting_date)
    print("TALLY DATE      :", tally_date)
    print("COMPANY         :", company_name)
    print("VOUCHER NUMBER  :", voucher_number)
    print("========================================")

    cancel_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>Vouchers</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<VOUCHER
DATE="{tally_date}"
TAGNAME="Voucher Number"
TAGVALUE="{voucher_number_xml}"
VCHTYPE="Journal"
ACTION="Cancel">

<DATE>{tally_date}</DATE>

<VOUCHERTYPENAME>Journal</VOUCHERTYPENAME>

<VOUCHERNUMBER>{voucher_number_xml}</VOUCHERNUMBER>

</VOUCHER>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    print("\n=========================================================")
    print("              ACTUAL TALLY JOURNAL CANCEL XML")
    print("=========================================================")

    print(cancel_xml)

    print("=========================================================")

    response = send_to_tally(
        cancel_xml,
        "CANCEL JOURNAL VOUCHER"
    )

    success = tally_response_success(
        response
    )

    print("\n========================================")
    print("AUTO TALLY JOURNAL CANCEL RESULT:", success)
    print("ERP JOURNAL:", journal_name)
    print("========================================")

    return {
        "success": success,
        "journal": journal_name,
        "erp_date": str(journal.posting_date),
        "tally_date": tally_date,
        "voucher_number": voucher_number,
        "company": company_name,
        "tally_response": response
    }


# =========================================================
# AUTOMATIC JOURNAL ENTRY CANCEL TRIGGER
# =========================================================

def journal_entry_on_cancel(doc, method=None):

    print("\n========================================")
    print("AUTO TALLY SYNC TRIGGERED")
    print("ACTION: CANCEL")
    print("Journal Entry:", doc.name)
    print("========================================")

    return cancel_journal_entry_in_tally(
        doc.name
    )

# =========================================================
# DELETE JOURNAL ENTRY IN TALLY
# =========================================================

@frappe.whitelist()
def delete_journal_entry_in_tally(journal_name):

    journal = frappe.get_doc(
        "Journal Entry",
        journal_name
    )

    company_name = journal.company

    posting_date = getdate(
        journal.posting_date
    )

    tally_date = posting_date.strftime(
        "%Y%m%d"
    )

    voucher_number = journal.name

    company_xml = escape(
        str(company_name)
    )

    voucher_number_xml = escape(
        str(voucher_number)
    )

    print("\n========================================")
    print("AUTO TALLY JOURNAL DELETE")
    print("ACTION          : DELETE")
    print("TALLY URL       :", TALLY_URL)
    print("ERP JOURNAL     :", journal_name)
    print("ERP DATE        :", journal.posting_date)
    print("TALLY DATE      :", tally_date)
    print("COMPANY         :", company_name)
    print("VOUCHER NUMBER  :", voucher_number)
    print("========================================")

    delete_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>Vouchers</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<VOUCHER
DATE="{tally_date}"
TAGNAME="Voucher Number"
TAGVALUE="{voucher_number_xml}"
VCHTYPE="Journal"
ACTION="Delete">

<DATE>{tally_date}</DATE>

<VOUCHERTYPENAME>Journal</VOUCHERTYPENAME>

<VOUCHERNUMBER>{voucher_number_xml}</VOUCHERNUMBER>

</VOUCHER>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    print("\n=========================================================")
    print("              ACTUAL TALLY JOURNAL DELETE XML")
    print("=========================================================")

    print(delete_xml)

    print("=========================================================")

    response = send_to_tally(
        delete_xml,
        "DELETE JOURNAL VOUCHER"
    )

    success = tally_response_success(
        response
    )

    print("\n========================================")
    print("AUTO TALLY JOURNAL DELETE RESULT:", success)
    print("ERP JOURNAL:", journal_name)
    print("========================================")

    return {
        "success": success,
        "journal": journal_name,
        "erp_date": str(journal.posting_date),
        "tally_date": tally_date,
        "voucher_number": voucher_number,
        "company": company_name,
        "tally_response": response
    }


# =========================================================
# AUTOMATIC JOURNAL ENTRY DELETE TRIGGER
# =========================================================

def journal_entry_on_trash(doc, method=None):

    print("\n========================================")
    print("AUTO TALLY SYNC TRIGGERED")
    print("ACTION: DELETE")
    print("Journal Entry:", doc.name)
    print("========================================")

    return delete_journal_entry_in_tally(
        doc.name
    )
    
def account_after_insert(doc, method=None):

    if doc.is_group:
        print(
            f"AUTO ACCOUNT SYNC SKIPPED: "
            f"{doc.name} - Group Account"
        )
        return

    if doc.account_type == "Receivable":
        tally_parent = "Sundry Debtors"

    elif doc.account_type == "Payable":
        tally_parent = "Sundry Creditors"

    elif doc.root_type == "Expense":
        tally_parent = "Indirect Expenses"

    elif doc.root_type == "Income":
        tally_parent = "Sales Accounts"

    elif doc.root_type == "Asset":
        tally_parent = "Current Assets"

    elif doc.root_type == "Liability":
        tally_parent = "Current Liabilities"

    else:
        tally_parent = "Primary"

    print(
        f"AUTO ACCOUNT SYNC: "
        f"{doc.name} -> {doc.company} -> {tally_parent}"
    )

    return create_tally_ledger(
        doc.name,
        doc.company,
        tally_parent
    )

def account_after_update(doc, method=None):

    if doc.is_group:
        print(
            f"AUTO ACCOUNT UPDATE SKIPPED: "
            f"{doc.name} - Group Account"
        )
        return

    if doc.account_type == "Receivable":
        tally_parent = "Sundry Debtors"

    elif doc.account_type == "Payable":
        tally_parent = "Sundry Creditors"

    elif doc.root_type == "Expense":
        tally_parent = "Indirect Expenses"

    elif doc.root_type == "Income":
        tally_parent = "Sales Accounts"

    elif doc.root_type == "Asset":
        tally_parent = "Current Assets"

    elif doc.root_type == "Liability":
        tally_parent = "Current Liabilities"

    else:
        tally_parent = "Primary"

    print(
        f"AUTO ACCOUNT UPDATE: "
        f"{doc.name} -> {doc.company} -> {tally_parent}"
    )

    return create_tally_ledger(
        doc.name,
        doc.company,
        tally_parent
    )

def account_on_trash(doc, method=None):

    if doc.is_group:
        print(
            f"AUTO ACCOUNT DELETE SKIPPED: "
            f"{doc.name} - Group Account"
        )
        return

    ledger_name = escape(str(doc.name))
    company_name = escape(str(doc.company))

    delete_xml = f"""
<ENVELOPE>
<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>
<DESC>
<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
</STATICVARIABLES>
</DESC>

<DATA>
<TALLYMESSAGE xmlns:UDF="TallyUDF">

<LEDGER NAME="{ledger_name}" ACTION="Delete">
<NAME>{ledger_name}</NAME>
</LEDGER>

</TALLYMESSAGE>
</DATA>
</BODY>
</ENVELOPE>
"""

    print(
        f"AUTO ACCOUNT DELETE: "
        f"{doc.name} -> {doc.company}"
    )

    return send_to_tally(
        delete_xml,
        f"DELETE LEDGER - {doc.name}"
    )

def cost_center_after_insert(doc, method=None):

    if doc.is_group:
        print(
            f"AUTO COST CENTER SYNC SKIPPED: "
            f"{doc.name} - Group Cost Center"
        )
        return

    cost_center_name = escape(str(doc.name))
    company_name = escape(str(doc.company))

    cost_center_xml = f"""
<ENVELOPE>
<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>
<DESC>
<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
</STATICVARIABLES>
</DESC>

<DATA>
<TALLYMESSAGE xmlns:UDF="TallyUDF">

<COSTCENTRE NAME="{cost_center_name}" ACTION="Create">
<NAME>{cost_center_name}</NAME>
<ISSUBLEDGER>No</ISSUBLEDGER>
</COSTCENTRE>

</TALLYMESSAGE>
</DATA>
</BODY>
</ENVELOPE>
"""

    print(
        f"AUTO COST CENTER SYNC: "
        f"{doc.name} -> {doc.company}"
    )

    return send_to_tally(
        cost_center_xml,
        f"COST CENTER - {doc.name}"
    )

def cost_center_after_update(doc, method=None):

    if doc.is_group:
        print(
            f"AUTO COST CENTER UPDATE SKIPPED: "
            f"{doc.name} - Group Cost Center"
        )
        return

    cost_center_name = escape(str(doc.name))
    company_name = escape(str(doc.company))

    cost_center_xml = f"""
<ENVELOPE>
<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>
<DESC>
<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
</STATICVARIABLES>
</DESC>

<DATA>
<TALLYMESSAGE xmlns:UDF="TallyUDF">

<COSTCENTRE NAME="{cost_center_name}" ACTION="Alter">
<NAME>{cost_center_name}</NAME>
<ISSUBLEDGER>No</ISSUBLEDGER>
</COSTCENTRE>

</TALLYMESSAGE>
</DATA>
</BODY>
</ENVELOPE>
"""

    print(
        f"AUTO COST CENTER UPDATE: "
        f"{doc.name} -> {doc.company}"
    )

    return send_to_tally(
        cost_center_xml,
        f"UPDATE COST CENTER - {doc.name}"
    )

def cost_center_on_trash(doc, method=None):

    if doc.is_group:
        print(
            f"AUTO COST CENTER DELETE SKIPPED: "
            f"{doc.name} - Group Cost Center"
        )
        return

    cost_center_name = escape(str(doc.name))
    company_name = escape(str(doc.company))

    delete_xml = f"""
<ENVELOPE>
<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>
<DESC>
<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
</STATICVARIABLES>
</DESC>

<DATA>
<TALLYMESSAGE xmlns:UDF="TallyUDF">

<COSTCENTRE NAME="{cost_center_name}" ACTION="Delete">
<NAME>{cost_center_name}</NAME>
</COSTCENTRE>

</TALLYMESSAGE>
</DATA>
</BODY>
</ENVELOPE>
"""

    print(
        f"AUTO COST CENTER DELETE: "
        f"{doc.name} -> {doc.company}"
    )

    return send_to_tally(
        delete_xml,
        f"DELETE COST CENTER - {doc.name}"
    )

def warehouse_after_insert(doc, method=None):

    if doc.is_group:
        print(
            f"AUTO WAREHOUSE SYNC SKIPPED: "
            f"{doc.name} - Group Warehouse"
        )
        return

    warehouse_name = escape(str(doc.name))
    company_name = escape(str(doc.company))

    godown_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<GODOWN NAME="{warehouse_name}" ACTION="Create">

<NAME>{warehouse_name}</NAME>

</GODOWN>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    print(
        f"AUTO WAREHOUSE SYNC: "
        f"{doc.name} -> {doc.company}"
    )

    return send_to_tally(
        godown_xml,
        f"GODOWN - {doc.name}"
    )


def warehouse_after_update(doc, method=None):
    if doc.is_group:
        print(
            f"AUTO WAREHOUSE UPDATE SKIPPED: "
            f"{doc.name} - Group Warehouse"
        )
        return

    warehouse_name = escape(str(doc.name))
    company_name = escape(str(doc.company))

    # ERPNext parent -> Tally parent mapping
    if doc.parent_warehouse == "All Warehouses - APPL":
        parent_warehouse = "Main Location"
    else:
        parent_warehouse = str(doc.parent_warehouse or "Main Location")

    parent_warehouse = escape(parent_warehouse)

    godown_xml = f"""
<ENVELOPE>
<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<GODOWN NAME="{warehouse_name}" ACTION="Alter">

<NAME>{warehouse_name}</NAME>

<PARENT>{parent_warehouse}</PARENT>

</GODOWN>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    print(
        f"AUTO WAREHOUSE UPDATE: "
        f"{doc.name} -> {doc.company} -> "
        f"{doc.parent_warehouse} -> TALLY: {parent_warehouse}"
    )

    return send_to_tally(
        godown_xml,
        f"UPDATE GODOWN - {doc.name}"
    )

def warehouse_on_trash(doc, method=None):

    if doc.is_group:
        print(
            f"AUTO WAREHOUSE DELETE SKIPPED: "
            f"{doc.name} - Group Warehouse"
        )
        return

    warehouse_name = escape(str(doc.name))
    company_name = escape(str(doc.company))

    delete_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_name}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<GODOWN NAME="{warehouse_name}" ACTION="Delete">

<NAME>{warehouse_name}</NAME>

</GODOWN>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    print(
        f"AUTO WAREHOUSE DELETE: "
        f"{doc.name} -> {doc.company}"
    )

    return send_to_tally(
        delete_xml,
        f"DELETE GODOWN - {doc.name}"
    )

# =========================================================
# UOM / UNIT AUTO SYNC
# =========================================================

def uom_after_insert(doc, method=None):

    unit_name = doc.uom_name or doc.name
    symbol = doc.symbol or unit_name
    company_name = "ABC Parent Pvt Ltd"

    print(
        f"AUTO UOM SYNC: "
        f"{unit_name} ({symbol}) -> {company_name}"
    )

    return create_tally_unit(
        unit_name,
        symbol,
        company_name
    )


def uom_after_update(doc, method=None):

    unit_name = doc.uom_name or doc.name
    company_name = "ABC Parent Pvt Ltd"

    unit_xml_name = escape(str(unit_name))
    company_xml = escape(str(company_name))

    unit_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<UNIT NAME="{unit_xml_name}" ACTION="Alter">

<NAME>{unit_xml_name}</NAME>

<ISSIMPLEUNIT>Yes</ISSIMPLEUNIT>

<SYMBOL>{unit_xml_name}</SYMBOL>

<DECIMALPLACES>0</DECIMALPLACES>

</UNIT>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    print(
        f"AUTO UOM UPDATE: "
        f"{unit_name} -> {company_name}"
    )

    return send_to_tally(
        unit_xml,
        f"UPDATE UNIT - {unit_name}"
    )


def uom_on_trash(doc, method=None):

    unit_name = doc.uom_name or doc.name
    company_name = "ABC Parent Pvt Ltd"

    unit_xml_name = escape(str(unit_name))
    company_xml = escape(str(company_name))

    delete_xml = f"""
<ENVELOPE>

<HEADER>
<VERSION>1</VERSION>
<TALLYREQUEST>Import</TALLYREQUEST>
<TYPE>Data</TYPE>
<ID>All Masters</ID>
</HEADER>

<BODY>

<DESC>

<STATICVARIABLES>
<SVCURRENTCOMPANY>{company_xml}</SVCURRENTCOMPANY>
</STATICVARIABLES>

</DESC>

<DATA>

<TALLYMESSAGE xmlns:UDF="TallyUDF">

<UNIT NAME="{unit_xml_name}" ACTION="Delete">

<NAME>{unit_xml_name}</NAME>

</UNIT>

</TALLYMESSAGE>

</DATA>

</BODY>

</ENVELOPE>
"""

    print(
        f"AUTO UOM DELETE: "
        f"{unit_name} -> {company_name}"
    )

    return send_to_tally(
        delete_xml,
        f"DELETE UNIT - {unit_name}"
    )

# =========================================================
# ERP AI ASSISTANT
# =========================================================

app_include_js = "/assets/bk_account/js/erp_ai_assistant.js"
app_include_css = "/assets/bk_account/css/erp_ai_assistant.css"



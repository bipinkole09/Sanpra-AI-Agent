import frappe
from frappe.utils import now_datetime


@frappe.whitelist()
def send_chat_message(receiver, message):
    """
    Send a person-to-person ERP AI chat message.
    The sender is always taken from the logged-in Frappe user.
    """

    sender = frappe.session.user

    if not sender or sender == "Guest":
        frappe.throw("You must be logged in to send messages.")

    if not receiver:
        frappe.throw("Receiver is required.")

    if not message or not str(message).strip():
        frappe.throw("Message cannot be empty.")

    receiver = str(receiver).strip()
    message = str(message).strip()

    receiver_user = frappe.db.get_value(
        "User",
        receiver,
        ["name", "enabled", "user_type"],
        as_dict=True,
    )

    if not receiver_user:
        frappe.throw("Receiver user was not found.")

    if not receiver_user.enabled:
        frappe.throw("Receiver user is disabled.")

    if receiver_user.user_type != "System User":
        frappe.throw("Receiver must be a System User.")

    chat_message = frappe.get_doc(
        {
            "doctype": "ERP AI Chat Message",
            "sender": sender,
            "receiver": receiver,
            "message": message,
            "sent_at": now_datetime(),
            "read": 0,
        }
    )

    chat_message.insert(ignore_permissions=True)
    frappe.db.commit()

    result = {
        "name": chat_message.name,
        "sender": sender,
        "receiver": receiver,
        "message": message,
        "sent_at": str(chat_message.sent_at),
        "read": 0,
    }

    try:
        frappe.publish_realtime(
            "erp_ai_chat_message",
            result,
            user=receiver,
        )
    except Exception:
        frappe.log_error(
            frappe.get_traceback(),
            "ERP AI Chat Realtime Notification Error",
        )

    return result


@frappe.whitelist()
def get_chat_messages(other_user, limit=50):
    """
    Get messages between the logged-in user and another user.
    """

    current_user = frappe.session.user

    if not current_user or current_user == "Guest":
        frappe.throw("You must be logged in to view messages.")

    if not other_user:
        frappe.throw("Other user is required.")

    other_user = str(other_user).strip()

    other_user_data = frappe.db.get_value(
        "User",
        other_user,
        ["name", "enabled", "user_type"],
        as_dict=True,
    )

    if not other_user_data:
        frappe.throw("User was not found.")

    if not other_user_data.enabled:
        frappe.throw("User is disabled.")

    if other_user_data.user_type != "System User":
        frappe.throw("User must be a System User.")

    try:
        limit = int(limit)
    except (TypeError, ValueError):
        limit = 50

    limit = max(1, min(limit, 100))

    messages = frappe.get_all(
        "ERP AI Chat Message",
        filters=[
            [
                "sender",
                "in",
                [current_user, other_user],
            ],
            [
                "receiver",
                "in",
                [current_user, other_user],
            ],
        ],
        fields=[
            "name",
            "sender",
            "receiver",
            "message",
            "sent_at",
            "read",
        ],
        order_by="sent_at asc",
        limit_page_length=limit,
        ignore_permissions=True,
    )

    return messages


@frappe.whitelist()
def mark_messages_read(other_user):
    """
    Mark messages received from another user as read.
    """

    current_user = frappe.session.user

    if not current_user or current_user == "Guest":
        frappe.throw("You must be logged in.")

    if not other_user:
        frappe.throw("Other user is required.")

    other_user = str(other_user).strip()

    frappe.db.sql(
        """
        UPDATE `tabERP AI Chat Message`
        SET `read` = 1
        WHERE `sender` = %s
          AND `receiver` = %s
          AND `read` = 0
        """,
        (other_user, current_user),
    )

    frappe.db.commit()

    return {
        "success": True,
    }


@frappe.whitelist()
def create_chat_contact(
    first_name,
    last_name=None,
    email=None,
    mobile_no=None,
):
    """
    Add an existing ERPNext System User as a chat contact.

    This function does NOT create a new ERPNext User.
    The email must belong to an existing enabled System User.
    """

    first_name = str(first_name or "").strip()
    last_name = str(last_name or "").strip()
    email = str(email or "").strip()
    mobile_no = str(mobile_no or "").strip()

    if not first_name:
        frappe.throw("First Name is required.")

    if not email:
        frappe.throw("Email is required.")

    # Only an existing ERPNext User can be added.
    existing_user = frappe.db.get_value(
        "User",
        email,
        ["name", "enabled", "user_type", "first_name", "last_name"],
        as_dict=True,
    )

    if not existing_user:
        frappe.throw(
            "No ERPNext User exists with this email. "
            "Please enter an existing ERPNext User email."
        )

    if not existing_user.enabled:
        frappe.throw("This ERPNext User is disabled.")

    if existing_user.user_type != "System User":
        frappe.throw(
            "This ERPNext User is not a System User and cannot be used for chat."
        )

    user_name = existing_user.name

    # Check whether Contact already exists for this email.
    existing_contact = frappe.db.get_value(
        "Contact Email",
        {"email_id": email},
        "parent",
    )

    if existing_contact:
        contact_name = existing_contact
    else:
        contact = frappe.get_doc(
            {
                "doctype": "Contact",
                "first_name": (
                    existing_user.first_name
                    or first_name
                ),
                "last_name": (
                    existing_user.last_name
                    or last_name
                ),
                "email_ids": [
                    {
                        "email_id": email,
                        "is_primary": 1,
                    }
                ],
                "phone_nos": (
                    [
                        {
                            "phone": mobile_no,
                            "is_primary_mobile_no": 1,
                        }
                    ]
                    if mobile_no
                    else []
                ),
            }
        )

        contact.insert(ignore_permissions=True)
        contact_name = contact.name

    frappe.db.commit()

    return {
        "success": True,
        "user": user_name,
        "contact": contact_name,
        "first_name": (
            existing_user.first_name
            or first_name
        ),
        "last_name": (
            existing_user.last_name
            or last_name
        ),
        "email": email,
        "mobile_no": mobile_no,
    }

@frappe.whitelist()
def delete_chat_contact(contact_name):
    """
    Delete only the ERPNext Contact used by the ERP AI Contacts list.

    This does NOT delete:
    - the linked ERPNext User
    - ERP AI Chat Message records
    """

    contact_name = str(contact_name or "").strip()

    if not contact_name:
        frappe.throw("Contact is required.")

    contact = frappe.db.get_value(
        "Contact",
        contact_name,
        ["name", "user"],
        as_dict=True,
    )

    if not contact:
        frappe.throw("Contact was not found.")

    # Delete only the Contact record.
    # The linked ERPNext User and chat history are untouched.
    frappe.delete_doc(
        "Contact",
        contact.name,
        ignore_permissions=True,
    )

    frappe.db.commit()

    return {
        "success": True,
        "contact": contact.name,
    }
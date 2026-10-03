;(function () {
    "use strict";

    let assistantState = {
    recognition: null,
    listening: false,
    callActive: false,
    processingVoice: false,
    callSeconds: 0,
    callTimer: null,
    speechSupported: false,
    speaking: false,
    speakingTimer: null,

    /* Person-to-person chat */
    currentPersonUser: null,
    currentPersonContact: null
};

    let elements = {};

    /* =========================================================
       INITIALIZATION
       ========================================================= */

    function initERPAssistant() {
        if (document.getElementById("erp-ai-assistant")) {
            return;
        }

        createAssistantUI();

        const assistant =
            document.getElementById("erp-ai-assistant");

        if (!assistant) {
            return;
        }

        cacheElements(assistant);

        /*
         * IMPORTANT:
         * Bot Call panel must ALWAYS be hidden
         * when ERP AI Assistant first loads.
         */
        if (elements.callPanel) {
            elements.callPanel.classList.add(
                "erp-ai-call-hidden"
            );

            elements.callPanel.style.display = "none";
        }

        initSpeechRecognition();
        bindEvents();
    }

    /* =========================================================
       CREATE UI
       ========================================================= */

    function createAssistantUI() {
        const wrapper = document.createElement("div");

        wrapper.innerHTML = `
            <div id="erp-ai-assistant">

                <!-- FLOATING BUTTON -->
                <button
                    type="button"
                    id="erp-ai-floating-button"
                    class="erp-ai-floating-button"
                    aria-label="Open ERP AI Assistant"
                >
                    <span class="erp-ai-floating-icon">🤖</span>
                </button>

                <!-- MAIN ASSISTANT -->
                <div
                    class="erp-ai-main-panel erp-ai-main-hidden"
                >

                    <!-- HEADER -->
                    <div class="erp-ai-header">

                        <div class="erp-ai-header-left">

                            <div class="erp-ai-avatar">
                                🤖
                            </div>

                            <div class="erp-ai-header-info">

                                <div class="erp-ai-title">
                                    ERP AI Assistant
                                </div>

                                <div class="erp-ai-status">
                                    <span class="erp-ai-status-dot"></span>
                                    Online · Ready to help
                                </div>

                            </div>

                        </div>

                        <button
                            type="button"
                            class="erp-ai-header-call"
                            aria-label="Start Bot Call"
                            title="Start Bot Call"
                        >
                            ☎️
                        </button>

                        <button
                            type="button"
                            class="erp-ai-close-button"
                            aria-label="Close"
                        >
                            ×
                        </button>

                    </div>

                    <!-- CHAT -->
                    <div class="erp-ai-chat-area">

                        <!-- CONTACTS BUTTON -->
<button
    type="button"
    class="erp-ai-contacts-button"
    id="erp-ai-contacts-button"
>
    <span>👥</span>
    <span>Contacts</span>
</button>

<!-- CONTACTS PANEL -->
<div
    class="erp-ai-contacts-panel erp-ai-contacts-hidden"
    id="erp-ai-contacts-panel"
>
    <div class="erp-ai-contacts-header">

    <button
        type="button"
        class="erp-ai-contacts-back"
        id="erp-ai-contacts-back"
        aria-label="Back"
    >
        ←
    </button>

    <div class="erp-ai-contacts-header-info">
        <div class="erp-ai-contacts-title">
            Contacts
        </div>

        <div class="erp-ai-contacts-subtitle">
            Select a person to chat
        </div>
    </div>

    <button
        type="button"
        class="erp-ai-add-contact-button"
        id="erp-ai-add-contact-button"
        aria-label="Add Contact"
        title="Add Contact"
    >
        +
    </button>

</div>

    <div
        class="erp-ai-contact-list"
        id="erp-ai-contact-list"
    >
        <div class="erp-ai-contacts-loading">
            Loading contacts...
        </div>
    </div>
</div>

<!-- PERSON CHAT -->
<div
    class="erp-ai-person-chat erp-ai-person-chat-hidden"
    id="erp-ai-person-chat"
>
    <div class="erp-ai-person-header">

        <button
            type="button"
            class="erp-ai-person-back"
            id="erp-ai-person-back"
            aria-label="Back to Contacts"
        >
            ←
        </button>

        <div
            class="erp-ai-person-avatar"
            id="erp-ai-person-avatar"
        >
            👤
        </div>

        <div class="erp-ai-person-info">

            <div
                class="erp-ai-person-name"
                id="erp-ai-person-name"
            >
                Contact
            </div>

            <div
                class="erp-ai-person-status"
                id="erp-ai-person-status"
            >
                Contact
            </div>

        </div>

        <button
            type="button"
            class="erp-ai-person-call"
            id="erp-ai-person-call"
            aria-label="Voice call"
            title="Voice call"
        >
            📞
        </button>

        <button
            type="button"
            class="erp-ai-person-video"
            id="erp-ai-person-video"
            aria-label="Video call"
            title="Video call"
        >
            📹
        </button>

    </div>

    <div
        class="erp-ai-person-messages"
        id="erp-ai-person-messages"
    >
        <div class="erp-ai-person-empty">
            Start a conversation with this person.
        </div>
    </div>

    <div class="erp-ai-person-input-area">

        <input
            type="text"
            class="erp-ai-person-input"
            id="erp-ai-person-input"
            placeholder="Type a message ..."
            autocomplete="off"
        />

        <button
            type="button"
            class="erp-ai-person-send"
            id="erp-ai-person-send"
            aria-label="Send message"
        >
            ➤
        </button>

    </div>
</div>




                        <!-- WELCOME -->
                        <div class="erp-ai-welcome">

                            <div class="erp-ai-welcome-avatar">
                                🤖
                            </div>

                            <div class="erp-ai-welcome-title">
                                Hello! I'm your ERP AI Bot
                            </div>

                            <div class="erp-ai-welcome-text">
                                Ask me about sales, purchases, stock, payments,
                                customers, accounts or ERPNext documents.
                            </div>

                        </div>

                        <!-- QUICK ACTIONS -->
                        <div class="erp-ai-quick-actions">

                            <button
                                type="button"
                                class="erp-ai-quick-button"
                                data-question="How many Sales Invoices?"
                            >
                                <span class="erp-ai-quick-icon">📊</span>
                                <span>How many Sales Invoices?</span>
                            </button>

                            <button
                                type="button"
                                class="erp-ai-quick-button"
                                data-question="Show low stock items"
                            >
                                <span class="erp-ai-quick-icon">📦</span>
                                <span>Show low stock items</span>
                            </button>

                            <button
                                type="button"
                                class="erp-ai-quick-button"
                                data-question="Show pending Purchase Orders"
                            >
                                <span class="erp-ai-quick-icon">🛒</span>
                                <span>Show pending Purchase Orders</span>
                            </button>

                        </div>

                        <!-- MESSAGES -->
                        <div class="erp-ai-messages"></div>

                    </div>

                    <!-- INPUT -->
                    <div class="erp-ai-input-area">

                        <button
                            type="button"
                            class="erp-ai-plus-button"
                            aria-label="More options"
                        >
                            +
                        </button>

                        <input
                            type="text"
                            class="erp-ai-input"
                            placeholder="Type a message ..."
                            autocomplete="off"
                        />

                        <button
                            type="button"
                            class="erp-ai-mic-button"
                            aria-label="Voice input"
                        >
                            🎤
                        </button>

                        <button
                            type="button"
                            class="erp-ai-send-button"
                            aria-label="Send"
                        >
                            ➤
                        </button>

                    </div>

                    <!-- BOT CALL PANEL -->
                    <div class="erp-ai-call-panel erp-ai-call-hidden">

                        <div class="erp-ai-call-header">

                            <div class="erp-ai-call-header-left">

                                <div class="erp-ai-call-avatar">
                                    🤖
                                </div>

                                <div>

                                    <div class="erp-ai-call-title">
                                        ERP AI Bot
                                    </div>

                                    <div class="erp-ai-call-status">
                                        Ready to talk
                                    </div>

                                </div>

                            </div>

                            <button
                                type="button"
                                class="erp-ai-call-close"
                                aria-label="Close call"
                            >
                                ×
                            </button>

                        </div>

                        <div class="erp-ai-call-body">

                            <div class="erp-ai-call-avatar-large">
                                <div class="erp-ai-call-avatar-ring"></div>
                                <div class="erp-ai-call-avatar-inner">
                                    🤖
                                </div>
                            </div>

                            <div class="erp-ai-call-timer">
                                00:00
                            </div>

                            <div class="erp-ai-call-main-status">
                                Ready to talk
                            </div>

                            <div class="erp-ai-call-transcript">
                                Press the microphone to start speaking.
                            </div>

                            <div class="erp-ai-call-waveform">
                                <span></span>
                                <span></span>
                                <span></span>
                                <span></span>
                                <span></span>
                                <span></span>
                                <span></span>
                            </div>

                            <div class="erp-ai-call-controls">

                                <button
                                    type="button"
                                    class="erp-ai-call-mic"
                                    aria-label="Start microphone"
                                >
                                    🎤
                                </button>

                                <button
                                    type="button"
                                    class="erp-ai-call-end"
                                    aria-label="End call"
                                >
                                    End Call
                                </button>

                            </div>

                        </div>

                    </div>

                </div>

            </div>
        `;

        document.body.appendChild(wrapper.firstElementChild);
    }

    /* =========================================================
       CACHE ELEMENTS
       ========================================================= */

    function cacheElements(assistant) {

        elements.assistant =
            assistant;

        elements.floatingButton =
            assistant.querySelector(
                "#erp-ai-floating-button"
            );

        elements.mainPanel =
            assistant.querySelector(
                ".erp-ai-main-panel"
            );

        elements.headerCallButton =
            assistant.querySelector(
                ".erp-ai-header-call"
            );

        elements.closeButton =
            assistant.querySelector(
                ".erp-ai-close-button"
            );

        elements.chatArea =
            assistant.querySelector(
                ".erp-ai-chat-area"
            );

        elements.messages =
            assistant.querySelector(
                ".erp-ai-messages"
            );

        elements.input =
            assistant.querySelector(
                ".erp-ai-input"
            );

        elements.sendButton =
            assistant.querySelector(
                ".erp-ai-send-button"
            );

        elements.micButton =
            assistant.querySelector(
                ".erp-ai-mic-button"
            );

        elements.quickButtons =
            assistant.querySelectorAll(
                ".erp-ai-quick-button"
            );

                elements.contactsButton =
            assistant.querySelector(
                "#erp-ai-contacts-button"
            );

        elements.contactsPanel =
            assistant.querySelector(
                "#erp-ai-contacts-panel"
            );

        elements.contactsBack =
            assistant.querySelector(
                "#erp-ai-contacts-back"
            );

        elements.addContactButton =
            assistant.querySelector(
                "#erp-ai-add-contact-button"
            );

        elements.contactList =
            assistant.querySelector(
                "#erp-ai-contact-list"
            );

        elements.personChat =
            assistant.querySelector(
                "#erp-ai-person-chat"
            );

        elements.personBack =
            assistant.querySelector(
                "#erp-ai-person-back"
            );

        elements.personAvatar =
            assistant.querySelector(
                "#erp-ai-person-avatar"
            );

        elements.personName =
            assistant.querySelector(
                "#erp-ai-person-name"
            );

        elements.personStatus =
            assistant.querySelector(
                "#erp-ai-person-status"
            );

        elements.personCall =
            assistant.querySelector(
                "#erp-ai-person-call"
            );

        elements.personVideo =
            assistant.querySelector(
                "#erp-ai-person-video"
            );

        elements.personMessages =
            assistant.querySelector(
                "#erp-ai-person-messages"
            );

        elements.personInput =
            assistant.querySelector(
                "#erp-ai-person-input"
            );

        elements.personSend =
            assistant.querySelector(
                "#erp-ai-person-send"
            );

        elements.callPanel =
            assistant.querySelector(
                ".erp-ai-call-panel"
            );

        elements.callMic =
            assistant.querySelector(
                ".erp-ai-call-mic"
            );

        elements.callEnd =
            assistant.querySelector(
                ".erp-ai-call-end"
            );

        elements.callClose =
            assistant.querySelector(
                ".erp-ai-call-close"
            );

        elements.callStatus =
            assistant.querySelector(
                ".erp-ai-call-status"
            );

        elements.callMainStatus =
            assistant.querySelector(
                ".erp-ai-call-main-status"
            );

        elements.callTranscript =
            assistant.querySelector(
                ".erp-ai-call-transcript"
            );

        elements.callTimer =
            assistant.querySelector(
                ".erp-ai-call-timer"
            );

        elements.callAvatar =
            assistant.querySelector(
                ".erp-ai-call-avatar"
            );

        elements.callAvatarLarge =
            assistant.querySelector(
                ".erp-ai-call-avatar-large"
            );

        elements.callWaveform =
            assistant.querySelector(
                ".erp-ai-call-waveform"
            );
    }

    /* =========================================================
       EVENTS
       ========================================================= */

    function bindEvents() {

        if (elements.floatingButton) {
            elements.floatingButton.addEventListener(
                "click",
                function () {
                    openAssistant();
                }
            );
        }

        if (elements.headerCallButton) {
            elements.headerCallButton.addEventListener(
                "click",
                function () {
                    startCall();
                }
            );
        }

        if (elements.closeButton) {
            elements.closeButton.addEventListener(
                "click",
                function () {
                    closeAssistant();
                }
            );
        }

        if (elements.sendButton) {
            elements.sendButton.addEventListener(
                "click",
                function () {
                    sendQuestion();
                }
            );
        }

        if (elements.input) {

            elements.input.addEventListener(
                "keydown",
                function (event) {

                    if (
                        event.key === "Enter" &&
                        !event.shiftKey
                    ) {
                        event.preventDefault();

                        sendQuestion();
                    }
                }
            );
        }

        if (elements.micButton) {
            elements.micButton.addEventListener(
                "click",
                function () {
                    openAssistant();

                    setTimeout(
                        function () {
                            startCall();
                        },
                        200
                    );
                }
            );
        }

        if (elements.quickButtons) {

            elements.quickButtons.forEach(
                function (button) {

                    button.addEventListener(
                        "click",
                        function () {

                            const question =
                                button.getAttribute(
                                    "data-question"
                                );

                            if (question) {
                                sendQuestion(question);
                            }

                        }
                    );

                }
            );
        }

                // CONTACTS
        if (elements.contactsButton) {
            elements.contactsButton.addEventListener(
                "click",
                function () {
                    openContacts();
                }
            );
        }
        
        console.log(
            "ADD CONTACT ELEMENT:",
            elements.addContactButton
        );

        if (elements.addContactButton) {
            elements.addContactButton.addEventListener(
                "click",
                function () {
                    openAddContactForm();
                }
            );
        } 

        // CONTACTS BACK
        if (elements.contactsBack) {
            elements.contactsBack.addEventListener(
                "click",
                function () {
                    closeContacts();
                }
            );
        }

        // PERSON CHAT BACK
        if (elements.personBack) {
            elements.personBack.addEventListener(
                "click",
                function () {
                    closePersonChat();
                }
            );
        }

        // PERSON CHAT SEND
        if (elements.personSend) {
            elements.personSend.addEventListener(
                "click",
                function () {
                    sendPersonMessage();
                }
            );
        }

        // PERSON CHAT ENTER
        if (elements.personInput) {
            elements.personInput.addEventListener(
                "keydown",
                function (event) {

                    if (
                        event.key === "Enter" &&
                        !event.shiftKey
                    ) {
                        event.preventDefault();

                        sendPersonMessage();
                    }

                }
            );
        }

        if (elements.callMic) {
            elements.callMic.addEventListener(
                "click",
                function () {

                    if (
                        assistantState.listening
                    ) {
                        stopListening();
                    } else {
                        startListening(true);
                    }

                }
            );
        }

        if (elements.callEnd) {
            elements.callEnd.addEventListener(
                "click",
                function () {
                    endCall();
                }
            );
        }

        if (elements.callClose) {
            elements.callClose.addEventListener(
                "click",
                function () {
                    endCall();
                }
            );
        }
    }

    /* =========================================================
       OPEN ASSISTANT
       ========================================================= */

    function openAssistant() {

        if (!elements.mainPanel) {
            return;
        }

        elements.mainPanel.classList.remove(
            "erp-ai-main-hidden"
        );

        elements.mainPanel.classList.add(
            "erp-ai-main-visible"
        );

        if (elements.input) {
            setTimeout(
                function () {
                    elements.input.focus();
                },
                150
            );
        }
    }

    /* =========================================================
       CLOSE ASSISTANT
       ========================================================= */

    function closeAssistant() {

        if (assistantState.callActive) {
            endCall();
        }

        if (!elements.mainPanel) {
            return;
        }

        elements.mainPanel.classList.remove(
            "erp-ai-main-visible"
        );

        elements.mainPanel.classList.add(
            "erp-ai-main-hidden"
        );
    }

    /* =========================================================
       CONTACTS
       ========================================================= */

    function openContacts() {

        if (
            !elements.contactsPanel ||
            !elements.contactsButton
        ) {
            return;
        }

        elements.contactsPanel.classList.remove(
            "erp-ai-contacts-hidden"
        );

        elements.contactsPanel.style.display = "flex";

        elements.contactsButton.style.display = "none";

        loadContacts();
    }


    function closeContacts() {

        if (!elements.contactsPanel) {
            return;
        }

        elements.contactsPanel.classList.add(
            "erp-ai-contacts-hidden"
        );

        elements.contactsPanel.style.display = "none";

        if (elements.contactsButton) {
            elements.contactsButton.style.display = "flex";
        }
    }


    function loadContacts() {

        if (!elements.contactList) {
            return;
        }

        elements.contactList.innerHTML = `
            <div class="erp-ai-contacts-loading">
                Loading contacts...
            </div>
        `;

        frappe.call({
            method: "frappe.client.get_list",
            args: {
                doctype: "Contact",
                fields: [
                    "name",
                    "first_name",
                    "last_name",
                    "email_id",
                    "mobile_no",
                    "user"
                ],
                order_by: "first_name asc",
                limit_page_length: 50
            }
        }).then(function (response) {

            const contacts =
                response &&
                response.message
                    ? response.message
                    : [];

            renderContacts(contacts);

        }).catch(function (error) {

            console.error(
                "ERP AI Contacts Error:",
                error
            );

            elements.contactList.innerHTML = `
                <div class="erp-ai-contacts-error">
                    Unable to load contacts.
                </div>
            `;
        });
    }


    function renderContacts(contacts) {

    if (!elements.contactList) {
        return;
    }

    if (
        !Array.isArray(contacts) ||
        contacts.length === 0
    ) {
        elements.contactList.innerHTML = `
            <div class="erp-ai-contacts-empty">
                No contacts found.
            </div>
        `;

        return;
    }

    elements.contactList.innerHTML = "";

    contacts.forEach(function (contact) {

        const firstName =
            contact.first_name || "";

        const lastName =
            contact.last_name || "";

        const fullName =
            (
                firstName +
                " " +
                lastName
            ).trim() ||
            contact.name ||
            "Contact";

        const email =
            contact.email_id ||
            "";

        const mobile =
            contact.mobile_no ||
            "";

        const detail =
            mobile ||
            email ||
            "Contact";

        const item =
            document.createElement("div");

        item.className =
            "erp-ai-contact-item";

        item.innerHTML = `
            <span class="erp-ai-contact-avatar">
                👤
            </span>

            <span class="erp-ai-contact-info">

                <span class="erp-ai-contact-name">
                    ${escapeHTML(fullName)}
                </span>

                <span class="erp-ai-contact-detail">
                    ${escapeHTML(detail)}
                </span>

            </span>

            <button
                type="button"
                class="erp-ai-contact-chat-button"
                aria-label="Open chat"
                title="Open chat"
            >
                ›
            </button>

            <button
                type="button"
                class="erp-ai-contact-delete-button"
                aria-label="Delete contact"
                title="Delete contact"
            >
                🗑
            </button>
        `;

        const chatButton =
            item.querySelector(
                ".erp-ai-contact-chat-button"
            );

        const deleteButton =
            item.querySelector(
                ".erp-ai-contact-delete-button"
            );

        chatButton.addEventListener(
            "click",
            function (event) {
                event.stopPropagation();
                openPersonChat(contact);
            }
        );

        deleteButton.addEventListener(
            "click",
            function (event) {

                event.stopPropagation();

                const confirmed =
                    window.confirm(
                        "Delete this contact from your chat contacts?"
                    );

                if (!confirmed) {
                    return;
                }

                deleteButton.disabled = true;
                deleteButton.textContent = "…";

                frappe.call({
                    method:
                        "bk_account.api.chat.delete_chat_contact",

                    args: {
                        contact_name:
                            contact.name
                    }
                })
                .then(function (response) {

                    if (
                        !response ||
                        !response.message ||
                        !response.message.success
                    ) {
                        throw new Error(
                            "Contact could not be deleted."
                        );
                    }

                    loadContacts();

                })
                .catch(function (error) {

                    console.error(
                        "ERP AI Delete Contact Error:",
                        error
                    );

                    deleteButton.disabled = false;
                    deleteButton.textContent = "🗑";

                    window.alert(
                        error.message ||
                        "Unable to delete contact."
                    );
                });
            }
        );

        elements.contactList.appendChild(item);
    });
}

function openAddContactForm() {
    const formHTML = `
        <div class="erp-ai-add-contact-overlay" id="erp-ai-add-contact-overlay">
            <div class="erp-ai-add-contact-modal">

                <div class="erp-ai-add-contact-header">
                    <div>
                        <div class="erp-ai-add-contact-title">
                            Add Contact
                        </div>

                        <div class="erp-ai-add-contact-subtitle">
                            Create a new person to chat with
                        </div>
                    </div>

                    <button
                        type="button"
                        class="erp-ai-add-contact-close"
                        id="erp-ai-add-contact-close"
                    >
                        ×
                    </button>
                </div>

                <div class="erp-ai-add-contact-body">

                    <label class="erp-ai-add-contact-label">
                        First Name
                    </label>

                    <input
                        type="text"
                        id="erp-ai-contact-first-name"
                        class="erp-ai-add-contact-input"
                        placeholder="Enter first name"
                    >

                    <label class="erp-ai-add-contact-label">
                        Last Name
                    </label>

                    <input
                        type="text"
                        id="erp-ai-contact-last-name"
                        class="erp-ai-add-contact-input"
                        placeholder="Enter last name"
                    >

                    <label class="erp-ai-add-contact-label">
                        Email
                    </label>

                    <input
                        type="email"
                        id="erp-ai-contact-email"
                        class="erp-ai-add-contact-input"
                        placeholder="Enter email"
                    >

                    <label class="erp-ai-add-contact-label">
                        Mobile Number
                    </label>

                    <input
                        type="text"
                        id="erp-ai-contact-mobile"
                        class="erp-ai-add-contact-input"
                        placeholder="Enter mobile number"
                    >

                    <div
                        class="erp-ai-add-contact-error"
                        id="erp-ai-add-contact-error"
                    ></div>

                    <button
                        type="button"
                        class="erp-ai-add-contact-save"
                        id="erp-ai-add-contact-save"
                    >
                        Add Contact
                    </button>

                </div>
            </div>
        </div>
    `;

    document.body.insertAdjacentHTML("beforeend", formHTML);

    const overlay = document.getElementById(
        "erp-ai-add-contact-overlay"
    );

    const closeButton = document.getElementById(
        "erp-ai-add-contact-close"
    );

    const saveButton = document.getElementById(
        "erp-ai-add-contact-save"
    );

    const errorBox = document.getElementById(
        "erp-ai-add-contact-error"
    );

    closeButton.addEventListener("click", function () {
        overlay.remove();
    });

    overlay.addEventListener("click", function (event) {
        if (event.target === overlay) {
            overlay.remove();
        }
    });

    saveButton.addEventListener("click", function () {
        const firstName = document
            .getElementById("erp-ai-contact-first-name")
            .value
            .trim();

        const lastName = document
            .getElementById("erp-ai-contact-last-name")
            .value
            .trim();

        const email = document
            .getElementById("erp-ai-contact-email")
            .value
            .trim();

        const mobileNo = document
            .getElementById("erp-ai-contact-mobile")
            .value
            .trim();

        errorBox.textContent = "";

        if (!firstName) {
            errorBox.textContent = "First Name is required.";
            return;
        }

        if (!email) {
            errorBox.textContent = "Email is required.";
            return;
        }

        saveButton.disabled = true;
        saveButton.textContent = "Creating...";

        frappe.call({
            method: "bk_account.api.chat.create_chat_contact",
            args: {
                first_name: firstName,
                last_name: lastName,
                email: email,
                mobile_no: mobileNo
            }
        })
        .then(function (response) {
            if (
                !response ||
                !response.message ||
                !response.message.success
            ) {
                throw new Error(
                    "Contact could not be created."
                );
            }

            overlay.remove();

            loadContacts();
        })
        .catch(function (error) {
            console.error(
                "ERP AI Create Contact Error:",
                error
            );

            errorBox.textContent =
                error.message ||
                "Unable to create contact.";

            saveButton.disabled = false;
            saveButton.textContent = "Add Contact";
        });
    });
}


function openPersonChat(contact) {

    if (!contact) {
        return;
    }

    if (!contact.user) {
        console.error(
            "ERP AI Person Chat: Contact has no linked User.",
            contact
        );

        frappe.msgprint(
            "This contact is not linked to a System User, so chat cannot be started."
        );

        return;
    }

    assistantState.currentPersonUser =
        contact.user;

    assistantState.currentPersonContact =
        contact;

    closeContacts();

    if (elements.personChat) {
        elements.personChat.classList.remove(
            "erp-ai-person-chat-hidden"
        );

        elements.personChat.style.display =
            "flex";
    }

    const firstName =
        contact.first_name || "";

    const lastName =
        contact.last_name || "";

    const fullName =
        (
            firstName +
            " " +
            lastName
        ).trim() ||
        contact.name ||
        "Contact";

    if (elements.personName) {
        elements.personName.textContent =
            fullName;
    }

    if (elements.personStatus) {
        elements.personStatus.textContent =
            contact.mobile_no ||
            contact.email_id ||
            "Contact";
    }

    if (elements.personMessages) {
        elements.personMessages.innerHTML = `
            <div class="erp-ai-person-empty">
                Loading conversation...
            </div>
        `;
    }

    loadPersonMessages();

    if (elements.personInput) {
        setTimeout(
            function () {
                elements.personInput.focus();
            },
            100
        );
    }
}

    function closePersonChat() {

        if (!elements.personChat) {
            return;
        }

        elements.personChat.classList.add(
            "erp-ai-person-chat-hidden"
        );

        elements.personChat.style.display =
            "none";

        if (elements.contactsButton) {
            elements.contactsButton.style.display =
                "flex";
        }
    }

    function loadPersonMessages() {


    if (!elements.personMessages) {
        return;
    }

    const otherUser =
        assistantState.currentPersonUser;

    if (!otherUser) {
        return;
    }

    elements.personMessages.innerHTML = `
        <div class="erp-ai-person-empty">
            Loading conversation...
        </div>
    `;

    frappe.call({
        method: "bk_account.api.chat.get_chat_messages",
        args: {
            other_user: otherUser,
            limit: 100
        }
    }).then(function (response) {

        const messages =
            response &&
            Array.isArray(response.message)
                ? response.message
                : [];


        renderPersonMessages(messages);

        frappe.call({
            method: "bk_account.api.chat.mark_messages_read",
            args: {
                other_user: otherUser
            }
        }).catch(function (error) {
            console.error(
                "ERP AI Mark Read Error:",
                error
            );
        });

    }).catch(function (error) {

        console.error(
            "ERP AI Load Person Messages Error:",
            error
        );

        elements.personMessages.innerHTML = `
            <div class="erp-ai-contacts-error">
                Unable to load conversation.
            </div>
        `;
    });
}


function renderPersonMessages(messages) {


    if (!elements.personMessages) {
        return;
    }

    if (
        !Array.isArray(messages) ||
        messages.length === 0
    ) {
        const contact =
            assistantState.currentPersonContact;

        const firstName =
            contact && contact.first_name
                ? contact.first_name
                : "";

        const lastName =
            contact && contact.last_name
                ? contact.last_name
                : "";

        const fullName =
            (
                firstName +
                " " +
                lastName
            ).trim() ||
            "this person";

        elements.personMessages.innerHTML = `
            <div class="erp-ai-person-empty">
                Start a conversation with ${escapeHTML(fullName)}.
            </div>
        `;

        return;
    }

    elements.personMessages.innerHTML = "";

    const currentUser =
        frappe.session.user;

    messages.forEach(function (item) {

        const messageElement =
            document.createElement("div");

        const isCurrentUser =
            item.sender === currentUser;

        messageElement.className =
            "erp-ai-person-message " +
            (
                isCurrentUser
                    ? "erp-ai-person-message-user"
                    : "erp-ai-person-message-other"
            );

        messageElement.textContent =
            item.message || "";

        elements.personMessages.appendChild(
            messageElement
        );
    });

    elements.personMessages.scrollTop =
        elements.personMessages.scrollHeight;
}


    function sendPersonMessage() {

    if (!elements.personInput) {
        return;
    }

    const message =
        elements.personInput.value.trim();

    if (!message) {
        return;
    }

    const receiver =
        assistantState.currentPersonUser;

    if (!receiver) {
        frappe.msgprint(
            "Please select a contact first."
        );

        return;
    }

    if (!elements.personMessages) {
        return;
    }

    const sendButton =
        elements.personSend;

    if (sendButton) {
        sendButton.disabled = true;
    }

    frappe.call({
        method: "bk_account.api.chat.send_chat_message",
        args: {
            receiver: receiver,
            message: message
        }
    }).then(function (response) {

        const savedMessage =
            response &&
            response.message
                ? response.message
                : null;

        if (!savedMessage) {
            throw new Error(
                "No message returned from server."
            );
        }

        const userMessage =
            document.createElement("div");

        userMessage.className =
            "erp-ai-person-message erp-ai-person-message-user";

        userMessage.textContent =
            savedMessage.message || message;

        elements.personMessages.appendChild(
            userMessage
        );

        elements.personInput.value = "";

        elements.personMessages.scrollTop =
            elements.personMessages.scrollHeight;

    }).catch(function (error) {

        console.error(
            "ERP AI Send Person Message Error:",
            error
        );

        frappe.msgprint(
            "Unable to send message."
        );

        if (sendButton) {
            sendButton.disabled = false;
        }

        if (elements.personInput) {
            elements.personInput.focus();
        }
    });
}

    function escapeHTML(value) {

        return String(value || "")
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }


    /* =========================================================
       ADD MESSAGE
       ========================================================= */

    function addMessage(
        message,
        type,
        showSpeaking
    ) {

        if (!elements.messages) {
            return;
        }

        /*
         * Safety:
         * Never allow objects to become [object Object].
         */
        if (
            message !== null &&
            typeof message === "object"
        ) {
            if (
                typeof message.answer === "string"
            ) {
                message = message.answer;
            } else if (
                typeof message.message === "string"
            ) {
                message = message.message;
            } else {
                message =
                    JSON.stringify(message);
            }
        }

        message =
            String(message || "");

        const row =
            document.createElement("div");

        row.className =
            "erp-ai-message-row " +
            (
                type === "user"
                    ? "erp-ai-message-user"
                    : "erp-ai-message-assistant"
            );

        const bubble =
            document.createElement("div");

        bubble.className =
            "erp-ai-message-bubble";

        const text =
            document.createElement("div");

        text.className =
            "erp-ai-message-text";

        text.textContent =
            message;

        bubble.appendChild(text);

        const meta =
            document.createElement("div");

        meta.className =
            "erp-ai-message-meta";

        const now =
            new Date();

        meta.textContent =
            now.toLocaleTimeString(
                [],
                {
                    hour: "2-digit",
                    minute: "2-digit"
                }
            );

        if (type === "user") {

            const ticks =
                document.createElement(
                    "span"
                );

            ticks.className =
                "erp-ai-message-ticks";

            ticks.textContent =
                " ✓✓";

            meta.appendChild(ticks);
        }

        bubble.appendChild(meta);

        row.appendChild(bubble);

        elements.messages.appendChild(row);

        scrollMessagesToBottom();

        if (
            type === "assistant" &&
            showSpeaking
        ) {
            speakText(message);
        }
    }

    /* =========================================================
       SCROLL
       ========================================================= */

    function scrollMessagesToBottom() {

        if (!elements.chatArea) {
            return;
        }

        setTimeout(
            function () {

                elements.chatArea.scrollTop =
                    elements.chatArea.scrollHeight;

            },
            30
        );
    }

    /* =========================================================
       TYPING MESSAGE
       ========================================================= */

    function addTypingMessage() {

        if (!elements.messages) {
            return;
        }

        removeTypingMessage();

        const row =
            document.createElement("div");

        row.className =
            "erp-ai-message-row erp-ai-message-assistant erp-ai-typing-row";

        row.id =
            "erp-ai-typing-message";

        const bubble =
            document.createElement("div");

        bubble.className =
            "erp-ai-message-bubble erp-ai-typing-bubble";

        bubble.innerHTML = `
            <span></span>
            <span></span>
            <span></span>
        `;

        row.appendChild(bubble);

        elements.messages.appendChild(row);

        scrollMessagesToBottom();
    }

    /* =========================================================
       REMOVE TYPING
       ========================================================= */

    function removeTypingMessage() {

        const typing =
            document.getElementById(
                "erp-ai-typing-message"
            );

        if (typing) {
            typing.remove();
        }
    }

    /* =========================================================
       ERP RESPONSE NORMALIZER
       ========================================================= */

    function getERPAnswer(response) {

        const message =
            response &&
            response.message;

        /*
         * ERPNext returns:
         *
         * {
         *     success: true,
         *     answer: "...",
         *     intent: {...},
         *     result: {...}
         * }
         *
         * Therefore we MUST use message.answer,
         * not message itself.
         */

        if (
            message &&
            typeof message === "object"
        ) {

            if (
                typeof message.answer === "string"
            ) {
                return message.answer;
            }

            if (
                typeof message.message === "string"
            ) {
                return message.message;
            }

            if (
                typeof message.error === "string"
            ) {
                return message.error;
            }

            return "No answer was returned from ERPNext.";
        }

        if (
            typeof message === "string"
        ) {
            return message;
        }

        return "I couldn't get a response from ERPNext.";
    }

    /* =========================================================
       VOICE QUESTION
       ========================================================= */

    function processVoiceQuestion(question) {

        if (
            !question ||
            assistantState.processingVoice
        ) {
            return;
        }

        assistantState.processingVoice =
            true;

        if (elements.callStatus) {
            elements.callStatus.textContent =
                "🤔 Thinking...";
        }

        if (elements.callMainStatus) {
            elements.callMainStatus.textContent =
                "🤔 Thinking...";
        }

        if (elements.callTranscript) {
            elements.callTranscript.textContent =
                "You: " + question;
        }

        /*
         * Also put recognized question into chat.
         */
        addMessage(
            question,
            "user"
        );

        if (elements.input) {
            elements.input.value = "";
        }

        addTypingMessage();

        frappe.call({
            method:
                "bk_account.api.erp_ai.ask_erp",

            args: {
                question:
                    question
            },

            callback:
                function (response) {

                    removeTypingMessage();

                    assistantState.processingVoice =
                        false;

                    const answer =
                        getERPAnswer(
                            response
                        );

                    addMessage(
                        answer,
                        "assistant",
                        false
                    );

                    if (elements.callTranscript) {
                        elements.callTranscript.textContent =
                            "ERP AI: " + answer;
                    }

                    if (elements.callStatus) {
                        elements.callStatus.textContent =
                            "Connected • Answer ready";
                    }

                    if (elements.callMainStatus) {
                        elements.callMainStatus.textContent =
                            "Answer ready";
                    }

                    /*
                     * Speak ERP answer.
                     */
                    if (
                        assistantState.callActive
                    ) {

                        speakText(
                            answer,
                            function () {

                                if (
                                    assistantState.callActive
                                ) {

                                    setTimeout(
                                        function () {

                                            if (
                                                assistantState.callActive
                                            ) {

                                                startListening(
                                                    true
                                                );

                                            }

                                        },
                                        400
                                    );

                                }

                            }
                        );

                    }

                    if (elements.sendButton) {
                        elements.sendButton.disabled =
                            false;
                    }

                    if (elements.input) {
                        elements.input.disabled =
                            false;
                    }
                },

            error:
                function () {

                    removeTypingMessage();

                    assistantState.processingVoice =
                        false;

                    const errorMessage =
                        "Sorry, I couldn't connect to ERPNext.";

                    addMessage(
                        errorMessage,
                        "assistant",
                        false
                    );

                    if (elements.callTranscript) {
                        elements.callTranscript.textContent =
                            errorMessage;
                    }

                    if (elements.callStatus) {
                        elements.callStatus.textContent =
                            "Connection error";
                    }

                    if (elements.callMainStatus) {
                        elements.callMainStatus.textContent =
                            "Connection error";
                    }

                    if (
                        assistantState.callActive
                    ) {

                        setTimeout(
                            function () {

                                if (
                                    assistantState.callActive
                                ) {
                                    startListening(
                                        true
                                    );
                                }

                            },
                            800
                        );
                    }

                    if (elements.sendButton) {
                        elements.sendButton.disabled =
                            false;
                    }

                    if (elements.input) {
                        elements.input.disabled =
                            false;
                    }
                }
        });
    }

    /* =========================================================
       NORMAL CHAT QUESTION
       ========================================================= */

    function sendQuestion(
        questionOverride
    ) {

        if (!elements.input) {
            return;
        }

        const question =
            typeof questionOverride === "string"
                ? questionOverride.trim()
                : elements.input.value.trim();

        if (!question) {
            return;
        }

        addMessage(
            question,
            "user"
        );

        elements.input.value = "";

        if (elements.sendButton) {
            elements.sendButton.disabled =
                true;
        }

        if (elements.input) {
            elements.input.disabled =
                true;
        }

        addTypingMessage();

        frappe.call({
            method:
                "bk_account.api.erp_ai.ask_erp",

            args: {
                question:
                    question
            },

            callback:
                function (response) {

                    removeTypingMessage();

                    const answer =
                        getERPAnswer(
                            response
                        );

                    addMessage(
                        answer,
                        "assistant",
                        assistantState.callActive
                    );

                    if (
                        assistantState.callActive
                    ) {

                        if (elements.callTranscript) {
                            elements.callTranscript.textContent =
                                "ERP AI: " + answer;
                        }
                    }

                    if (elements.sendButton) {
                        elements.sendButton.disabled =
                            false;
                    }

                    if (elements.input) {
                        elements.input.disabled =
                            false;

                        elements.input.focus();
                    }
                },

            error:
                function () {

                    removeTypingMessage();

                    addMessage(
                        "Sorry, I couldn't connect to ERPNext.",
                        "assistant",
                        false
                    );

                    if (elements.sendButton) {
                        elements.sendButton.disabled =
                            false;
                    }

                    if (elements.input) {
                        elements.input.disabled =
                            false;

                        elements.input.focus();
                    }
                }
        });
    }

    /* =========================================================
       SPEECH RECOGNITION
       ========================================================= */

    function initSpeechRecognition() {

        const SpeechRecognition =
            window.SpeechRecognition ||
            window.webkitSpeechRecognition;

        if (!SpeechRecognition) {

            assistantState.speechSupported =
                false;

            return;
        }

        assistantState.speechSupported =
            true;

        assistantState.recognition =
            new SpeechRecognition();

        assistantState.recognition.continuous =
            false;

        assistantState.recognition.interimResults =
            false;

        assistantState.recognition.lang =
            "en-IN";

        assistantState.recognition.onstart =
            function () {

                assistantState.listening =
                    true;

                updateCallListeningUI();

                if (elements.callStatus) {
                    elements.callStatus.textContent =
                        "Listening...";
                }

                if (elements.callMainStatus) {
                    elements.callMainStatus.textContent =
                        "I'm listening";
                }

                if (elements.callTranscript) {
                    elements.callTranscript.textContent =
                        "I'm listening. Tell me what you want to do in ERPNext.";
                }
            };

        assistantState.recognition.onresult =
            function (event) {

                let transcript =
                    "";

                for (
                    let i = event.resultIndex;
                    i < event.results.length;
                    i++
                ) {

                    transcript +=
                        event.results[i][0].transcript;
                }

                transcript =
                    transcript.trim();

                assistantState.listening =
                    false;

                updateCallListeningUI();

                if (transcript) {
                    processVoiceQuestion(
                        transcript
                    );
                }
            };

        assistantState.recognition.onerror =
            function (event) {

                assistantState.listening =
                    false;

                updateCallListeningUI();

                if (
                    elements.callStatus
                ) {

                    if (
                        event.error ===
                        "not-allowed"
                    ) {

                        elements.callStatus.textContent =
                            "Microphone permission denied";

                    } else {

                        elements.callStatus.textContent =
                            "Voice error. Try again.";

                    }
                }

                if (
                    elements.callMainStatus
                ) {

                    elements.callMainStatus.textContent =
                        "Voice error";

                }
            };

        assistantState.recognition.onend =
            function () {

                assistantState.listening =
                    false;

                updateCallListeningUI();

            };
    }

    /* =========================================================
       START LISTENING
       ========================================================= */

    function startListening(
        showMessage
    ) {

        if (
            !assistantState.speechSupported ||
            !assistantState.recognition
        ) {

            if (elements.callStatus) {
                elements.callStatus.textContent =
                    "Voice recognition is not supported by this browser.";
            }

            if (elements.callMainStatus) {
                elements.callMainStatus.textContent =
                    "Voice not supported";
            }

            return;
        }

        if (
            assistantState.processingVoice
        ) {
            return;
        }

        stopSpeaking();

        try {

            assistantState.recognition.start();

        } catch (error) {

            /*
             * Browser throws InvalidStateError
             * if recognition is already running.
             */
        }
    }

    /* =========================================================
       STOP LISTENING
       ========================================================= */

    function stopListening() {

        if (
            assistantState.recognition
        ) {

            try {
                assistantState.recognition.stop();
            } catch (error) {
                // Ignore browser recognition stop errors.
            }
        }

        assistantState.listening =
            false;

        updateCallListeningUI();
    }

    /* =========================================================
       UPDATE CALL LISTENING UI
       ========================================================= */

    function updateCallListeningUI() {

        if (elements.callMic) {

            elements.callMic.classList.toggle(
                "erp-ai-call-mic-active",
                assistantState.listening
            );
        }

        if (
            elements.callWaveform
        ) {

            elements.callWaveform.classList.toggle(
                "erp-ai-wave-active",
                assistantState.listening ||
                assistantState.speaking
            );
        }

        if (
            elements.callAvatarLarge
        ) {

            elements.callAvatarLarge.classList.toggle(
                "erp-ai-avatar-speaking",
                assistantState.speaking
            );
        }
    }

    /* =========================================================
       START CALL
       ========================================================= */

    function startCall() {

        if (
            !assistantState.speechSupported
        ) {

            if (elements.callStatus) {
                elements.callStatus.textContent =
                    "Voice recognition is not supported by this browser.";
            }
        }

        assistantState.callActive =
            true;

        assistantState.processingVoice =
            false;

        stopSpeaking();

        if (elements.callPanel) {

            elements.callPanel.classList.remove(
                "erp-ai-call-hidden"
            );

            elements.callPanel.style.display =
                "flex";
        }

        if (elements.callStatus) {
            elements.callStatus.textContent =
                "Connected • Speak now";
        }

        if (elements.callMainStatus) {
            elements.callMainStatus.textContent =
                "Connected";
        }

        if (elements.callTranscript) {
            elements.callTranscript.textContent =
                "I'm listening. Tell me what you want to do in ERPNext.";
        }

        startCallTimer();

        setTimeout(
            function () {

                startListening(
                    true
                );

            },
            400
        );
    }

    /* =========================================================
       END CALL
       ========================================================= */

    function endCall() {

        assistantState.callActive =
            false;

        assistantState.processingVoice =
            false;

        stopListening();
        stopSpeaking();
        stopCallTimer();

        if (elements.callPanel) {

            elements.callPanel.classList.add(
                "erp-ai-call-hidden"
            );

            elements.callPanel.style.display =
                "none";
        }

        if (elements.callStatus) {
            elements.callStatus.textContent =
                "Ready to talk";
        }

        if (elements.callMainStatus) {
            elements.callMainStatus.textContent =
                "Ready to talk";
        }

        if (elements.callTranscript) {
            elements.callTranscript.textContent =
                "Press the microphone to start speaking.";
        }

        if (elements.callTimer) {
            elements.callTimer.textContent =
                "00:00";
        }

        assistantState.callSeconds =
            0;
    }

    /* =========================================================
       CALL TIMER
       ========================================================= */

    function startCallTimer() {

        stopCallTimer();

        assistantState.callSeconds =
            0;

        updateCallTimer();

        assistantState.callTimer =
            setInterval(
                function () {

                    assistantState.callSeconds++;

                    updateCallTimer();

                },
                1000
            );
    }

    function stopCallTimer() {

        if (
            assistantState.callTimer
        ) {

            clearInterval(
                assistantState.callTimer
            );

            assistantState.callTimer =
                null;
        }
    }

    function updateCallTimer() {

        if (!elements.callTimer) {
            return;
        }

        const minutes =
            Math.floor(
                assistantState.callSeconds /
                60
            );

        const seconds =
            assistantState.callSeconds %
            60;

        elements.callTimer.textContent =
            String(minutes).padStart(
                2,
                "0"
            ) +
            ":" +
            String(seconds).padStart(
                2,
                "0"
            );
    }

    /* =========================================================
       SPEECH SYNTHESIS
       ========================================================= */

    function speakText(
        text,
        onComplete
    ) {

        if (
            !window.speechSynthesis
        ) {

            if (onComplete) {
                onComplete();
            }

            return;
        }

        stopSpeaking();

        const utterance =
            new SpeechSynthesisUtterance(
                String(text || "")
            );

        utterance.lang =
            "en-IN";

        utterance.rate =
            0.95;

        utterance.pitch =
            1;

        assistantState.speaking =
            true;

        updateCallListeningUI();

        if (
            elements.callStatus
        ) {

            elements.callStatus.textContent =
                "AI is speaking...";
        }

        if (
            elements.callMainStatus
        ) {

            elements.callMainStatus.textContent =
                "AI is speaking";
        }

        utterance.onend =
            function () {

                assistantState.speaking =
                    false;

                assistantState.speakingTimer =
                    null;

                updateCallListeningUI();

                if (
                    elements.callStatus
                ) {

                    elements.callStatus.textContent =
                        assistantState.callActive
                            ? "Connected • Speak now"
                            : "Ready to talk";
                }

                if (
                    elements.callMainStatus
                ) {

                    elements.callMainStatus.textContent =
                        assistantState.callActive
                            ? "Your turn"
                            : "Ready to talk";
                }

                if (onComplete) {
                    onComplete();
                }
            };

        utterance.onerror =
            function () {

                assistantState.speaking =
                    false;

                assistantState.speakingTimer =
                    null;

                updateCallListeningUI();

                if (onComplete) {
                    onComplete();
                }
            };

        window.speechSynthesis.speak(
            utterance
        );
    }

    /* =========================================================
       STOP SPEAKING
       ========================================================= */

    function stopSpeaking() {

        if (
            window.speechSynthesis
        ) {

            try {
                window.speechSynthesis.cancel();
            } catch (error) {
                // Ignore speech synthesis errors.
            }
        }

        assistantState.speaking =
            false;

        updateCallListeningUI();
    }

    /* =========================================================
       START ON DOM READY
       ========================================================= */

    if (
        document.readyState ===
        "loading"
    ) {

        document.addEventListener(
            "DOMContentLoaded",
            initERPAssistant
        );

    } else {

        initERPAssistant();

    }

})();


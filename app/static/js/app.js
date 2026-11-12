// BiztelAI Shop Floor Copilot - Clean Minimal UI

document.addEventListener("DOMContentLoaded", () => {
    const queryForm = document.getElementById("queryForm");
    const questionInput = document.getElementById("questionInput");
    const submitBtn = document.getElementById("submitBtn");
    const voiceBtn = document.getElementById("voiceBtn");

    const resultCard = document.getElementById("resultCard");
    const loadingBox = document.getElementById("loadingBox");
    const revisionAlertBanner = document.getElementById("revisionAlertBanner");
    const answerBody = document.getElementById("answerBody");
    const citationsSection = document.getElementById("citationsSection");
    const citationsList = document.getElementById("citationsList");

    queryForm.addEventListener("submit", (e) => {
        e.preventDefault();
        const q = questionInput.value.trim();
        if (q) submitQuery(q);
    });

    async function submitQuery(question) {
        resultCard.classList.add("hidden");
        loadingBox.classList.remove("hidden");
        submitBtn.disabled = true;

        try {
            const res = await fetch("/api/query", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ question, provider: "auto" })
            });

            const data = await res.json();
            renderResponse(data);
        } catch (err) {
            console.error(err);
            renderError("Network error. Could not connect to copilot server.");
        } finally {
            loadingBox.classList.add("hidden");
            resultCard.classList.remove("hidden");
            submitBtn.disabled = false;
        }
    }

    function renderResponse(data) {
        // Revision Warning Banner (only displayed if a document is superseded)
        if (data.revision_alert && data.revision_alert.type === "warning") {
            revisionAlertBanner.classList.remove("hidden");
            revisionAlertBanner.className = "alert-banner superseded-revision";
            revisionAlertBanner.innerHTML = formatMarkdown(data.revision_alert.message);
        } else {
            revisionAlertBanner.classList.add("hidden");
        }

        // Answer Body
        answerBody.innerHTML = formatMarkdown(data.answer);

        // Source Citation
        citationsList.innerHTML = "";
        if (data.citations && data.citations.length > 0) {
            data.citations.forEach(c => {
                const badge = document.createElement("div");
                badge.className = "citation-badge";
                badge.innerHTML = `<strong>${c.doc_id} (${c.revision})</strong> &bull; ${c.section_number}: ${c.section_title} &bull; Page ${c.page_number}`;
                citationsList.appendChild(badge);
            });
            citationsSection.classList.remove("hidden");
        } else {
            citationsSection.classList.add("hidden");
        }
    }

    function renderError(msg) {
        revisionAlertBanner.classList.add("hidden");
        answerBody.innerHTML = `<span style="color: #dc2626;">${msg}</span>`;
        citationsSection.classList.add("hidden");
    }

    function formatMarkdown(text) {
        if (!text) return "";
        let html = escapeHtml(text);

        // Bold
        html = html.replace(/\*\*(.*?)\*\*/g, "<strong>$1</strong>");

        // Italics
        html = html.replace(/\*(.*?)\*/g, "<em>$1</em>");

        // Bullet lists
        html = html.replace(/^\s*-\s+(.*)$/gm, "<li>$1</li>");
        html = html.replace(/(<li>.*<\/li>)/s, "<ul>$1</ul>");

        // Numbered lists
        html = html.replace(/^\s*(\d+)\.\s+(.*)$/gm, "<li><strong>$1.</strong> $2</li>");

        // Line breaks
        html = html.replace(/\n\n/g, "<br><br>");
        return html;
    }

    function escapeHtml(string) {
        const entityMap = {
            "&": "&amp;",
            "<": "&lt;",
            ">": "&gt;",
            '"': '&quot;',
            "'": '&#39;'
        };
        return String(string).replace(/[&<>"']/g, s => entityMap[s]);
    }

    // Voice Input (Speech to Text)
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = false;
        recognition.lang = "en-US";

        let recognizing = false;

        voiceBtn.addEventListener("click", () => {
            if (recognizing) {
                recognition.stop();
                return;
            }
            try {
                recognition.start();
                recognizing = true;
                voiceBtn.classList.add("active");
                questionInput.placeholder = "Listening... Speak your question";
            } catch (err) {
                console.error("Speech recognition error:", err);
            }
        });

        recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            questionInput.value = transcript;
            submitQuery(transcript);
        };

        recognition.onend = () => {
            recognizing = false;
            voiceBtn.classList.remove("active");
            questionInput.placeholder = "Ask a question (e.g. AL-104 alarm, coolant concentration, bearing tolerance)...";
        };
    } else {
        voiceBtn.style.display = "none";
    }
});

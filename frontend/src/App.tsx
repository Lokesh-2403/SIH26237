import React, { useEffect, useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";


type Recipient = {
  recipient_id: string;
  name: string;
  email: string;
  has_signing_private_key?: boolean;
  has_kem_private_key?: boolean;
  has_kem_public_key?: boolean;
};

type Page =
  | "dashboard"
  | "protect"
  | "decrypt"
  | "investigate"
  | "ledger";

function App() {
  const [page, setPage] = useState<Page>("dashboard");

  return (
    <div className="app">
      <style>{`
        * {
          box-sizing: border-box;
        }

        body {
          margin: 0;
          font-family: Arial, Helvetica, sans-serif;
          background: #f5f7fb;
          color: #172033;
        }

        button,
        input {
          font: inherit;
        }

        button {
          cursor: pointer;
        }

        .app {
          min-height: 100vh;
        }

        .topbar {
          background: #172033;
          color: white;
          padding: 18px 32px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }

        .brand {
          font-size: 22px;
          font-weight: 700;
        }

        .brand-subtitle {
          font-size: 12px;
          opacity: 0.7;
          margin-top: 3px;
        }

        .page-container {
          max-width: 1100px;
          margin: 0 auto;
          padding: 32px 20px 60px;
        }

        .nav {
          display: flex;
          gap: 8px;
          flex-wrap: wrap;
        }

        .nav button {
          border: none;
          background: rgba(255,255,255,0.08);
          color: white;
          padding: 9px 13px;
          border-radius: 7px;
        }

        .nav button:hover {
          background: rgba(255,255,255,0.16);
        }

        .nav button.active {
          background: white;
          color: #172033;
        }

        .page-title {
          margin: 0 0 8px;
          font-size: 30px;
        }

        .page-description {
          margin: 0 0 28px;
          color: #647084;
        }

        .card {
          background: white;
          border: 1px solid #e1e6ef;
          border-radius: 12px;
          padding: 24px;
          margin-bottom: 20px;
          box-shadow: 0 2px 8px rgba(20, 30, 50, 0.04);
        }

        .card h2 {
          margin-top: 0;
          margin-bottom: 8px;
        }

        .card-description {
          color: #687386;
          margin-top: 0;
        }

        .form-group {
          margin-bottom: 20px;
        }

        .form-group label {
          display: block;
          font-weight: 600;
          margin-bottom: 8px;
        }

        input[type="text"],
        input[type="email"] {
          width: 100%;
          padding: 12px 14px;
          border: 1px solid #cfd6e2;
          border-radius: 8px;
          outline: none;
          background: white;
        }

        input[type="text"]:focus,
        input[type="email"]:focus {
          border-color: #3b82f6;
        }

        input[type="file"] {
          width: 100%;
          padding: 12px;
          border: 1px dashed #b9c3d2;
          border-radius: 8px;
          background: #fafbfc;
        }

        .file-info {
          margin-top: 10px;
          padding: 12px;
          background: #f3f6fa;
          border-radius: 8px;
          color: #4c586b;
        }

        .recipient-list {
          display: flex;
          flex-direction: column;
          gap: 10px;
        }

        .recipient-item {
          display: flex;
          align-items: center;
          gap: 12px;
          padding: 13px 14px;
          border: 1px solid #dce2eb;
          border-radius: 9px;
          background: #fff;
        }

        .recipient-item:hover {
          background: #f8fafc;
        }

        .recipient-item input {
          width: 18px;
          height: 18px;
        }

        .recipient-details {
          flex: 1;
        }

        .recipient-name {
          font-weight: 700;
        }

        .recipient-meta {
          font-size: 13px;
          color: #697487;
          margin-top: 3px;
        }

        .add-recipient-grid {
          display: grid;
          grid-template-columns: 1fr 1fr 1fr auto;
          gap: 10px;
          align-items: end;
        }

        .button {
          border: none;
          border-radius: 8px;
          padding: 11px 17px;
          font-weight: 600;
        }

        .button-primary {
          background: #2563eb;
          color: white;
        }

        .button-primary:hover {
          background: #1d4ed8;
        }

        .button-secondary {
          background: #e9eef5;
          color: #263246;
        }

        .button-secondary:hover {
          background: #dfe6ef;
        }

        .button-danger {
          background: #dc2626;
          color: white;
        }

        .button:disabled {
          opacity: 0.55;
          cursor: not-allowed;
        }

        .actions {
          display: flex;
          gap: 10px;
          flex-wrap: wrap;
          margin-top: 20px;
        }

        .message {
          padding: 13px 15px;
          border-radius: 8px;
          margin-bottom: 20px;
          background: #ecfdf3;
          border: 1px solid #b7ebca;
          color: #166534;
        }

        .error {
          padding: 13px 15px;
          border-radius: 8px;
          margin-bottom: 20px;
          background: #fff1f2;
          border: 1px solid #fecdd3;
          color: #be123c;
        }

        .result-card {
          margin-top: 20px;
          padding: 20px;
          border: 1px solid #b7ebca;
          background: #f0fdf4;
          border-radius: 10px;
        }

        .result-label {
          display: block;
          font-size: 12px;
          text-transform: uppercase;
          letter-spacing: 0.05em;
          color: #4b6352;
          margin-bottom: 7px;
        }

        .document-id {
          display: block;
          font-size: 20px;
          word-break: break-all;
          color: #166534;
          background: white;
          border: 1px solid #cce7d3;
          border-radius: 7px;
          padding: 12px;
        }

        .authorized-result {
          margin-top: 15px;
          color: #365342;
        }

        .empty-state {
          padding: 20px;
          text-align: center;
          color: #697487;
          background: #f8fafc;
          border-radius: 8px;
        }

        .dashboard-grid {
          display: grid;
          grid-template-columns: repeat(2, 1fr);
          gap: 18px;
        }

        .dashboard-card {
          background: white;
          border: 1px solid #e1e6ef;
          border-radius: 12px;
          padding: 22px;
          cursor: pointer;
          transition: transform 0.15s ease, box-shadow 0.15s ease;
        }

        .dashboard-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 5px 15px rgba(20, 30, 50, 0.08);
        }

        .dashboard-card h3 {
          margin-top: 0;
        }

        .dashboard-card p {
          color: #687386;
          line-height: 1.5;
        }

        .section-title {
          margin-top: 0;
          margin-bottom: 14px;
        }

        .back-button {
          margin-bottom: 20px;
        }

        .loading {
          opacity: 0.7;
        }

        .small-note {
          color: #6b7280;
          font-size: 13px;
          margin-top: 8px;
        }

        .stat-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 15px;
        }

        .stat {
          background: #f8fafc;
          border: 1px solid #e5eaf1;
          border-radius: 9px;
          padding: 16px;
        }

        .stat-number {
          font-size: 25px;
          font-weight: 700;
        }

        .stat-label {
          color: #687386;
          margin-top: 4px;
          font-size: 13px;
        }

        .ledger-table {
          width: 100%;
          border-collapse: collapse;
        }

        .ledger-table th,
        .ledger-table td {
          padding: 12px;
          border-bottom: 1px solid #e5eaf1;
          text-align: left;
          font-size: 14px;
        }

        .ledger-table th {
          background: #f8fafc;
        }

        .code-value {
          font-family: monospace;
          word-break: break-all;
        }

        @media (max-width: 800px) {
          .topbar {
            flex-direction: column;
            align-items: flex-start;
            gap: 15px;
          }

          .dashboard-grid {
            grid-template-columns: 1fr;
          }

          .add-recipient-grid {
            grid-template-columns: 1fr;
          }

          .stat-grid {
            grid-template-columns: 1fr;
          }
        }
      `}</style>

      <header className="topbar">
        <div>
          <div className="brand">Secure Document Distribution</div>
          <div className="brand-subtitle">
            SIH26237 • Post-Quantum Secure Document System
          </div>
        </div>

        <nav className="nav">
          <button
            className={page === "dashboard" ? "active" : ""}
            onClick={() => setPage("dashboard")}
          >
            Dashboard
          </button>

          <button
            className={page === "protect" ? "active" : ""}
            onClick={() => setPage("protect")}
          >
            Protect
          </button>

          <button
            className={page === "decrypt" ? "active" : ""}
            onClick={() => setPage("decrypt")}
          >
            Decrypt
          </button>

          <button
            className={page === "investigate" ? "active" : ""}
            onClick={() => setPage("investigate")}
          >
            Investigate
          </button>

          <button
            className={page === "ledger" ? "active" : ""}
            onClick={() => setPage("ledger")}
          >
            Ledger
          </button>
        </nav>
      </header>

      <main className="page-container">
        {page === "dashboard" && <Dashboard setPage={setPage} />}
        {page === "protect" && <ProtectPage setPage={setPage} />}
        {page === "decrypt" && <DecryptPage setPage={setPage} />}
        {page === "investigate" && <InvestigatePage setPage={setPage} />}
        {page === "ledger" && <LedgerPage setPage={setPage} />}
      </main>
    </div>
  );
}

/* =========================================================
   DASHBOARD
========================================================= */

function Dashboard({ setPage }: { setPage: (page: Page) => void }) {
  return (
    <>
      <h1 className="page-title">Dashboard</h1>
      <p className="page-description">
        Secure document protection, recipient authorization, decryption and
        investigation.
      </p>

      <div className="dashboard-grid">
        <div className="dashboard-card" onClick={() => setPage("protect")}>
          <h3>🔐 Protect Document</h3>
          <p>
            Upload a PDF, select the recipients who are authorized to decrypt
            it, and protect the document.
          </p>
        </div>

        <div className="dashboard-card" onClick={() => setPage("decrypt")}>
          <h3>🔓 Decrypt Document</h3>
          <p>
            An authorized recipient can decrypt a document using the Document
            ID and Recipient ID.
          </p>
        </div>

        <div
          className="dashboard-card"
          onClick={() => setPage("investigate")}
        >
          <h3>🔎 Investigate Document</h3>
          <p>
            Upload a decrypted or leaked PDF and inspect its embedded
            watermark and investigation information.
          </p>
        </div>

        <div className="dashboard-card" onClick={() => setPage("ledger")}>
          <h3>📋 Audit Ledger</h3>
          <p>
            View the audit information recorded for document protection and
            decryption operations.
          </p>
        </div>
      </div>
    </>
  );
}

/* =========================================================
   PROTECT PAGE
========================================================= */

function ProtectPage({ setPage }: { setPage: (page: Page) => void }) {
  const [file, setFile] = useState<File | null>(null);

  const [recipients, setRecipients] = useState<Recipient[]>([]);
  const [selectedRecipients, setSelectedRecipients] = useState<string[]>([]);

  const [recipientId, setRecipientId] = useState("");
  const [recipientName, setRecipientName] = useState("");
  const [recipientEmail, setRecipientEmail] = useState("");

  const [loadingRecipients, setLoadingRecipients] = useState(false);
  const [addingRecipient, setAddingRecipient] = useState(false);
  const [loading, setLoading] = useState(false);

  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [documentId, setDocumentId] = useState("");

  useEffect(() => {
    loadRecipients();
  }, []);

  const loadRecipients = async () => {
    setLoadingRecipients(true);
    setError("");

    try {
      const response = await fetch(`${API_BASE}/recipients`);

      if (!response.ok) {
        throw new Error("Failed to load recipients.");
      }

      const data = await response.json();

      setRecipients(Array.isArray(data) ? data : []);
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load recipients."
      );
    } finally {
      setLoadingRecipients(false);
    }
  };

  const handleFileChange = (
    event: React.ChangeEvent<HTMLInputElement>
  ) => {
    const selectedFile = event.target.files?.[0] || null;

    setFile(selectedFile);
    setMessage("");
    setError("");
    setDocumentId("");
  };

  const toggleRecipient = (id: string) => {
    setSelectedRecipients((current) => {
      if (current.includes(id)) {
        return current.filter((recipientId) => recipientId !== id);
      }

      return [...current, id];
    });

    setMessage("");
    setError("");
  };

  const addRecipient = async () => {
    setError("");
    setMessage("");

    const trimmedId = recipientId.trim();
    const trimmedName = recipientName.trim();
    const trimmedEmail = recipientEmail.trim();

    if (!trimmedId || !trimmedName || !trimmedEmail) {
      setError("Recipient ID, name and email are required.");
      return;
    }

    setAddingRecipient(true);

    try {
      const formData = new FormData();

      formData.append("recipient_id", trimmedId);
      formData.append("name", trimmedName);
      formData.append("email", trimmedEmail);

      const response = await fetch(`${API_BASE}/recipients`, {
        method: "POST",
        body: formData,
      });

      let data: any = null;

      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            data?.message ||
            "Failed to add recipient."
        );
      }

      const newRecipient: Recipient = {
        recipient_id:
          data?.recipient_id ||
          data?.recipient?.recipient_id ||
          trimmedId,
        name:
          data?.name ||
          data?.recipient?.name ||
          trimmedName,
        email:
          data?.email ||
          data?.recipient?.email ||
          trimmedEmail,
        has_signing_private_key: true,
        has_kem_private_key: true,
        has_kem_public_key: true,
      };

      setRecipients((current) => {
        const alreadyExists = current.some(
          (recipient) =>
            recipient.recipient_id === newRecipient.recipient_id
        );

        if (alreadyExists) {
          return current.map((recipient) =>
            recipient.recipient_id === newRecipient.recipient_id
              ? { ...recipient, ...newRecipient }
              : recipient
          );
        }

        return [...current, newRecipient];
      });

      setSelectedRecipients((current) => [
        ...current.filter(
          (id) => id !== newRecipient.recipient_id
        ),
        newRecipient.recipient_id,
      ]);

      setRecipientId("");
      setRecipientName("");
      setRecipientEmail("");

      setMessage(
        `Recipient ${newRecipient.recipient_id} added and authorized for this document.`
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to add recipient."
      );
    } finally {
      setAddingRecipient(false);
    }
  };

  /*
   * IMPORTANT:
   *
   * /protect returns JSON metadata.
   * It does NOT return the protected PDF.
   *
   * Therefore we parse response.json() and display the
   * Document ID returned by the backend.
   */
  const protectDocument = async () => {
    setError("");
    setMessage("");
    setDocumentId("");

    if (!file) {
      setError("Please select a PDF document first.");
      return;
    }

    if (
      file.type !== "application/pdf" &&
      !file.name.toLowerCase().endsWith(".pdf")
    ) {
      setError("Only PDF documents are supported.");
      return;
    }

    if (selectedRecipients.length === 0) {
      setError("Please authorize at least one recipient.");
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();

      formData.append("file", file);

      /*
       * Backend expects comma-separated recipient IDs.
       */
      formData.append(
        "recipient_ids",
        selectedRecipients.join(",")
      );

      const response = await fetch(`${API_BASE}/protect`, {
        method: "POST",
        body: formData,
      });

      let data: any = null;

      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            data?.message ||
            "Document protection failed."
        );
      }

      /*
       * Backend returns document_id.
       *
       * Support both document_id and documentId
       * just in case the response naming changes.
       */
      const returnedDocumentId =
        data?.document_id ||
        data?.documentId ||
        data?.id ||
        "";

      if (!returnedDocumentId) {
        throw new Error(
          "Document was protected, but the backend did not return a Document ID."
        );
      }

      setDocumentId(String(returnedDocumentId));

      setMessage(
        "Document protected successfully. Save the Document ID for decryption."
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Document protection failed."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        className="button button-secondary back-button"
        onClick={() => setPage("dashboard")}
      >
        ← Back to Dashboard
      </button>

      <h1 className="page-title">Protect Document</h1>

      <p className="page-description">
        Encrypt a PDF and authorize only selected recipients to decrypt it.
      </p>

      {message && <div className="message">✓ {message}</div>}

      {error && <div className="error">⚠ {error}</div>}

      <div className="card">
        <h2>1. Select Document</h2>

        <p className="card-description">
          Select the PDF that should be protected.
        </p>

        <div className="form-group">
          <label htmlFor="pdf-file">PDF Document</label>

          <input
            id="pdf-file"
            type="file"
            accept=".pdf,application/pdf"
            onChange={handleFileChange}
          />

          {file && (
            <div className="file-info">
              <strong>{file.name}</strong>{" "}
              <span>
                {(file.size / 1024).toFixed(1)} KB
              </span>
            </div>
          )}
        </div>
      </div>

      <div className="card">
        <h2>2. Authorize Recipients</h2>

        <p className="card-description">
          Only the recipients selected below will be allowed to decrypt this
          document.
        </p>

        {loadingRecipients ? (
          <div className="empty-state">
            Loading recipients...
          </div>
        ) : recipients.length === 0 ? (
          <div className="empty-state">
            No recipients registered yet.
          </div>
        ) : (
          <div className="recipient-list">
            {recipients.map((recipient) => (
              <label
                className="recipient-item"
                key={recipient.recipient_id}
              >
                <input
                  type="checkbox"
                  checked={selectedRecipients.includes(
                    recipient.recipient_id
                  )}
                  onChange={() =>
                    toggleRecipient(recipient.recipient_id)
                  }
                />

                <div className="recipient-details">
                  <div className="recipient-name">
                    {recipient.name}
                  </div>

                  <div className="recipient-meta">
                    {recipient.recipient_id} • {recipient.email}
                  </div>
                </div>
              </label>
            ))}
          </div>
        )}

        <p className="small-note">
          Selected recipients: {selectedRecipients.length}
        </p>
      </div>

      <div className="card">
        <h2>3. Add Recipient</h2>

        <p className="card-description">
          Register a new recipient. The newly added recipient will
          automatically be selected for this document.
        </p>

        <div className="add-recipient-grid">
          <div className="form-group" style={{ marginBottom: 0 }}>
            <label htmlFor="recipient-id">
              Recipient ID
            </label>

            <input
              id="recipient-id"
              type="text"
              placeholder="OFFICER-004"
              value={recipientId}
              onChange={(event) =>
                setRecipientId(event.target.value)
              }
            />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label htmlFor="recipient-name">
              Name
            </label>

            <input
              id="recipient-name"
              type="text"
              placeholder="Officer D"
              value={recipientName}
              onChange={(event) =>
                setRecipientName(event.target.value)
              }
            />
          </div>

          <div className="form-group" style={{ marginBottom: 0 }}>
            <label htmlFor="recipient-email">
              Email
            </label>

            <input
              id="recipient-email"
              type="email"
              placeholder="officerD@gov.in"
              value={recipientEmail}
              onChange={(event) =>
                setRecipientEmail(event.target.value)
              }
            />
          </div>

          <button
            className="button button-secondary"
            onClick={addRecipient}
            disabled={addingRecipient}
          >
            {addingRecipient ? "Adding..." : "Add Recipient"}
          </button>
        </div>
      </div>

      <div className="card">
        <h2>4. Protect & Distribute</h2>

        <p className="card-description">
          The document will be encrypted and stored securely. The backend will
          return a Document ID. No protected PDF download is required.
        </p>

        <div className="actions">
          <button
            className="button button-primary"
            onClick={protectDocument}
            disabled={
              loading ||
              !file ||
              selectedRecipients.length === 0
            }
          >
            {loading
              ? "Protecting Document..."
              : "Protect & Distribute"}
          </button>
        </div>

        {documentId && (
          <div className="result-card">
            <span className="result-label">
              Document ID
            </span>

            <strong className="document-id">
              {documentId}
            </strong>

            <p>
              Keep this Document ID. An authorized recipient needs
              this ID together with their Recipient ID to decrypt the
              document.
            </p>

            <div className="authorized-result">
              <strong>
                Authorized recipients:
              </strong>{" "}
              {selectedRecipients.length}
            </div>

            <div className="authorized-result">
              <strong>Recipient IDs:</strong>{" "}
              {selectedRecipients.join(", ")}
            </div>
          </div>
        )}
      </div>
    </>
  );
}

/* =========================================================
   DECRYPT PAGE
========================================================= */

function DecryptPage({ setPage }: { setPage: (page: Page) => void }) {
  const [documentId, setDocumentId] = useState("");
  const [recipientId, setRecipientId] = useState("");

  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");

  const [sessionId, setSessionId] = useState("");
  const [watermarkId, setWatermarkId] = useState("");

  const getFilenameFromResponse = (
    response: Response
  ): string | null => {
    const contentDisposition =
      response.headers.get("content-disposition");

    if (!contentDisposition) {
      return null;
    }

    const utf8Match = contentDisposition.match(
      /filename\*=UTF-8''([^;]+)/i
    );

    if (utf8Match?.[1]) {
      try {
        return decodeURIComponent(utf8Match[1]);
      } catch {
        return utf8Match[1];
      }
    }

    const filenameMatch = contentDisposition.match(
      /filename="?([^"]+)"?/i
    );

    return filenameMatch?.[1] || null;
  };

  const decryptDocument = async () => {
    setError("");
    setMessage("");
    setSessionId("");
    setWatermarkId("");

    const trimmedDocumentId = documentId.trim();
    const trimmedRecipientId = recipientId.trim();

    if (!trimmedDocumentId) {
      setError("Please enter the Document ID.");
      return;
    }

    if (!trimmedRecipientId) {
      setError("Please enter the Recipient ID.");
      return;
    }

    setLoading(true);

    try {
      const url =
        `${API_BASE}/decrypt/` +
        `${encodeURIComponent(trimmedDocumentId)}` +
        `?recipient_id=${encodeURIComponent(trimmedRecipientId)}`;

      const response = await fetch(url, {
        method: "GET",
      });

      if (!response.ok) {
        let errorMessage =
          "Document decryption failed.";

        try {
          const data = await response.json();

          errorMessage =
            data?.detail ||
            data?.message ||
            errorMessage;
        } catch {
          // Keep default message.
        }

        if (response.status === 403) {
          errorMessage =
            "This recipient is not authorized to decrypt this document.";
        }

        throw new Error(errorMessage);
      }

      const blob = await response.blob();

      if (blob.size === 0) {
        throw new Error(
          "The server returned an empty document."
        );
      }

      const filename =
        getFilenameFromResponse(response) ||
        "decrypted_document.pdf";

      const downloadUrl =
        window.URL.createObjectURL(blob);

      const downloadLink =
        document.createElement("a");

      downloadLink.href = downloadUrl;
      downloadLink.download = filename;

      document.body.appendChild(downloadLink);
      downloadLink.click();
      downloadLink.remove();

      window.URL.revokeObjectURL(downloadUrl);

      setSessionId(
        response.headers.get("x-session-id") || ""
      );

      setWatermarkId(
        response.headers.get("x-watermark-id") || ""
      );

      setMessage(
        "Document decrypted successfully. The PDF has been downloaded."
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Document decryption failed."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        className="button button-secondary back-button"
        onClick={() => setPage("dashboard")}
      >
        ← Back to Dashboard
      </button>

      <h1 className="page-title">Decrypt Document</h1>

      <p className="page-description">
        Enter the Document ID and your Recipient ID to request
        decryption.
      </p>

      {message && <div className="message">✓ {message}</div>}

      {error && <div className="error">⚠ {error}</div>}

      <div className="card">
        <h2>Document Information</h2>

        <div className="form-group">
          <label htmlFor="decrypt-document-id">
            Document ID
          </label>

          <input
            id="decrypt-document-id"
            type="text"
            placeholder="Enter Document ID"
            value={documentId}
            onChange={(event) =>
              setDocumentId(event.target.value)
            }
          />
        </div>

        <div className="form-group">
          <label htmlFor="decrypt-recipient-id">
            Recipient ID
          </label>

          <input
            id="decrypt-recipient-id"
            type="text"
            placeholder="OFFICER-001"
            value={recipientId}
            onChange={(event) =>
              setRecipientId(event.target.value)
            }
          />
        </div>

        <div className="actions">
          <button
            className="button button-primary"
            onClick={decryptDocument}
            disabled={loading}
          >
            {loading
              ? "Decrypting..."
              : "Decrypt Document"}
          </button>
        </div>
      </div>

      {(sessionId || watermarkId) && (
        <div className="card">
          <h2>Decryption Details</h2>

          {sessionId && (
            <p>
              <strong>Session ID:</strong>{" "}
              <span className="code-value">
                {sessionId}
              </span>
            </p>
          )}

          {watermarkId && (
            <p>
              <strong>Watermark ID:</strong>{" "}
              <span className="code-value">
                {watermarkId}
              </span>
            </p>
          )}
        </div>
      )}
    </>
  );
}

/* =========================================================
   INVESTIGATE PAGE
========================================================= */

function InvestigatePage({
  setPage,
}: {
  setPage: (page: Page) => void;
}) {
  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState("");
  const [error, setError] = useState("");
  const [result, setResult] = useState<any>(null);

  const investigateDocument = async () => {
    setError("");
    setMessage("");
    setResult(null);

    if (!file) {
      setError("Please select a PDF document.");
      return;
    }

    setLoading(true);

    try {
      const formData = new FormData();
      formData.append("file", file);

      const response = await fetch(
        `${API_BASE}/investigate`,
        {
          method: "POST",
          body: formData,
        }
      );

      let data: any = null;

      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            data?.message ||
            "Investigation failed."
        );
      }

      setResult(data);
      setMessage("Document investigation completed.");
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Investigation failed."
      );
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <button
        className="button button-secondary back-button"
        onClick={() => setPage("dashboard")}
      >
        ← Back to Dashboard
      </button>

      <h1 className="page-title">
        Investigate Document
      </h1>

      <p className="page-description">
        Inspect a PDF for watermark and investigation information.
      </p>

      {message && <div className="message">✓ {message}</div>}

      {error && <div className="error">⚠ {error}</div>}

      <div className="card">
        <h2>Select PDF</h2>

        <div className="form-group">
          <label htmlFor="investigate-file">
            PDF Document
          </label>

          <input
            id="investigate-file"
            type="file"
            accept=".pdf,application/pdf"
            onChange={(event) => {
              setFile(
                event.target.files?.[0] || null
              );
              setResult(null);
              setMessage("");
              setError("");
            }}
          />
        </div>

        {file && (
          <div className="file-info">
            <strong>{file.name}</strong>{" "}
            <span>
              {(file.size / 1024).toFixed(1)} KB
            </span>
          </div>
        )}

        <div className="actions">
          <button
            className="button button-primary"
            onClick={investigateDocument}
            disabled={loading || !file}
          >
            {loading
              ? "Investigating..."
              : "Investigate Document"}
          </button>
        </div>
      </div>

      {result && (
        <div className="card">
          <h2>Investigation Result</h2>

          <pre
            style={{
              whiteSpace: "pre-wrap",
              wordBreak: "break-word",
              background: "#f8fafc",
              padding: "16px",
              borderRadius: "8px",
              overflowX: "auto",
            }}
          >
            {JSON.stringify(result, null, 2)}
          </pre>
        </div>
      )}
    </>
  );
}

/* =========================================================
   LEDGER PAGE
========================================================= */

function LedgerPage({ setPage }: { setPage: (page: Page) => void }) {
  const [ledger, setLedger] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [clearing, setClearing] = useState(false);
  const [error, setError] = useState("");
  const [message, setMessage] = useState("");

  useEffect(() => {
    loadLedger();
  }, []);

  const loadLedger = async () => {
    setLoading(true);
    setError("");
    setMessage("");

    try {
      const response = await fetch(`${API_BASE}/ledger`);

      if (!response.ok) {
        let detail = "Failed to load ledger.";

        try {
          const data = await response.json();
          detail = data?.detail || data?.message || detail;
        } catch {
          // Keep default.
        }

        throw new Error(detail);
      }

      const data = await response.json();

      if (Array.isArray(data)) {
        setLedger(data);
      } else if (Array.isArray(data?.entries)) {
        setLedger(data.entries);
      } else if (Array.isArray(data?.ledger)) {
        setLedger(data.ledger);
      } else {
        setLedger([]);
      }
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to load ledger."
      );
    } finally {
      setLoading(false);
    }
  };

  const clearLedger = async () => {
    const confirmed = window.confirm(
      "Are you sure you want to clear all decryption ledger records?"
    );

    if (!confirmed) {
      return;
    }

    setClearing(true);
    setError("");
    setMessage("");

    try {
      const response = await fetch(`${API_BASE}/ledger`, {
        method: "DELETE",
      });

      let data: any = null;

      try {
        data = await response.json();
      } catch {
        data = null;
      }

      if (!response.ok) {
        throw new Error(
          data?.detail ||
            data?.message ||
            "Failed to clear ledger."
        );
      }

      setLedger([]);
      setMessage(
        "Ledger cleared successfully. New decryption records will be stored again."
      );
    } catch (err) {
      setError(
        err instanceof Error
          ? err.message
          : "Failed to clear ledger."
      );
    } finally {
      setClearing(false);
    }
  };

  return (
    <>
      <button
        className="button button-secondary back-button"
        onClick={() => setPage("dashboard")}
      >
        ← Back to Dashboard
      </button>

      <h1 className="page-title">Audit Ledger</h1>

      <p className="page-description">
        View the cryptographic provenance details recorded when a document is decrypted.
      </p>

      {message && <div className="message">✓ {message}</div>}

      {error && <div className="error">⚠ {error}</div>}

      <div className="card">
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            gap: "10px",
            marginBottom: "18px",
            flexWrap: "wrap",
          }}
        >
          <div>
            <h2 style={{ margin: 0 }}>Decryption Records</h2>
            <p className="small-note" style={{ marginBottom: 0 }}>
              Each successful decryption creates a signed provenance record.
            </p>
          </div>

          <div
            style={{
              display: "flex",
              gap: "10px",
              flexWrap: "wrap",
            }}
          >
            <button
              className="button button-secondary"
              onClick={loadLedger}
              disabled={loading || clearing}
            >
              {loading ? "Refreshing..." : "Refresh Ledger"}
            </button>

            <button
              className="button button-danger"
              onClick={clearLedger}
              disabled={loading || clearing || ledger.length === 0}
            >
              {clearing ? "Clearing..." : "Clear Ledger"}
            </button>
          </div>
        </div>

        {loading && ledger.length === 0 ? (
          <div className="empty-state">
            Loading decryption records...
          </div>
        ) : ledger.length === 0 ? (
          <div className="empty-state">
            <div style={{ fontSize: "30px", marginBottom: "8px" }}>📋</div>
            <strong>No decryption records</strong>
            <p>
              Decrypt an authorized document and its provenance details will appear here.
            </p>
          </div>
        ) : (
          <div className="ledger-list">
            {ledger.map((entry, index) => (
              <LedgerRecord
                key={entry?.id ?? entry?.index ?? index}
                record={entry}
                index={index}
              />
            ))}
          </div>
        )}
      </div>
    </>
  );
}

/* =========================================================
   LEDGER RECORD
========================================================= */

function ResultItem({
  label,
  value,
}: {
  label: string;
  value: React.ReactNode;
}) {
  return (
    <div
      className="result-item"
      style={{
        minWidth: 0,
        width: "100%",
        boxSizing: "border-box",
      }}
    >
      <div className="result-label">{label}</div>
      <div
        className="result-value"
        style={{
          minWidth: 0,
          maxWidth: "100%",
          boxSizing: "border-box",
          overflowWrap: "anywhere",
          wordBreak: "break-word",
          whiteSpace: "pre-wrap",
        }}
      >
        {value || "—"}
      </div>
    </div>
  );
}

function LedgerRecord({
  record,
  index,
}: {
  record: any;
  index: number;
}) {
  const event = record?.event || record || {};

  const documentId =
    event?.document_id || record?.document_id;

  const recipientId =
    event?.recipient_id || record?.recipient_id;

  const sessionId =
    event?.session_id || record?.session_id;

  const watermarkId =
    event?.watermark_id || record?.watermark_id;

  const timestamp =
    event?.timestamp || record?.timestamp;

  const signature =
    event?.signature || record?.signature;

  return (
    <div className="ledger-record">
      <div className="ledger-record-header">
        <strong>
          Decryption Record #{index + 1}
        </strong>

        <span className="ledger-valid">
          ✓ Decryption Recorded
        </span>
      </div>

      <div className="ledger-details">
        <ResultItem
          label="Document ID"
          value={documentId}
        />

        <ResultItem
          label="Recipient ID"
          value={recipientId}
        />

        <ResultItem
          label="Session ID"
          value={sessionId}
        />

        <ResultItem
          label="Watermark ID"
          value={watermarkId}
        />

        <ResultItem
          label="Timestamp"
          value={timestamp}
        />

        <ResultItem
          label="Signature Algorithm"
          value="ML-DSA-65"
        />

        <ResultItem
          label="Signature"
          value={signature}
        />

        <ResultItem
          label="Ledger Status"
          value="Recorded"
        />
      </div>
    </div>
  );
}

export default App;
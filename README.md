# Entra-GitHub Automation

> Effortlessly sync Microsoft Entra (Azure AD) groups with GitHub teams — for seamless onboarding, offboarding, and access control at scale.

---

## 🚀 Overview

**Entra-GitHub Automation** is a serverless solution designed to bridge the gap between Microsoft Entra (formerly Azure AD) and GitHub Enterprise Cloud. When a user is added to a specific Entra group, they are automatically assigned to the corresponding GitHub team — and vice versa.

This automation ensures:
- 🔐 Enterprise-grade role-based security across platforms
- ⚡ Instant team sync for onboarding and offboarding
- ✅ Consistent access control and compliance
- 🔄 Seamless integration with Microsoft and GitHub ecosystems

---

## 📌 Use Cases

- **IT/Admin Automation:** Eliminate manual GitHub team assignments
- **Security & Compliance:** Ensure access consistency across identity providers
- **Developer Onboarding:** Automatically place new hires in the correct repos
- **Offboarding Workflows:** Revoke access instantly when users are removed from Entra groups

---

## 🧠 How It Works

1. 🎯 Monitors Entra group changes (user joins/leaves)
2. 🔄 Azure Function triggers automation logic
3. 🔐 GitHub API assigns/removes user in the mapped team
4. 🧾 Logs and handles errors for full visibility

---

## ⚙️ Tech Stack

- **Azure Functions** (Python)
- **Microsoft Graph API**
- **GitHub REST API**
- **Azure App Service**
- **GitHub Actions** (CI/CD)

---

## 📁 Project Structure

```bash
.
├── .github/workflows        # CI/CD with GitHub Actions
├── function_app.py          # Main Azure Function handler
├── ghub_entra_group_automation.py # Core sync logic
├── host.json                # Azure Functions metadata
├── requirements.txt         # Python dependencies
└── README.md                # You're here ✨
```

---

## 🛠️ Getting Started

1. **Clone the Repo**
   ```bash
   git clone https://github.com/Saphyre-Solutions-LLC/entra-ghub-automation.git
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set Up Azure Function App**
   - Deploy using GitHub Actions or VS Code Azure Functions extension
   - Configure required environment variables (Entra + GitHub credentials)

4. **Map Entra Groups to GitHub Teams**
   - Customize logic inside `ghub_entra_group_automation.py`

5. ✅ Done! Sync will now run on Azure Function triggers.

---

## 🔐 Permissions Required

- **Microsoft Graph:** Group.Read.All, User.Read.All
- **GitHub App or PAT:** `admin:org`, `read:org`

> Ensure credentials are securely stored in Azure App Settings or GitHub Secrets.

---

## 📣 Coming Soon

- ✅ Bi-directional sync (GitHub ➜ Entra)
- 📊 Audit dashboard for sync status
- 🔄 Scheduled sync options
- 🧩 Teams/Slack notifications for changes

---

## 🤝 Contributing

We welcome feedback, ideas, and contributions! Feel free to fork, submit PRs, or open issues.

---

## 📜 License

MIT License © 2025 [Saphyre Solutions LLC](https://saphyresolutions.com)

---

## 📬 Questions?

Open an issue or contact: [tim.spurlin@saphyresolutions.com](mailto:tim.spurlin@saphyresolutions.com)

---

> Built with ❤️ by veterans, engineers, and innovators @ Saphyre Solutions LLC

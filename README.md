# ⚡ BusinessApp - Desktop Management & Billing System
> **High-speed wholesale & retail inventory, billing, and ledger management software for electrical trade shops.**  
> *Powered by [wokdens.com](https://wokdens.com)*

---

## 🚀 Key Features

- **⚡ Tally-Style Zero-Mouse Speed Billing**: Fast keyboard-driven workflow for sales invoicing.
- **📄 Instant Estimate Generation**: Clean, professional estimates formatted with compliant notes and zero clutter.
- **📦 Real-time Inventory & Stock Tracking**: Live stock level badges (Normal / Low / Out of Stock) and unit management.
- **👥 Customer Management & Ledgers**: Complete transaction logs, balance tracking, and customer history.
- **🔒 Admin Authentication**: Password-protected critical operations (stock adjustments, deletion, inventory overrides).
- **💾 Auto-Backups & Offline First**: Local SQLite storage designed for reliable offline shop operations.

---

## ⌨️ Keyboard Shortcuts & Speed Billing Guide (Tally-Style)

### 🔄 Continuous "Enter-to-Next" Billing Loop
Punch entire multi-item bills without touching the mouse:
1. **Customer Search** ➔ Select customer ➔ Press `[Enter]` to jump into **Product Search**.
2. **Product Search** ➔ Type keywords (e.g. `poly 2.5`) ➔ Press `[Tab]` / `[Down Arrow]` to navigate suggestions ➔ Press `[Enter]` to select.
3. **Qty** ➔ Rate, MRP, Unit, and Stock are autofilled; cursor lands in **Qty** (pre-selected). Type quantity ➔ Press `[Enter]`.
4. **Price / Rate** ➔ Press `[Enter]` to keep default or type custom rate.
5. **Discount %** ➔ Type discount % ➔ Press `[Enter]` to **immediately add item to the bill**.
6. Focus **instantly snaps back to Product Search** for Item #2!

---

### 📌 Function Keys & Global Shortcuts

| Shortcut | Action | Scope / Context |
| :--- | :--- | :--- |
| **`F1`** / `Ctrl + C` | Focus **Customer Search** | Anywhere on invoice screen |
| **`F2`** / `Ctrl + P` | Focus **Product Search** | Anywhere on invoice screen |
| **`F3`** / `Alt + C` | Quick **Add New Customer** popup | Anywhere on invoice screen |
| **`F4`** / `Enter` | **Edit Selected Item** in cart table | Table row selected |
| **`Del`** / `Backspace` | **Delete Selected Row** from cart table | Table row selected |
| **`F9`** / `Ctrl + S` | **💾 Save Invoice + Generate PDF** | Anywhere on invoice screen |
| **`F12`** | Jump focus directly to **Paid Amount** | Anywhere on invoice screen |
| **`Alt + X`** | **🧹 Clear / New Bill** | Anywhere on invoice screen |
| **`Tab`** | Move down suggestions dropdown *(like ↓)* | Autocomplete search |
| **`Shift + Tab`** | Move up suggestions dropdown *(like ↑)* | Autocomplete search |
| **`Esc`** | Dismiss suggestion popup | Autocomplete search |

---

## 🛠️ Installation & Local Setup

### Prerequisites
- **Python 3.10+** (Tested on Python 3.11)
- **Windows OS**

### Running from Source
```bash
# 1. Clone the repository
git clone https://github.com/wokdens/BusinessApp.git
cd BusinessApp

# 2. Create and activate virtual environment
python -m venv .venv
.venv\Scripts\activate

# 3. Install required dependencies
pip install -r requirements.txt

# 4. Launch Application
python app.py
```

---

## 📁 Project Structure

```
BusinessApp-model-4/
├── app.py                     # Main application entry point
├── config.py                  # App configuration & theme settings
├── database.py                # SQLite database queries & business logic
├── requirements.txt           # Python dependencies
├── ui/                        # User interface modules
│   ├── main_window.py         # Main container with navigation tabs
│   ├── invoice_ui.py          # Sales invoicing & estimate PDF generation
│   ├── inventory_ui.py        # Inventory catalog & stock adjustments
│   ├── ledger_ui.py           # Customer ledgers & payment history
│   ├── dashboard_ui.py        # Analytics & sales overview
│   ├── autocomplete_combobox.py # Floating Tally-style autocomplete widget
│   ├── customer_popup.py      # Customer addition modal
│   └── admin_auth_dialog.py   # Admin authentication dialog
├── certificates/              # Code signing certificate & keys
├── installer/                 # Inno Setup Windows installer script (.iss)
├── scripts/                   # Code signing and certificate registration scripts
└── invoices/                  # Output directory for generated PDF estimates
```

---

## 🛡️ Production Packaging & Windows SmartScreen Elimination

To distribute the application to client laptops without triggering Windows SmartScreen "Unknown Publisher" / "Install Anyway" warnings:

### 1. Build & Code-Sign Pipeline (1-Click)
Run the automated build script:
```cmd
build_installer.bat
```
*(or run `.venv\Scripts\python.exe build_installer.py`)*

This performs the complete pipeline automatically:
1. **Compiles with `--onedir` & `version.txt`**: Embeds official Wokdens metadata (Company, Product, Version, Copyright) and avoids single-file `%TEMP%` heuristic false positives.
2. **Applies Authenticode Digital Signature**: Signs `BusinessApp.exe` with timestamping from DigiCert.
3. **Packages with Inno Setup**: Compiles a modern Windows installer wizard `BusinessApp_Setup_v1.0.exe` in `dist_installer/`.

### 2. Client Laptop One-Time Trust Setup
For client or trade counter deployments:
- Run **`scripts\install_certificate.bat`** as Administrator on the client laptop.
- This registers the Wokdens certificate into Windows `Trusted Root` and `Trusted Publishers` stores.
- Windows Defender and SmartScreen will permanently recognize **Publisher: Wokdens** and launch smoothly without warnings.

---

## 📄 License & Attribution
- Developed & Maintained by **[wokdens.com](https://wokdens.com)**
- Dedicated for electrical trade counters, wholesale dealers, and retailers.


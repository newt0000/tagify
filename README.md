
# Tagify – Prep Sticker Printer

Tagify is a desktop application designed to streamline the process of generating and printing food preparation labels.  
It provides a fast, searchable interface for selecting prep items and automatically prints standardized **1×1 inch food safety labels** containing:

- Item name
- Date prepped
- Expiration date

The system is designed for environments such as:

- Restaurants
- Cafes
- Commercial kitchens
- Food production facilities

The application is built with **Python + PySide6** and integrates directly with Windows printer drivers.

---

# Table of Contents

1. Overview
2. Architecture
3. Installation
4. Running the Application
5. Packaging the Application
6. Project Structure
7. Detailed Module Documentation
8. Printing System
9. Database System
10. Configuration System
11. Troubleshooting
12. Future Improvements

---

# 1. Overview

Tagify was created to replace manual label writing with a **fast digital workflow**.

Typical workflow:

1. Select a food item
2. Adjust the number of labels
3. Print

Each printed label includes:

```
Item Name
Prepped: MM/DD/YYYY
Expires: MM/DD/YYYY
```

The expiration date is automatically calculated based on the configured shelf life.

The UI is optimized for **touchscreens or quick mouse interaction** in busy kitchens.

---

# 2. Architecture

The application consists of five primary systems:

| System | Responsibility |
|------|------|
| UI Layer | All visual components |
| Database Layer | Stores items, categories, and settings |
| Printer Backend | Manages printer discovery and status |
| Label Renderer | Generates label images |
| Config Manager | Handles data import/export |

---

# 3. Installation

### Requirements

Python 3.11+ recommended.

Install dependencies:

```
pip install PySide6 pillow reportlab pywin32
```

Dependencies:

| Library | Purpose |
|------|------|
PySide6 | GUI framework |
Pillow | Image rendering |
ReportLab | PDF label generation |
pywin32 | Windows printing API |

---

# 4. Running the Application

Run from the project root:

```
python app.py
```

---

# 5. Packaging the Application

To package as a standalone executable:

```
pyinstaller app.py --onefile --windowed --icon=icon.ico --add-data "icon.png;_internal"
```

Explanation:

| Flag | Purpose |
|------|------|
--onefile | Creates single executable |
--windowed | Prevents console window |
--icon | Sets program icon |
--add-data | Bundles resource files |

---

# 6. Project Structure

```
tagify/
│
├── app.py
├── db.py
├── label_print.py
├── printer_backend.py
│
├── ui_main.py
├── ui_settings.py
├── ui_config.py
│
├── styles.py
│
├── data/
│   └── database.db
│
└── _internal/
    └── icon.png
```

---

# 7. Detailed Module Documentation

---

# app.py

Main application entry point.

Responsible for:

- launching the GUI
- initializing the database
- creating application tabs
- coordinating data refresh events

## Functions

### main()

```
def main():
```

Application startup routine.

Steps:

1. Initialize database
2. Create QApplication
3. Apply UI styling
4. Create MainWindow
5. Start Qt event loop

---

## Class: MainWindow

Central window controller.

Creates three major tabs:

| Tab | Purpose |
|------|------|
Main | Label printing interface |
Settings | Printer configuration |
Config | Data management |

### Methods

#### on_data_changed()

Called whenever:

- items are added
- categories change
- configuration is imported

Triggers UI refresh.

---

# ui_main.py

Contains the **primary user interface used during normal operation**.

Responsibilities:

- item search
- category filtering
- label preview
- print controls

---

## Class: MainTab

Primary label printing interface.

### Components

Left Panel:

| Component | Purpose |
|------|------|
Print Count | Number of labels |
Preview | Shows rendered label |
Print Button | Sends job to printer |

Right Panel:

| Component | Purpose |
|------|------|
Item Grid | Select prep items |
Search Box | Filter items |
Category Filter | Organize items |

---

### Methods

#### refresh_tiles()

Rebuilds the item button grid.

Called when:

- database changes
- category filter changes
- search query changes

---

#### reload_categories()

Reloads category list from database.

---

#### refresh_printer_status()

Checks printer availability and updates the status indicator bubble.

---

# ui_settings.py

Contains system configuration tools.

Sections include:

| Section | Description |
|------|------|
Printer Selection | Choose printer |
Admin Panel | Manage prep items |
Category Manager | Organize item groups |

---

## Class: SettingsTab

Primary configuration interface.

### Methods

#### list_printers()

Populates the printer dropdown using Windows printer enumeration.

#### refresh_admin_tables()

Reloads item/category tables after database changes.

---

# ui_config.py

Provides data management tools.

Functions include:

- Import configuration
- Export configuration
- Backup database

Useful for migrating between machines.

---

# label_print.py

Handles **label generation and printing**.

---

## generate_1x1_label_pdf()

```
generate_1x1_label_pdf(item_name, prepped, expires, out_path)
```

Creates a **1×1 inch label** containing:

- item name
- prep date
- expiration date

Uses ReportLab to generate a PDF.

---

## print_label_pdf()

```
print_label_pdf(pdf_path, printer_name)
```

Prints the label file.

Steps:

1. Validate file
2. Resolve printer name
3. Send job to printer spooler
4. Monitor job completion

---

## make_temp_label_path()

Creates temporary storage location for generated labels.

Example:

```
C:/Temp/prep_label_1x1.pdf
```

---

# printer_backend.py

Responsible for:

- printer discovery
- connection status
- driver communication

---

## list_printers()

Returns all printers detected by Windows.

Uses:

```
win32print.EnumPrinters()
```

---

## get_printer_state()

Checks printer status.

Returns:

| Field | Description |
|------|------|
connected | True if printer available |
name | Printer name |
status | Status text |

---

# db.py

Handles all database interactions.

Database type:

```
SQLite
```

Tables:

| Table | Purpose |
|------|------|
items | Prep items |
categories | Item groups |
settings | System configuration |

---

## init_db()

Creates database and tables if missing.

---

## get_items()

Returns all stored prep items.

---

## add_item()

Adds new prep item.

Fields:

| Field | Description |
|------|------|
name | Item name |
expire_days | Shelf life |
category | Item category |

---

# 8. Printing System

Tagify prints labels by:

1. Generating a label image
2. Sending it to the Windows printer driver
3. Scaling to fit a 1×1 inch page

Supported printers:

- Thermal label printers
- Inkjet/laser printers
- Virtual printers

---

# 9. Database System

Uses SQLite for portability.

Benefits:

- No server required
- File-based storage
- Easy backup

---

# 10. Configuration System

Configuration tools allow:

- exporting items
- importing setups
- migrating between devices

---

# 11. Troubleshooting

### Printer not detected

Ensure printer is installed in Windows.

### Printing error

Verify:

- printer selected in settings
- printer is online

### Application fails to launch

Ensure dependencies installed.

---

# 12. Future Improvements

Potential enhancements:

- barcode support
- QR labels
- thermal printer ESC/POS mode
- network printing
- inventory integration
---
## Application Gallery

<p align="center">
  <img src="gallery/screenshot1.png" width="30%">
  <img src="gallery/screenshot2.png" width="30%">
  <img src="gallery/screenshot3.png" width="30%">
</p>

<p align="center">
  <img src="gallery/screenshot4.png" width="30%">
  <img src="gallery/screenshot5.png" width="30%">
  <img src="gallery/screenshot6.png" width="30%">
</p>

<p align="center">
  <img src="gallery/screenshot7.png" width="30%">
  <img src="gallery/screenshot8.png" width="30%">
  <img src="gallery/screenshot10.png" width="30%">
</p>

<p align="center">
  <img src="gallery/screenshot9.png" width="30%">
</p>
---

# License

Internal kitchen use / custom deployment.\
Protected under Creative Commons Copyright  &copy; Newt-tech 2026

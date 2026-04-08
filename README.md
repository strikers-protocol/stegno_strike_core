<div align="center">

# 🕵️‍♂️ STEGNO_STRIKE :: ECOSYSTEM

<a href="https://github.com/strikers-protocol/stegno_strike_app"><img src="https://img.shields.io/badge/📥_DOWNLOAD_APP-00E5FF?style=for-the-badge&logoColor=black" alt="App"/></a>
<a href="https://github.com/strikers-protocol/stegno_strike_theory"><img src="https://img.shields.io/badge/📖_READ_THEORY-007ACC?style=for-the-badge&logoColor=white" alt="Theory"/></a>
<a href="https://github.com/strikers-protocol/stegno_strike_core"><img src="https://img.shields.io/badge/💻_SOURCE_CODE-111111?style=for-the-badge&logoColor=white" alt="Code"/></a>

<br>
<i>The raw Python source code and cryptographic engine for Stegno_Strike.</i>
<br><br>

---

</div>

## 💻 Developer Documentation

This repository contains the raw Python source code for the Stegno_Strike engine. It is designed for security researchers, open-source contributors, and developers who wish to audit the AES-256 encryption or run the tool directly from their terminal.

### ⚙️ System Requirements
* **Python:** v3.8 or higher.
* **OS:** Cross-platform (Windows, macOS, Linux). The compiled `.exe` (available in the App repo) is Windows-only, but this source code runs anywhere.

### 🛠️ Local Environment Setup

**1. Clone the Repository:**
`git clone https://github.com/strikers-protocol/stegno_strike_core.git`
`cd stegno_strike_core`

**2. Create a Virtual Environment (Recommended):**
`python -m venv venv`
* **Windows:** `venv\Scripts\activate`
* **Mac/Linux:** `source venv/bin/activate`

**3. Install Dependencies:**
The engine relies on `customtkinter` for the UI, `Pillow` for image processing, and `cryptography` for the AES-256 cipher.
`pip install -r requirements.txt`

### 🚀 Running the Engine
Once your environment is set up, initialize the core script:
`python gui_stego.py`

---

### 🏗️ Build Instructions (PyInstaller)
If you wish to compile your own standalone executable from this source code, use the following command (requires `pyinstaller`):

`pyinstaller --noconsole --onefile --clean --add-data "strike.ico;." --icon="strike.ico" --version-file="version.txt" --name="stegno_strike" gui_stego.py`

<br>

***

<div align="center">

*To download the pre-compiled application or read the steganography theory, use the Control Panel above.*

*© 2026 Strikers Protocol. All rights reserved.*

</div>

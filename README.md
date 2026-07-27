# FocusFlow 🚀

FocusFlow is a lightweight, cross-platform Python tool designed to help students and professionals boost productivity by blocking distracting websites during deep work or study sessions.

## 💡 Why FocusFlow?
In an age of constant digital distraction, FocusFlow helps you regain control of your time. By modifying your system's `hosts` file, it effectively prevents access to time-wasting sites like YouTube, Facebook, and TikTok during your scheduled study hours.

## ✨ Features
- **Smart Blocking:** Automatically redirects distracting domains to `127.0.0.1`.
- **Cross-Platform:** Works seamlessly on both Windows and Linux.
- **Safety First:** Includes a cleanup mechanism to restore your `hosts` file when the session ends or if the program is interrupted.
- **Notifications:** Built-in alerts to remind you when your study time is about to start.
- **Clean Code:** Modular design with robust error handling.

## 🛠 Prerequisites
- **Python 3.x** installed on your system.
- **Administrator/Sudo privileges** are required (as the program modifies system files).

## 🚀 Installation & Usage

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Abdelilah-dev/FocusFlow.git
   cd FocusFlow
   ```
   ٍ
2. **Run the application:**

   - **On Linux:**
     ```bash
     sudo python3 main.py
     ```

   - **On Windows:**
     Run your terminal (CMD or PowerShell) as **Administrator** and execute:
     ```bash
     python main.py
     ```

3. **Follow the prompts:**
   - Enter your preferred start time (HH:MM).
   - Enter your study duration (HH:MM).

## 🛡 How it works
FocusFlow uses the `hosts` file logic to override DNS resolution. When the study session starts, it appends block rules; when the session ends or you terminate the process (`Ctrl+C`), it cleanly removes these rules to restore normal internet access.

## 🤝 Contributing
Contributions are welcome! If you have suggestions or improvements, feel free to open an issue or submit a pull request.

## 📝 License
This project is open-source and available under the MIT License.

---
*Built with ❤️ by Abdelilah.*
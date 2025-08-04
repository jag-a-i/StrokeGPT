StrokeGPT - AI-Controlled Pleasure

Welcome to StrokeGPT! This is a simple guide to help you set up your own private, voice-enabled AI companion for compatible devices.

WINDOWS ONLY.

## What Does It Do?

* Multi-Device Support: Compatible with The Handy and any device supported by Buttplug.io/Intiface Central (vibrators, strokers, and more).
* AI-Controlled Fun: Chat with an AI that controls your device's movements in real-time.
* Fully Customizable Persona: Change the AI's name, personality, and even their profile picture to create your perfect partner.
* Interactive Modes: Go beyond simple chat with advanced, interactive modes for Edging, Milking, and Auto-play. You can even influence the AI's patterns mid-session with chat messages!
* It Remembers You: The AI learns your preferences and remembers details from past chats.
* Internet-Connected for Control & Voice: The app requires an internet connection for device control and optional voice features. Your AI model (Ollama) still runs 100% locally on your computer.
* Hidden Easter Eggs: A few secrets are tucked away.
* Built-in Safety: The app includes safety limiters to ensure movements always stay within your comfortable range.

## How to Get Started (easier than it looks!)

### Step 1: Install Prerequisites

You need these free programs to run the app:

**Python:**
* Download the latest version from the official Python website.
* During installation, you **must check the box** that says "Add Python to PATH."

**For Buttplug.io/Intiface Central users (optional):**
* Download and install Intiface Central from https://intiface.com/central/
* Launch Intiface Central and ensure it's running before starting StrokeGPT

**Ollama (The AI's "Brain"):**
* Download Ollama from the Ollama website.
* After installing, open a terminal (Command Prompt on Windows) and run the following command **once** to download the AI model:
    ```
    ollama run llama3:8b-instruct-q4_K_M
    ```
* This will take a few minutes because, much like your mum, models are chonky. Once it's finished, you can close the terminal. Make sure the Ollama application is running in the background before you start StrokeGPT.

### Step 2: Download & Install StrokeGPT

* Download the Project: Go to the project's GitHub page and click the green `<> Code` button, then select "Download ZIP".
* Unzip the file into a folder you can easily access, like your Desktop.
* Install Required Libraries:
    * Open a terminal directly in your new project folder:
    * Open the folder, click the address bar at the top, type `cmd`, and press Enter.
    * In the terminal, run this command:
        ```
        pip install -r requirements.txt
        ```

### Step 3: Run the App!

* Start the Server:
    * In the same terminal (still in your project folder), run this command:
        ```
        python app.py
        ```
    * The server is working when you see a message ending in `Running on http://127.0.0.1:5000`. Keep this terminal window open.
* Open in Browser:
    * Open your web browser and go to the following address:
        http://127.0.0.1:5000
* The splash screen will appear. Press Enter to begin the on-screen setup guide.
* In the setup, you'll be asked to choose your device type:
  - **The Handy**: Enter your Handy connection key when prompted
  - **Buttplug.io/Intiface Central**: Make sure Intiface Central is running, then select your device from the list

Enjoy your personalized experience!

## Tips for Best Experience

* **Speed Settings**: Don't be fooled by the 0-100 scale! For The Handy, many users find a Max Speed setting between 10-25 to be more than enough. Start low and adjust to your preference.
* **Buttplug.io Users**: Ensure Intiface Central is running before starting StrokeGPT. The app will automatically detect compatible devices.
* **Troubleshooting**: If your device isn't detected, check that:
  - The device is properly connected and powered on
  - Intiface Central is running (for Buttplug devices)
  - You've selected the correct device type in the setup

* Enjoying StrokeGPT?
This app is a passion project and is completely free. If you're having fun and want to support future development, consider buying me a coffee!

https://ko-fi.com/strokegpt
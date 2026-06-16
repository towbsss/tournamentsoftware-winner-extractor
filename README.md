# TournamentSoftware Winner Extractor 🏆

A modern web application built with Python and Streamlit to extract results and placements of your club's athletes from any TournamentSoftware.com winners page. 

It matches player names from your roster list (either typed in, loaded from a `.txt` file, or loaded from an Excel `.xlsx` spreadsheet) against the final tournament winners table. It automatically normalizes names (removing tournament seedings like `[1]` or `[3/4]`) and translates numerical placements into standard rankings (`Champion`, `Finalist`, `Semi-finalist`).

---

## Features

- **Multi-format Input**: Paste names directly, import a `.txt` file, or load a `.xlsx` Excel sheet of player names.
- **Auto URL/ID Parsing**: Paste a full tournament overview link, draws link, or raw tournament ID (GUID). The app automatically resolves it to the correct winners page.
- **Copy & Export**: Copy findings to clipboard with one click, or export matched results directly to a text file.
- **Modern Interface**: Designed with high-contrast UI accents, dark mode support, and interactive visual feedback.

---

## How to Run Locally

### Prerequisites
You need **Python** installed (along with libraries listed in `requirements.txt`). If you use Anaconda:

1. Open **PowerShell** or your **Anaconda Prompt**.
2. Navigate to your project directory:
   ```powershell
   cd path/to/your/project-directory
   ```
3. Run the following command to launch the Streamlit web server:
   ```powershell
   streamlit run app_streamlit.py
   ```
4. The app will open automatically in your browser at `http://localhost:8501`.

---

## How to Deploy to GitHub & Streamlit (Free Hosting)

To share this app with your club members via a public website link, follow these steps:

### Step 1: Upload to GitHub
1. Create a free account at [github.com](https://github.com) if you haven't already.
2. Create a new **public repository** named `tournamentsoftware-winner-extractor`.
3. In PowerShell, initialize git and push your files to GitHub (replace your username in the URL below):
   ```powershell
   git init
   git add .
   git commit -m "Initial commit of winner extractor"
   git branch -M main
   git remote add origin https://github.com/YOUR_GITHUB_USERNAME/tournamentsoftware-winner-extractor.git
   git push -u origin main
   ```

### Step 2: Deploy on Streamlit Community Cloud
1. Go to [streamlit.io/cloud](https://streamlit.io/cloud) and click **Sign Up** / **Sign In**.
2. Select **Continue with GitHub** to connect your GitHub profile.
3. Once logged in, click the **New app** button.
4. Fill in the deployment details:
   - **Repository**: `YOUR_GITHUB_USERNAME/tournamentsoftware-winner-extractor` (or select it from the dropdown)
   - **Branch**: `main`
   - **Main file path**: `app_streamlit.py`
5. Click **Deploy!**
6. Once the setup completes (usually takes about a minute), your app will be live on a public URL (e.g. `https://your-app-name.streamlit.app`) which you can share with your club!

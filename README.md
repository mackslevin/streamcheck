# streamcheck
A command line utility to track movie streaming availability across paid and free platforms. Checks US availability by default, with an option to search internationally. Searches are saved to a local JSON watchlist, allowing users to easily poll for status updates and receive native system notifications when a movie's streaming status changes.

## Features
- **Title Search:** Quickly find if a movie is streaming, and where.
- **International Availability:** Option to expand the search beyond the US to see global streaming options.
- **Watchlist Tracking:** Automatically saves searched movies to a local watchlist (`~/.config/streamcheck/watchlist.json`).
- **Status Alerts:** Run a check against your watchlist and receive native desktop notifications when a movie arrives on a streaming service.

## Prerequisites
- Python 3
- TMDB API Key: You must have a free API key from [The Movie Database (TMDB)](https://www.themoviedb.org/settings/api).

## Installation
1. **Clone the repository:**
   ```bash
   git clone https://github.com/mackslevin/streamcheck.git
   cd streamcheck
   ```

2. **Install the required dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

3. **Make the script executable:**
   ```bash
   chmod +x streamcheck.py
   ```

4. **Create a global symlink:** This allows you to run the `streamcheck` command from anywhere in your terminal.

   **For Linux:**
   ```bash
   ln -s $(pwd)/streamcheck.py ~/.local/bin/streamcheck
   ```
   *(Note: Ensure `~/.local/bin` is in your system's PATH).*

   **For macOS:**
   ```bash
   sudo ln -s $(pwd)/streamcheck.py /usr/local/bin/streamcheck
   ```

5. **Set up your API Key:**
   Add your TMDB API key to your environment variables so the script can authenticate your searches.

   **For macOS (Zsh - Default):**
   Add the following line to your `~/.zshrc` file:
   ```bash
   export TMDB_API_KEY="your_actual_api_key_here"
   ```
   Then reload your profile: `source ~/.zshrc`

   **For Linux (Bash):**
   Add the following line to your `~/.bashrc` file:
   ```bash
   export TMDB_API_KEY="your_actual_api_key_here"
   ```
   Then reload your profile: `source ~/.bashrc`

## Usage
Run the tool directly from your terminal:

- **Search for a movie:** `streamcheck "Barry Lyndon"`
- **Refresh watchlist and check for updates:** `streamcheck --check`
- **List all saved movies and their current status:** `streamcheck --list`
- **Remove the most recently added movie:** `streamcheck --remove-last` (or `streamcheck -rl`)
- **Manually edit the watchlist JSON file:** `streamcheck --edit`

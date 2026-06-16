import re
import urllib.parse
import streamlit as st
import requests
from bs4 import BeautifulSoup
import urllib3
import pandas as pd

# Disable Insecure Request Warning from urllib3 when using verify=False
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

# --- CORE PARSING LOGIC ---

def clean_player_name(name):
    """Strip trailing seeding info like [1] or [3/4] or [5/8]."""
    cleaned = re.sub(r'\s*\[\s*\d+(?:/\d+)?\s*\]\s*$', '', name)
    cleaned = ' '.join(cleaned.split())
    return cleaned

def extract_players_from_cell(cell):
    """Extract and clean player names from a cell (tries <a> first, falls back to text splits)."""
    links = cell.find_all('a')
    if links:
        names = [a.get_text().strip() for a in links]
    else:
        names = [name.strip() for name in cell.get_text(separator='\n').split('\n') if name.strip()]
    
    return [clean_player_name(name) for name in names if name.strip()]

def map_place(place_str):
    """Map place string (1, 2, 3/4) to standard text."""
    place_str = place_str.strip()
    if place_str == '1':
        return 'Champion'
    elif place_str == '2':
        return 'Finalist'
    elif place_str in ('3', '4', '3/4'):
        return 'Semi-finalist'
    else:
        return f"Placed {place_str}"

def extract_winners(html_content, target_names):
    """Parse winners page HTML and match against target names (case-insensitive)."""
    target_names_lower = {name.lower().strip(): name for name in target_names}
    matched_results = {}  # name -> list of result strings
    
    soup = BeautifulSoup(html_content, 'html.parser')
    tables = soup.find_all('table')
    
    for table in tables:
        rows = table.find_all('tr')
        current_event = "Unknown Event"
        
        for row in rows:
            cells = row.find_all(['td', 'th'])
            if len(cells) == 1:
                # Event category header (e.g. MS, WD, S SH6)
                current_event = cells[0].get_text().strip()
            elif len(cells) == 2:
                # Placement row
                place = cells[0].get_text().strip()
                players = extract_players_from_cell(cells[1])
                
                for player in players:
                    player_lower = player.lower()
                    if player_lower in target_names_lower:
                        original_target_name = target_names_lower[player_lower]
                        placement_str = map_place(place)
                        result_entry = f"{current_event} {placement_str}"
                        
                        if original_target_name not in matched_results:
                            matched_results[original_target_name] = []
                        matched_results[original_target_name].append(result_entry)
                        
    return matched_results


# --- STREAMLIT UI ---

st.set_page_config(
    page_title="TournamentSoftware Winner Extractor",
    page_icon="🏆",
    layout="centered"
)

# Custom Style for clean margins
st.markdown("""
    <style>
    .reportview-container {
        background-color: #121214;
    }
    h1 {
        padding-bottom: 0.2rem;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🏆 TournamentSoftware Winner Extractor")
st.markdown("Extract results and placements of your club's athletes from any TournamentSoftware.com winners list.")

# 1. Tournament Input Section
st.header("1. Tournament Details")
url_input = st.text_input(
    "Paste the full TournamentSoftware URL or the 36-character tournament ID (GUID):",
    value="...",
    placeholder="e.g. 7A817C4F-7EDD-493C-918B-8DC6C2EDFA67"
)

# 2. Roster Names Input Section
st.header("2. Roster / Athlete Names")

# Setup tabs for different input methods
tab_paste, tab_upload = st.tabs(["📋 Paste Names Directly", "📁 Upload Roster File"])

names_list = []

with tab_paste:
    pasted_text = st.text_area(
        "Enter player names as used on TournamentSoftware (one per line):",
        value="John DOE\nJane SMITH\nFirst Middle LASTNAME",
        height=150,
        help="Type or paste a list of players. Matches are case-insensitive."
    )
    if pasted_text:
        names_list = [line.strip() for line in pasted_text.split('\n') if line.strip()]

with tab_upload:
    uploaded_file = st.file_uploader(
        "Upload a .txt or Excel file (.xlsx, .xls):",
        type=["txt", "xlsx", "xls"],
        help="Text files should list one name per line. Excel files should have names in the first column."
    )
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith(".txt"):
                content = uploaded_file.read().decode("utf-8")
                names_list = [line.strip() for line in content.split('\n') if line.strip()]
            else:
                df = pd.read_excel(uploaded_file, header=None)
                if not df.empty:
                    raw_names = df.iloc[:, 0].dropna().tolist()
                    names_list = [str(n).strip() for n in raw_names if str(n).strip()]
            
            st.success(f"Successfully loaded {len(names_list)} names from file!")
            # Display loaded names preview
            with st.expander("Preview loaded names"):
                st.write(names_list)
        except Exception as e:
            st.error(f"Error reading file: {str(e)}")

# 3. Extraction Action
st.header("3. Results")

if st.button("⚡ Extract & Match Winners", use_container_width=True):
    if not url_input.strip():
        st.error("Please provide a valid tournament link or ID.")
    elif not names_list:
        st.error("Please enter or upload player names.")
    else:
        with st.spinner("Fetching winners from TournamentSoftware..."):
            try:
                # 1. Normalize ID and domain
                subdomain = "badmintoncanada"  # default
                tournament_id = ""
                
                guid_pattern = r'[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}'
                guid_match = re.search(guid_pattern, url_input, re.IGNORECASE)
                
                if guid_match:
                    tournament_id = guid_match.group(0)
                else:
                    raise ValueError("Could not find a valid 36-character tournament ID (GUID) in your input.")
                
                if "tournamentsoftware.com" in url_input:
                    parsed_url = urllib.parse.urlparse(url_input)
                    netloc = parsed_url.netloc
                    if netloc:
                        parts = netloc.split('.')
                        if len(parts) >= 3:
                            subdomain = parts[0]
                
                winners_url = f"https://{subdomain}.tournamentsoftware.com/sport/winners.aspx?id={tournament_id}"
                
                # 2. Fetch page
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                }
                response = requests.get(winners_url, headers=headers, verify=False, timeout=15)
                
                if response.status_code != 200:
                    raise Exception(f"Unable to access winners page. Server returned status code: {response.status_code}")
                
                # 3. Process matches
                matched_results = extract_winners(response.text, names_list)
                
                # 4. Format results
                output_lines = []
                has_matches = False
                
                for name in names_list:
                    matched_key = None
                    for key in matched_results:
                        if key.lower() == name.lower():
                            matched_key = key
                            break
                    
                    if matched_key:
                        has_matches = True
                        output_lines.append(name)
                        for placement in matched_results[matched_key]:
                            output_lines.append(placement)
                        output_lines.append("")  # spacing
                
                output_text = "\n".join(output_lines).strip()
                
                if has_matches:
                    st.success("Matches found!")
                    st.code(output_text, language="text")
                    
                    # Download button
                    st.download_button(
                        label="📥 Download Results as TXT",
                        data=output_text,
                        file_name="matched_winners.txt",
                        mime="text/plain",
                        use_container_width=True
                    )
                else:
                    st.info("No matches found in the tournament winners list.")
                    
            except Exception as e:
                st.error(f"Failed to extract winners: {str(e)}")

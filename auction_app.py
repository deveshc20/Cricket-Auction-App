import streamlit as st
import pandas as pd
import openpyxl
import time

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Cricket Auction App", layout="wide")

# ----------- CUSTOM CSS FOR UI -----------
st.markdown("""
<style>
html, body, [class*="css"]  { font-family: "Segoe UI", Tahoma, Geneva, Verdana, sans-serif; }
table { border-collapse: collapse; width: 100%; transition: all 0.5s ease-in-out; }
thead tr { background-color: #0275d8; color: white; }
th, td { padding: 8px 12px; border: 1px solid #ddd; text-align: left; }
tr:nth-child(even) { background-color: #f9f9f9; }
div.stButton > button:hover { background-color: #0275d8; color: white; transform: scale(1.05); transition: 0.3s; }
.css-ffhzg2 { margin-top: 10px; margin-bottom: 20px; }
.metric-value { font-size: 2.2rem !important; font-weight: 600 !important; }
.fade-in { animation: fadeIn 0.8s ease-in-out; }
.countdown-container { width: 100%; background-color: #ddd; border-radius: 5px; margin-top: 5px; }
.countdown-bar { height: 15px; border-radius: 5px; transition: width 0.3s ease-in-out; }
@keyframes fadeIn { 0% {opacity:0;} 100% {opacity:1;} }
</style>
""", unsafe_allow_html=True)

# ---------- SOUND & CONFETTI EFFECT ----------
sound_base64 = "SUQzAwAAAAAAIVRBTEIAAAAPAAABAAAAAAAAAAAAAAAAAA=="
sound_html = f"""
<audio autoplay>
    <source src="data:audio/mp3;base64,{sound_base64}" type="audio/mp3">
</audio>
"""
confetti_html = """
<script src="https://cdn.jsdelivr.net/npm/canvas-confetti@1.6.0/dist/confetti.browser.min.js"></script>
<script>
function launchConfetti() {
  confetti({
    particleCount: 100,
    spread: 70,
    origin: { y: 0.6 }
  });
}
</script>
"""

st.markdown(confetti_html, unsafe_allow_html=True)

# ---------- SESSION INIT ----------
for key in ['player_index','teams','auction_results','players_df','start_time','history','current_player']:
    if key not in st.session_state:
        st.session_state[key] = [] if key in ['teams','auction_results','history'] else None

# ---------- HISTORY HELPERS ----------
def push_history(action: dict):
    st.session_state['history'].append(action)

def undo_last():
    if not st.session_state['history']:
        return False, "Nothing to undo."
    action = st.session_state['history'].pop()
    df = st.session_state['players_df']
    df.loc[df['Player No'] == action['player_no'], 'Auctioned'] = False
    st.session_state['players_df'] = df.copy()
    for i in range(len(st.session_state['auction_results']) - 1, -1, -1):
        if st.session_state['auction_results'][i]['Player No'] == action['player_no']:
            st.session_state['auction_results'].pop(i)
            break
    if action['type'] == 'sold':
        team_name = action['team']
        price = action['price']
        for team in st.session_state['teams']:
            if team['Team'] == team_name:
                team['Players'] = [p for p in team['Players'] if p['Player No'] != action['player_no']]
                team['Spent'] -= price
                team['Budget'] += price
                break
    return True, "Last action undone."

# ---------- SIDEBAR ----------
st.sidebar.markdown("[\U0001F310 GitHub](https://github.com/deveshc20)  |  \U0001F9D1‍\U0001F4BB Created by **DC**")
st.sidebar.title("🏏 Cricket Auction System")

with st.sidebar:
    st.markdown("---")
    if st.button("↩️ Undo Last", key="undo_last"):
        ok, msg = undo_last()
        st.success(msg) if ok else st.info(msg)
        st.rerun()

    col_s1, col_s2 = st.columns(2)
    if col_s1.button("🔁 Restart Auction", key="restart"):
        st.session_state['player_index'] = 0
        st.session_state['auction_results'] = []
        st.session_state['history'] = []
        if st.session_state.get('players_df') is not None:
            st.session_state['players_df']['Auctioned'] = False
        for team in st.session_state['teams']:
            team['Players'] = []
            team['Spent'] = 0
        st.success("Auction restarted.")
        st.rerun()

    if col_s2.button("❌ Clear All Data", key="clear_all"):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.success("All session data cleared.")
        st.rerun()

    st.markdown("---")
    st.subheader("🛠️ Manual Correction for Unsold Players")
    unsold_players = [p for p in st.session_state['auction_results'] if p['Team'] == 'UNSOLD']
    if unsold_players:
        unsold_player_names = [f"{p['Player Name']} (Player No: {p['Player No']})" for p in unsold_players]
        selected_unsold = st.selectbox("Select Unsold Player to Correct", options=unsold_player_names, key="unsold_select")
        selected_index = unsold_player_names.index(selected_unsold)
        selected_player = unsold_players[selected_index]
        correction_team = st.selectbox("Select Team to assign", [t['Team'] for t in st.session_state['teams']], key="correction_team")
        correction_price = st.number_input("Enter Sold Price (₹)", min_value=0, step=10, value=100, key="correction_price")
        if st.button("✅ Confirm Correction", key="correction_confirm"):
            if correction_price>0:
                st.session_state['auction_results'] = [p for p in st.session_state['auction_results'] if not (p['Player No']==selected_player['Player No'] and p['Team']=='UNSOLD')]
                st.session_state['auction_results'].append({
                    'Player No': selected_player['Player No'],
                    'Player Name': selected_player['Player Name'],
                    'Role': selected_player.get('Role',''),
                    'Team': correction_team,
                    'Price': correction_price
                })
                for team in st.session_state['teams']:
                    if team['Team']==correction_team and all(p['Player No'] != selected_player['Player No'] for p in team['Players']):
                        team['Players'].append({
                            'Player No': selected_player['Player No'],
                            'Player Name': selected_player['Player Name'],
                            'Role': selected_player.get('Role',''),
                            'Price': correction_price
                        })
                        team['Spent']+=correction_price
                        team['Budget']-=correction_price
                        break
                push_history({'type':'sold','player_no':selected_player['Player No'],'team':correction_team,'price':correction_price,'player_row':selected_player})
                st.success(f"Corrected unsold player '{selected_player['Player Name']}' as sold to {correction_team} for ₹{correction_price}.")
                st.rerun()
    else:
        st.info("No unsold players to correct.")

# ---------- TABS ----------
tab_upload, tab_team, tab_auction, tab_summary = st.tabs(
    ["1️⃣ Upload Players","2️⃣ Team Setup","3️⃣ Auction Panel","4️⃣ Summary & Export"]
)

# ---------- 1️⃣ Upload ----------
with tab_upload:
    st.title("📅 Upload Player List")
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])
    canonical_required = {"player no":"Player No","player name":"Player Name","role":"Role"}
    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)
            df.columns = pd.Index(df.columns).astype(str).str.strip().str.lower()
            missing = [c for c in canonical_required.keys() if c not in df.columns]
            if missing: st.error("Missing columns: "+",".join(missing))
            else:
                df = df.rename(columns=canonical_required)
                if "Auctioned" not in df.columns: df["Auctioned"]=False
                st.session_state['players_df'] = df.copy()
                st.success("✅ File uploaded successfully!")
                st.dataframe(df.head(10))
        except Exception as e:
            st.error(f"Error reading file: {e}")
    else: st.info("Upload an Excel file with columns: Player No, Player Name, Role")

# ---------- 2️⃣ Team Setup ----------
with tab_team:
    st.title("👥 Team Setup")
    num_teams = st.number_input("Number of teams", min_value=2, max_value=12, value=4, step=1, key="num_teams")
    with st.form("team_setup_form"):
        st.subheader("Enter Team Details")
        teams = []
        for i in range(num_teams):
            col1, col2 = st.columns([2,1])
            name = col1.text_input(f"Team {i+1} Name", key=f"team_name_{i}")
            budget = col2.number_input(f"Budget (₹)", min_value=100, step=10, value=900, key=f"team_budget_{i}")
            teams.append({'Team':name.strip(),'Budget':budget,'Spent':0,'Players':[]})
        submit = st.form_submit_button("✅ Save Teams")
    if submit:
        if all(team['Team'] for team in teams):
            st.session_state['teams']=teams
            st.success("✅ Teams saved successfully!")
        else: st.error("❌ All team names are required.")
    if st.session_state['teams']:
        st.subheader("📋 Team Summary")
        st.dataframe(pd.DataFrame(st.session_state['teams']).drop(columns=['Players']))

# ---------- 3️⃣ Auction Panel ----------
with tab_auction:
    st.title("🎯 Auction Panel")
    if st.session_state.get('players_df') is None or st.session_state['players_df'].empty:
        st.warning("⚠️ Upload the player list first.")
    else:
        df = st.session_state['players_df']
        total_players = df.shape[0]
        pending_players = int((df['Auctioned']==False).sum())
        auctioned_players = int((df['Auctioned']==True).sum())
        k1,k2,k3 = st.columns(3)
        k1.metric("Total Players", total_players)
        k2.metric("Pending for Auction", pending_players)
        k3.metric("Auctioned So Far", auctioned_players)

        col_a,col_b = st.columns([3,1])
        with col_a:
            st.subheader("🏏 Current Auction")
            unauctioned_df = df[df['Auctioned']==False]
            pick_disabled = unauctioned_df.empty or bool(st.session_state.get('current_player'))
            if st.button("🎲 Pick Random Player", disabled=pick_disabled, key="pick_random"):
                available_players = unauctioned_df[~unauctioned_df['Player No'].isin([p['Player No'] for p in st.session_state['auction_results']])]
                if not available_players.empty:
                    selected_player = available_players.sample(1).iloc[0].to_dict()
                    st.session_state['current_player'] = selected_player
                    st.session_state['start_time'] = time.time()
                    st.rerun()
                else: st.warning("⚠️ No more players available for auction.")

            if st.session_state.get('current_player'):
                player = st.session_state['current_player']
                st.markdown(f"""
                <div class="fade-in" style="padding:15px;border-radius:12px;background:linear-gradient(135deg,#f09b13,#ffdd00);box-shadow:0 4px 15px rgba(0,0,0,0.2);">
                    <h2 style="margin:0;color:white;">🔥 {player['Player Name']}</h2>
                    <p style="margin:0;color:white;">Role: {player['Role']} | Player No: {player['Player No']}</p>
                </div>
                """, unsafe_allow_html=True)
                
                countdown_seconds = 60
                elapsed = int(time.time()-st.session_state['start_time']) if st.session_state['start_time'] else 0
                remaining = max(countdown_seconds-elapsed,0)
                color="#4CAF50" if remaining>40 else "#FFC107" if remaining>20 else "#F44336"
                percentage = int((remaining/countdown_seconds)*100)
                st.markdown(f"""
                <div class="countdown-container">
                    <div class="countdown-bar" style="width:{percentage}%;background-color:{color};"></div>
                </div>
                """, unsafe_allow_html=True)

                col1,col2,col3 = st.columns([2,1,1])
                team_names = [t['Team'] for t in st.session_state['teams']]
                selected_team = col1.selectbox("🏷️ Select Team", team_names, key="team_select")
                sold_price = col2.number_input("💰 Sold Price (₹)", min_value=0, step=10, key="sold_price")
                sold_button = col3.button("✅ Mark as Sold", key="mark_sold")
                unsold_button = st.button("❌ Mark as Unsold", key="mark_unsold")

                if sold_button and sold_price>0:
                    st.session_state['players_df'].loc[df['Player No']==player['Player No'],'Auctioned']=True
                    for team in st.session_state['teams']:
                        if team['Team']==selected_team:
                            team['Players'].append({'Player No':player['Player No'],'Player Name':player['Player Name'],'Role':player['Role'],'Price':sold_price})
                            team['Spent']+=sold_price
                            team['Budget']-=sold_price
                            break
                    st.session_state['auction_results'].append({'Player No':player['Player No'],'Player Name':player['Player Name'],'Role':player['Role'],'Team':selected_team,'Price':sold_price})
                    push_history({'type':'sold','player_no':player['Player No'],'team':selected_team,'price':sold_price,'player_row':dict(player)})
                    del st.session_state['current_player']
                    st.success(f"🎉 Player sold to {selected_team} for ₹{sold_price}!")
                    st.markdown(sound_html, unsafe_allow_html=True)
                    st.markdown('<script>launchConfetti();</script>', unsafe_allow_html=True)
                    st.rerun()
                if unsold_button:
                    st.session_state['players_df'].loc[df['Player No']==player['Player No'],'Auctioned']=True
                    st.session_state['auction_results'].append({'Player No':player['Player No'],'Player Name':player['Player Name'],'Role':player['Role'],'Team':'UNSOLD','Price':0})
                    push_history({'type':'unsold','player_no':player['Player No'],'team':'UNSOLD','price':0,'player_row':dict(player)})
                    del st.session_state['current_player']
                    st.info("🚫 Player marked as unsold.")
                    st.rerun()

            if st.session_state['teams']:
                team_df = pd.DataFrame([
                    {
                        'Team': t['Team'],
                        'Spent': t['Spent'],
                        'Remaining Budget': t['Budget'],
                        'Total Budget': t['Spent'] + t['Budget'],
                        'Players Bought': len(t.get('Players', []))  # Count of players bought
                    }
                    for t in st.session_state['teams']
                ])
                st.subheader("💰 Team Budget Overview")
                st.dataframe(team_df)

        col_b.empty()
        st.divider()
        st.subheader("📋 Auction Progress")
        st.markdown('<div class="fade-in">', unsafe_allow_html=True)
        st.dataframe(df)
        st.markdown('</div>', unsafe_allow_html=True)

# ---------- 4️⃣ Summary & Export ----------
with tab_summary:
    st.title("📊 Auction Summary")
    if not st.session_state['auction_results']:
        st.warning("⚠️ No results yet.")
    else:
        res_df = pd.DataFrame(st.session_state['auction_results'])
        st.subheader("📝 Auction Results")
        st.dataframe(res_df)
        with pd.ExcelWriter("auction_results.xlsx", engine='openpyxl') as writer:
            res_df.to_excel(writer, index=False, sheet_name="Combined Results")
            for team in st.session_state['teams']:
                players = team.get('Players', [])
                if players:
                    for p in players:
                        if 'Price' not in p: p['Price']=0
                    df_team = pd.DataFrame(players)[['Player No','Player Name','Role','Price']]
                    sheet_name = team['Team'][:31] if len(team['Team'])>31 else team['Team']
                    df_team.to_excel(writer,index=False,sheet_name=sheet_name)
        with open("auction_results.xlsx","rb") as f:
            st.download_button(label="⬇️ Download Excel File", data=f.read(), file_name="auction_results.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

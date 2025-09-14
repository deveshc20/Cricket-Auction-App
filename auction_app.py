import streamlit as st
import pandas as pd
import openpyxl
import time
import os

# ---------- SOUND EFFECT ----------
def play_sound():
    sound_path = "assets/bell.mp3"
    if os.path.exists(sound_path):
        audio_file = open(sound_path, 'rb')
        audio_bytes = audio_file.read()
        b64 = base64.b64encode(audio_bytes).decode()
        sound_html = f"""
        <audio autoplay>
            <source src="data:audio/mp3;base64,{b64}" type="audio/mp3">
        </audio>
        """
        st.markdown(sound_html, unsafe_allow_html=True)

# ---------- PAGE CONFIG ----------
st.set_page_config(page_title="Cricket Auction App", layout="wide")

st.sidebar.markdown("[🌐 GitHub](https://github.com/deveshc20)  |  🧑‍💻 Created by **DC**")
st.sidebar.title("🏏 Cricket Auction System")
page = st.sidebar.radio("Go to", ["1️⃣ Upload Players", "2️⃣ Team Setup", "3️⃣ Auction Panel", "4️⃣ Summary & Export"])

# ---------- SESSION INIT ----------
defaults = {
    'player_index': 0,
    'teams': [],
    'auction_results': [],
    'players_df': None,
    'current_bid': 20,
    'current_bid_team': None,
    'start_time': None,
}
for key, val in defaults.items():
    st.session_state.setdefault(key, val)

# ---------- 1️⃣ UPLOAD PLAYERS ----------
with tab_upload:
    st.title("📅 Upload Player List")
    uploaded_file = st.file_uploader("Upload Excel file", type=["xlsx"])
    canonical_required = {
        "player no": "Player No",
        "player name": "Player Name",
        "role": "Role",
    }

    if uploaded_file:
        try:
            df = pd.read_excel(uploaded_file)

            if all(col in df.columns for col in required_columns):
                df['Auctioned'] = False
                st.session_state['players_df'] = df.copy()
                st.success("✅ File uploaded successfully!")
                st.dataframe(df.head(10))
            else:
                missing = list(set(required_columns) - set(df.columns))
                st.error(f"Missing columns: {', '.join(missing)}")

        except Exception as e:
            st.error(f"Error reading file: {e}")
    else:
        st.info("Upload an Excel file with columns: Player No, Player Name, Role")

# ---------- 2️⃣ TEAM SETUP ----------
with tab_team:
    st.title("👥 Team Setup")
    num_teams = st.number_input("Number of teams", min_value=2, max_value=12, value=4, step=1, key="num_teams")

    with st.form("team_setup_form"):
        st.subheader("Enter Team Details")
        teams = []
        for i in range(num_teams):
            col1, col2 = st.columns([2, 1])
            name = col1.text_input(f"Team {i+1} Name", key=f"team_name_{i}")
            budget = col2.number_input(f"Budget (₹)", min_value=100, step=10, value=900, key=f"budget_{i}")
            teams.append({'Team': name.strip(), 'Budget': budget, 'Spent': 0, 'Players': []})
        submit = st.form_submit_button("✅ Save Teams")

    if submit:
        if all(team['Team'] for team in teams):
            st.session_state['teams'] = teams
            st.success("✅ Teams saved successfully!")
        else:
            st.error("❌ All team names are required.")

    if st.session_state['teams']:
        st.subheader("📋 Team Summary")
        st.dataframe(pd.DataFrame(st.session_state['teams']).drop(columns=['Players']))

# ---------- 3️⃣ AUCTION PANEL ----------
with tab_auction:
    st.title("🎯 Auction Panel")

    if 'players_df' not in st.session_state or st.session_state['players_df'].empty:
        st.warning("⚠️ Upload the player list first.")
    else:
        df = st.session_state['players_df']
        unauctioned_df = df[df['Auctioned'] == False]

        # --- KPI Metrics Row ---
        total_players = df.shape[0]
        pending_players = int((df['Auctioned'] == False).sum())
        auctioned_players = int((df['Auctioned'] == True).sum())

        k1, k2, k3 = st.columns(3)
        with k1:
            st.metric("Total Players", value=total_players)
        with k2:
            st.metric("Pending for Auction", value=pending_players)
        with k3:
            st.metric("Auctioned So Far", value=auctioned_players)

        col_a, col_b = st.columns([3, 1])

        with col_a:
            st.subheader("🏏 Current Auction")

            pick = st.button("🎲 Pick Random Player", disabled=unauctioned_df.empty)
            if pick:
                selected_player = unauctioned_df.sample(1).iloc[0].to_dict()
                st.session_state['current_player'] = selected_player
                st.session_state['start_time'] = time.time()
                st.rerun()

            if 'current_player' in st.session_state:
                player = st.session_state['current_player']
                st.markdown(f"**🔥 {player['Player Name']}**")
                st.markdown(f"**Role:** {player['Role']}  |  **Player No:** {player['Player No']}")

                countdown_seconds = 60
                elapsed = int(time.time() - st.session_state['start_time']) if st.session_state['start_time'] else 0
                remaining = max(countdown_seconds - elapsed, 0)
                st.markdown(f"⏱️ **Time Left:** {remaining} seconds")

                col1, col2, col3 = st.columns([2, 1, 1])
                team_names = [t['Team'] for t in st.session_state['teams']]
                selected_team = col1.selectbox("🏷️ Select Team", team_names, key="team_select")
                sold_price = col2.number_input("💰 Sold Price (₹)", min_value=0, step=10, key="sold_price")
                sold_button = col3.button("✅ Mark as Sold")
                unsold_button = st.button("❌ Mark as Unsold")

                    if sold_button:
                        if sold_price > 0:
                            df.loc[df['Player No'] == player['Player No'], 'Auctioned'] = True
                            for team in st.session_state['teams']:
                                if team['Team'] == selected_team:
                                    team['Players'].append(player)
                                    team['Spent'] += sold_price
                                    team['Budget'] -= sold_price
                                    break
                            st.session_state['auction_results'].append({
                                'Player No': player['Player No'],
                                'Player Name': player['Player Name'],
                                'Role': player['Role'],
                                'Team': selected_team,
                                'Price': sold_price
                            })
                            del st.session_state['current_player']
                            st.success(f"🎉 Player sold to {selected_team} for ₹{sold_price}!")
                            st.markdown(
    f"""
    <audio id="bell" autoplay>
        <source src="data:audio/mp3;base64,{sound_base64}" type="audio/mp3">
    </audio>
    <script>
        var audio = document.getElementById("bell");
        if (audio) {{
            audio.play().catch(error => console.log(error));
        }}
    </script>
    """,
    unsafe_allow_html=True
)
                        else:
                            st.warning("⚠️ Enter a valid price greater than 0.")

                if unsold_button:
                    df.loc[df['Player No'] == player['Player No'], 'Auctioned'] = True
                    st.session_state['auction_results'].append({
                        'Player No': player['Player No'],
                        'Player Name': player['Player Name'],
                        'Role': player['Role'],
                        'Team': 'UNSOLD',
                        'Price': 0
                    })
                    push_history({
                        'type': 'unsold',
                        'player_no': player['Player No'],
                        'team': 'UNSOLD',
                        'price': 0,
                        'player_row': dict(player)
                    })
                    del st.session_state['current_player']
                    st.info("🚫 Player marked as unsold.")
                    st.rerun()

            if st.session_state['teams']:
                team_df = pd.DataFrame([
                    {'Team': t['Team'], 'Spent': t['Spent'], 'Remaining Budget': t['Budget'],
                     'Total Budget': t['Spent'] + t['Budget']} for t in st.session_state['teams']
                ])
                st.subheader("💰 Team Budget Overview")
                st.dataframe(team_df)

        with col_b:
            # Previously separate budgets replaced by unified table above
            pass

        st.divider()
        st.subheader("📋 Auction Progress")
        st.dataframe(df)

# ---------- 4️⃣ SUMMARY & EXPORT ----------
elif page == "4️⃣ Summary & Export":
    st.title("📊 Auction Summary")

    if not st.session_state['auction_results']:
        st.warning("⚠️ No results yet.")
    else:
        res_df = pd.DataFrame(st.session_state['auction_results'])
        st.subheader("📝 Auction Results")
        st.dataframe(res_df)

    with pd.ExcelWriter("auction_results.xlsx", engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name="Results")
        for team in st.session_state['teams']:
            team_name = team['Team']
            players = team['Players']
            if players:
                team_df = pd.DataFrame(players)[['Player No', 'Player Name', 'Role']]
                team_df['Spent'] = team['Spent']
                team_df['Remaining Budget'] = team['Budget']
                team_df.to_excel(writer, index=False, sheet_name=team_name[:31])

    with open("auction_results.xlsx", "rb") as f:
        st.download_button(
            label="⬇️ Download Excel File",
            data=f.read(),
            file_name="auction_results.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        st.subheader("👥 Team Details")
        for team in st.session_state['teams']:
            with st.expander(f"{team['Team']} (💰 Left: ₹{team['Budget']:,})"):
                if team['Players']:
                    st.dataframe(pd.DataFrame(team['Players'])[['Player No', 'Player Name', 'Role']])
                else:
                    st.info("No players bought yet.")

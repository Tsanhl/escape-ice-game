import streamlit as st
from typing import List, Tuple, Optional
from collections import deque
import math
import random

# ========== GAME LOGIC ==========

def generate_grid() -> List[List[str]]:
    """
    Generate the base grid with some walls and random ice positions.
    """
    base_grid = [
        ['.', '.', '.', '.', '.', '.', '.', '.', '#', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.'],
        ['#', '.', '.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.'],
        ['.', '.', '.', '.', '.', '#', '.', '.', '.', '.'],
    ]
    R, C = len(base_grid), len(base_grid[0])
    num_ice = random.randint(3, 5)
    possible_positions = [
        (r, c)
        for r in range(R)
        for c in range(C//2, C)
        if base_grid[r][c] == '.'
        and (r, c) not in [(0, 0), (0, C-1)]
        and not (r < 3 and c < 3)
    ]
    random.shuffle(possible_positions)
    for i in range(min(num_ice, len(possible_positions))):
        r, c = possible_positions[i]
        base_grid[r][c] = 'I'
    return base_grid

def compute_ice_times(grid: List[List[str]], spread_interval: int) -> List[List[int]]:
    """
    For each cell, calculate when it will be frozen by ice (BFS).
    """
    R, C = len(grid), len(grid[0])
    directions = [(-1,0),(1,0),(0,-1),(0,1)]
    ice_time = [[math.inf]*C for _ in range(R)]
    q = deque()
    for r in range(R):
        for c in range(C):
            if grid[r][c] == 'I':
                ice_time[r][c] = 0
                q.append((r, c, 0))
    while q:
        r, c, t = q.popleft()
        dirs = directions[:]
        random.shuffle(dirs)
        for dr, dc in dirs[:random.randint(3,3)]:
            nr, nc = r+dr, c+dc
            if (0 <= nr < R and 0 <= nc < C
                and grid[nr][nc] != '#'
                and ice_time[nr][nc] > t + spread_interval):
                ice_time[nr][nc] = t + spread_interval
                q.append((nr, nc, t + spread_interval))
    return ice_time

def find_shortest_safe_steps(
        grid: List[List[str]],
        ice_time: List[List[int]]
    ) -> Optional[int]:
    """
    Find the shortest number of steps to reach the exit without freezing.
    """
    R, C = len(grid), len(grid[0])
    visited = [[False]*C for _ in range(R)]
    q = deque([(0,0,0)])
    visited[0][0] = True
    while q:
        r, c, steps = q.popleft()
        if (r, c) == (0, C-1):
            return steps
        for dr, dc in [(-1,0),(1,0),(0,-1),(0,1)]:
            nr, nc = r+dr, c+dc
            if (0 <= nr < R and 0 <= nc < C
                and not visited[nr][nc]
                and grid[nr][nc] != '#'
                and steps+1 < ice_time[nr][nc]):
                visited[nr][nc] = True
                q.append((nr, nc, steps+1))
    return None

def generate_balanced_ice(grid: List[List[str]], max_steps: int = 15) -> Tuple[List[List[int]], int]:
    """
    Ensure the ice spreads fast, but always possible to escape in < max_steps.
    """
    interval = 2
    while True:
        ice_time = compute_ice_times(grid, interval)
        shortest = find_shortest_safe_steps(grid, ice_time)
        if shortest is not None and shortest < max_steps:
            return ice_time, interval
        interval += 1
        #Try interval = 2  →  ice spreads fast   →  player can't escape  →  try next
        # Try interval = 3  →  ice a bit slower  →  player can't escape  →  try next
        # Try interval = 4  →  ice slower        →  player CAN escape in 13 steps → return!

def render_grid(grid, ice_time, current_steps, pos_r, pos_c):
    """
    Render the current state of the grid as HTML.
    """
    R, C = len(grid), len(grid[0])
    html = """
    <style>
      table { border-collapse: collapse; margin:20px auto;}
      td { width:40px; height:40px; text-align:center; font-size:24px; border:1px solid #ccc;}
      .wall { background:#333; color:#333;}
      .empty{ background:#fff;}
      .ice  { background:lightblue;}
      .player{background:green; color:#fff;}
      .exit{background:yellow;color:#000;}
    </style><table>"""
    for r in range(R):
        html += "<tr>"
        for c in range(C):
            if (r, c) == (pos_r, pos_c):
                html += '<td class="player">P</td>'
            elif (r, c) == (0, C-1):
                html += '<td class="exit">E</td>'
            elif grid[r][c] == '#':
                html += '<td class="wall"></td>'
            elif ice_time[r][c] <= current_steps:
                html += '<td class="ice"></td>'
            else:
                html += '<td class="empty"></td>'
        html += "</tr>"
    html += "</table>"
    return html

# ========== STREAMLIT APP ==========

st.set_page_config(page_title="Escape the Ice Game", layout="centered")
st.title("🧊 Escape the Ice Game")
st.info("**How to play:**\n- Use the four direction buttons to move the player (P).\n- Reach the exit (E) before the ice (blue) spreads to you!\n- If the ice covers you, game over. Good luck!")

if 'ice_time' not in st.session_state:
    grid = generate_grid()
    st.session_state.grid = grid
    ice_time, interval = generate_balanced_ice(grid)
    st.session_state.ice_time = ice_time
    st.session_state.interval = interval
    if ice_time[0][0] <= 0:
        st.error("Frozen at start! Game over.")
        st.stop()

if 'pos_r' not in st.session_state:
    st.session_state.pos_r = 0
    st.session_state.pos_c = 0
    st.session_state.current_steps = 0
    st.session_state.game_over = False
    st.session_state.won = False

grid = st.session_state.grid
ice_time = st.session_state.ice_time
pos_r = st.session_state.pos_r
pos_c = st.session_state.pos_c
current_steps = st.session_state.current_steps
R, C = len(grid), len(grid[0])
directions = {'Up':(-1,0),'Down':(1,0),'Left':(0,-1),'Right':(0,1)}

if st.session_state.won:
    st.success(f"🎉 Reached exit in {current_steps} steps!")
    if st.button("Restart"):
        for k in ['ice_time','grid','interval','pos_r','pos_c','current_steps','game_over','won']:
            if k in st.session_state:
                del st.session_state[k]
        st.experimental_rerun()
        st.stop()  # <--- Force halt after rerun!
elif st.session_state.game_over:
    st.error("💀 You froze! Game over.")
    if st.button("Restart"):
        for k in ['ice_time','grid','interval','pos_r','pos_c','current_steps','game_over','won']:
            if k in st.session_state:
                del st.session_state[k]
        st.experimental_rerun()
        st.stop()  # <--- Force halt after rerun!
else:
    st.markdown(render_grid(grid, ice_time, current_steps, pos_r, pos_c), unsafe_allow_html=True)
    cols = st.columns(4)
    buttons = {d: cols[i].button(d) for i,d in enumerate(directions)}
    for d, pressed in buttons.items():
        if not pressed: continue
        dr, dc = directions[d]
        nr, nc = pos_r+dr, pos_c+dc
        if 0<=nr<R and 0<=nc<C and grid[nr][nc] != '#':
            new_steps = current_steps + 1
            if new_steps >= ice_time[nr][nc]:
                st.session_state.game_over = True
                st.experimental_rerun()
            st.session_state.pos_r = nr
            st.session_state.pos_c = nc
            st.session_state.current_steps = new_steps
            if (nr, nc) == (0, C-1):
                st.session_state.won = True
            st.experimental_rerun()
        else:
            st.warning("Invalid move: wall or out of bounds!")

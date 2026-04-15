Here's the prompt for Figma AI:

---

# SpaceAI FC — Full UI Design

Keep the existing Champions League-themed header and dark background. Design the following screens inside the main content area. The overall vibe is premium football broadcast (like UCL coverage on CBS or BT Sport) — dark backgrounds, subtle gradients, glassmorphism cards, glowing accents, clean typography.

## Screen 1: Home / Dashboard

The landing screen after login. Shows all 12 features as a grid of clickable cards.

**Layout:**
- Welcome message at top: "Welcome back, [Name]" with a subtle greeting
- Below it: a large hero card for "Full Match Analysis" — the primary action, more prominent than others, maybe with a pitch background or gradient
- Below the hero: a 3-column grid (4 rows) of feature cards for the remaining 11 features
- Each card has: an icon, feature name, one-line description, and a subtle hover glow effect
- Cards should feel like premium glass panels on the dark background

**The 12 features with icons:**
1. 🏟️ Full Match Analysis — "Complete tactical breakdown"
2. 🔗 Pass Network — "Passing structure & key distributors"
3. 🗺️ Space Control — "Territorial dominance mapping"
4. 📐 Formation Detection — "Identify team shape & structure"
5. 💪 Press Resistance — "Measure pressing survival"
6. 🔍 Tactical Patterns — "Detect overlaps, blocks, overloads"
7. 🎯 Strategy Recommendations — "AI-powered tactical suggestions"
8. 👤 Player Assessment — "Scouting reports & radar charts"
9. 💬 Ask SpaceAI — "Tactical Q&A with AI"
10. ⚖️ Compare — "Side-by-side tactical comparison"
11. 🎮 Simulation — "What-if tactical testing"
12. 📝 Tactical Explanation — "Full match analysis report"

At the bottom of the page: a "Recent Analyses" section showing 3 most recent saved analyses as small cards with match name, date, and feature used.

## Screen 2: Feature Page — Input State

This is the template for any feature before the user runs analysis. Design it for "Space Control" as the example.

**Layout:**
- Feature header: icon + name + one-line description in a styled banner
- Below: three tabs — "Manual Entry" (active), "Video / YouTube", "Dataset Upload"
- Manual Entry tab content:
  - Two columns: Team A (left) and Team B (right)
  - Each column has: team name input, color picker, and a table of 11 player rows (name, number, x position, y position, position dropdown)
  - Below the columns: Ball Position (x, y inputs)
  - A prominent "Load Demo Data" button (gold/accent colored) that fills everything with sample data
- At the bottom: a large "Analyze" button — full width, glowing green accent, feels important
- Video tab: drag-and-drop upload zone with dotted border, plus a YouTube URL input field below
- Dataset tab: drag-and-drop upload zone for CSV/JSON files, with a preview table after upload

## Screen 3: Feature Page — Results State

Same page but after analysis is complete. Design it for "Space Control" as the example.

**Layout:**
- Results appear below the input section (input section collapses or stays visible with a toggle)
- **Visualizations section:** Two large pitch map images side by side (Voronoi map and Influence map) in dark card frames with subtle borders
- **Metrics row:** 3-4 metric cards in a row — glassmorphism style, showing:
  - "Team A Control: 54.3%" (with team color accent)
  - "Team B Control: 45.7%"
  - "Midfield Control: Team A 58%"
  - Each metric card has the number large and gold, label smaller and white
- **Zone Breakdown:** a horizontal bar or segmented bar showing defensive/middle/attacking third percentages for each team
- **Insights section:** a card with bullet points of key findings, each with a small icon (checkmark for strengths, warning for concerns)
- **Download section:** row of buttons — "Download PNG", "Download Report (DOCX)", "Save to History"

## Screen 4: Ask SpaceAI — Chat Interface

The AI tactical Q&A screen.

**Layout:**
- Header: "💬 Ask SpaceAI" with subtitle "Your AI tactical analyst"
- Main area: chat interface with dark background
  - User messages: right-aligned bubbles with a subtle accent color border
  - AI responses: left-aligned bubbles with a different style (maybe a slight glow or gradient edge), SpaceAI avatar icon next to each response
  - Responses should support markdown-like formatting (bold text, bullet points)
- Below the chat: "Try these examples" section with 4-5 clickable pill buttons:
  - "How to beat a low block?"
  - "Weaknesses of 4-3-3?"
  - "Best setup vs high press?"
  - "Half-space overloads explained"
- Input bar at the very bottom: text input field with a send button (like a modern chat app), plus an optional "Attach match data" toggle
- If no API key: show a subtle banner at top "Connect your AI key to unlock full responses"

## Screen 5: Player Assessment — Results

**Layout:**
- **Player Profile Card** at the top: large card with player name, number, position, age, preferred foot, team name. Styled like a football card or FIFA-style card with the dark premium theme.
- **Radar Chart:** a spider/radar chart showing all stats (speed, passing, dribbling, shooting, vision, etc.) with the team's accent color. This should be prominent and centered.
- **Role Classification:** a badge/label showing detected role (e.g., "Deep-Lying Playmaker") with confidence percentage
- **Scouting Report:** a text card with the AI-generated analysis, styled with good typography, maybe a quote-style left border accent
- **Heatmap:** if video data was used, show the player's movement heatmap on a pitch

## Screen 6: Compare — Side by Side

**Layout:**
- Two columns taking equal width
- Left column: Team A / Setup A visualizations, metrics, formation
- Right column: Team B / Setup B visualizations, metrics, formation
- Center divider line with "VS" badge
- Below the columns: a comparison table with rows for each metric, color-coded cells (green = advantage, red = disadvantage)
- At the bottom: "Verdict" card with the AI/template summary of who has the tactical advantage

## Screen 7: Simulation — Results

**Layout:**
- Simulation frame/animation displayed in a large dark card (the pitch with players)
- Below: score display styled like a matchday scoreboard (Team A 0 - 0 Team B)
- Stats comparison: side-by-side bars for possession, territorial control, shots
- If multiple runs: a small results table showing W/D/L record and averages
- Tactical insight card at the bottom with the analysis text

## Screen 8: Login / Sign Up

**Layout:**
- Centered card on the dark background
- SpaceAI FC logo at top of card
- "Welcome to SpaceAI FC" heading
- Email and password inputs with clean styling
- "Sign In" button (glowing accent)
- "Don't have an account? Sign Up" link below
- Sign Up page: same layout but with name, email, password, confirm password
- Optional: "Continue with Google" button

## Screen 9: History

**Layout:**
- "Your Analyses" heading
- List/grid of saved analysis cards, each showing:
  - Match name (e.g., "Barcelona vs Real Madrid")
  - Feature used (e.g., "Full Match Analysis")
  - Date and time
  - Small thumbnail of a visualization
  - Click to load the full results
- Filter/sort options at top: by date, by feature, search bar
- Empty state: "No analyses yet — start by running your first analysis!"

## Screen 10: Sidebar Navigation

A vertical sidebar on the left (collapsible).

**Layout:**
- SpaceAI FC logo and name at top
- Divider line
- "ANALYSIS" section label
- Feature list with icons — each item is clickable, active item has a glowing left border accent
- Group the features:
  - ANALYSIS: Full Match, Pass Network, Space Control, Formation, Press Resistance, Patterns
  - INTELLIGENCE: Strategy, Ask SpaceAI, Explanation
  - ADVANCED: Player Assessment, Compare, Simulation
- Divider line
- "History" link with clock icon
- "Settings" link with gear icon
- At the bottom: user avatar, name, and logout button
- The sidebar should feel like a premium navigation panel, not a basic list

## Design Tokens

- Background: #0D1117 or similar very dark navy/black
- Card backgrounds: rgba(255,255,255,0.05) with backdrop blur (glassmorphism)
- Primary accent: #1E88E5 (Champions League blue) or the blue from the existing header
- Secondary accent: #FFD700 (gold for metrics and highlights)
- Success: #4CAF50 (green for positive metrics)
- Danger: #F44336 (red for negative metrics/warnings)
- Text primary: #FFFFFF
- Text secondary: #9E9E9E
- Borders: rgba(255,255,255,0.1)
- Font: Inter or similar clean sans-serif

---

Design all screens in this Figma file. Each screen should be a separate frame/page. The design should look like it belongs on a Champions League broadcast — premium, dark, professional, with subtle glassmorphism and glow effects.
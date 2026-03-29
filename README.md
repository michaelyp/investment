# Investment Dashboard

A personal investment dashboard built for a Canadian investor managing GICs, dividend stocks (ENB, Royal Bank, Fortis), and US tech/AI equities (NVDA, MSFT, GOOGL).

## Features

- **Portfolio overview** — live P&L, allocation donut chart, signal summary
- **Holdings table** — per-stock cost basis, current value, profit/loss
- **Buy signals** — ENB yield-based entry zones + Nasdaq drawdown tech triggers + AI momentum scoring
- **GIC income tracker** — monthly payout math, compound vs payout strategy comparison
- **Tax optimization** — TFSA / RRSP / Taxable placement review with Canadian tax rules
- **Action plan** — monthly execution cycle, today's buy/hold/reduce list
- **Live data refresh** — uses Anthropic API with web search to fetch current prices

---

## Running locally

No server, no install, no Python needed.

1. Download `index.html`
2. Double-click it — opens in your browser
3. Done

That's it. The dashboard works completely offline with sample data.

### To enable live price refresh

1. Get a free Anthropic API key at https://console.anthropic.com
2. Open the dashboard in your browser
3. Click **"Set Anthropic API key"** in the sidebar
4. Paste your key (starts with `sk-ant-`)
5. Click **"↻ Refresh live data"**

The key is stored in memory only — it disappears when you close the tab and is never written anywhere.

---

## Editing your portfolio

Open `index.html` in any text editor and find this section near the bottom:

```javascript
let PORTFOLIO = [
  { ticker:"ENB.TO", name:"Enbridge",  shares:3000, cost:65.0,  price:72.00, acct:"TFSA",    type:"div",  sect:"Energy",    enbDiv:3.77 },
  { ticker:"RY.TO",  name:"Royal Bank",shares:500,  cost:130.0, price:175.00,acct:"Taxable", type:"div",  sect:"Banks" },
  ...
];
```

Edit the values to match your real holdings:
- `shares` — how many shares you own
- `cost` — your average purchase price (cost basis)
- `price` — current price (updated by live refresh, or set manually)
- `acct` — `"TFSA"`, `"RRSP"`, or `"Taxable"`
- `enbDiv` — ENB's annual dividend (used for yield calculations)

For GIC values, find:
```javascript
const GIC = [
  { lbl:"2-Year monthly payout", amt:300000, rate:3.54, tp:"m" },
  { lbl:"3-Year compound",       amt:200000, rate:3.72, tp:"c" },
];
```
Change `amt` and `rate` to match your actual GIC principal and rates.

---

## Deploying to GitHub Pages (free hosting)

### Step 1 — Create a GitHub account
Go to https://github.com and sign up if you don't have an account.

### Step 2 — Create a new repository
1. Click the **+** button (top right) → **New repository**
2. Name it: `investment-dashboard` (or anything you like)
3. Set visibility to **Public** (required for free GitHub Pages)
4. Click **Create repository**

### Step 3 — Upload the file
**Option A — via GitHub website (easiest):**
1. On your new repo page, click **"uploading an existing file"**
2. Drag and drop `index.html`
3. Scroll down, click **Commit changes**

**Option B — via Git command line:**
```bash
git init
git add index.html README.md
git commit -m "Initial dashboard"
git branch -M main
git remote add origin https://github.com/YOUR_USERNAME/investment-dashboard.git
git push -u origin main
```

### Step 4 — Enable GitHub Pages
1. Go to your repo → **Settings** tab
2. Click **Pages** in the left sidebar
3. Under **Source**, select **Deploy from a branch**
4. Branch: **main**, Folder: **/ (root)**
5. Click **Save**

### Step 5 — Access your live dashboard
After 1–2 minutes, your dashboard will be live at:
```
https://YOUR_USERNAME.github.io/investment-dashboard/
```

GitHub sends you an email when it's ready. You can also check Settings → Pages to see the URL.

---

## Updating your dashboard

When you want to update portfolio values or add new stocks:

1. Edit `index.html` locally
2. Go to your GitHub repo
3. Click on `index.html` → click the pencil icon (Edit)
4. Paste your updated code
5. Click **Commit changes**

GitHub Pages updates automatically within ~1 minute.

---

## Security notes

- **Never put your Anthropic API key in the code** — enter it via the UI only
- The API key input stores the key in browser memory only (cleared on tab close)
- Your GitHub repo is public, so don't add any personal financial data you want private
- For a private dashboard, upgrade to GitHub Pro ($4/month) and use a private repo

---

## How the live refresh works

When you click **Refresh live data**, the app:
1. Sends a request to the Anthropic API (claude-sonnet-4) with web search enabled
2. Asks Claude to look up current prices for all your tickers
3. Parses the JSON response and updates all calculations
4. The API key you entered is sent in the request header (standard API authentication)

This costs a few cents of Anthropic API credits per refresh (web search queries).

---

## Signals explained

### ENB yield zones
Enbridge is a dividend stock that trades like a bond. When rates rise, its price drops and yield rises. The dashboard uses yield (not price) to determine entry:
- 5.2–5.5% yield → small buy
- 5.8–6.2% → buy medium
- 6.5–7.0% → buy large
- 7%+ → all-in deploy

### AI momentum score
Each stock gets a score from -2 to +4 based on:
- Price vs cost basis (is it up or down?)
- Market regime: BULL (+1) or BEAR (-1)
- For tech stocks: Nasdaq drawdown level (bigger dip = higher score)

### Nasdaq drawdown triggers
- 0 to -5%: Hold
- -5%: Deploy 20% of tech cash
- -10%: Deploy another 30%
- -15%: Deploy another 30%
- -20%+: All remaining capital

---

*Not financial advice. This is a personal decision-support tool.*

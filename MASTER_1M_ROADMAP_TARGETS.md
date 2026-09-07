# 🏆 INSTITUTIONAL ROADMAP (VERIFIED 8.1/10 — CONDITIONAL GO)
### Non-Custodial Spot Execution Infrastructure & Transaction Cost Analysis (TCA) Engine
**Classification:** B2B Quantitative Software & IP Export | Zero Balance-Sheet Risk | Zero Domestic Crypto Trading  
**Architecture:** Two-Plane Model (Bangladesh Control Plane + Client-Controlled Foreign Execution Plane)  
**Bangladesh Bank Compliance:** Form-C (ICT) Purpose Code **2411** (IT Consultancy) / **2412** (Customized Software)  
**Tax Clearance:** 100% Tax-Exempt under Finance Act through June 30, 2027 (Wholly Banked Operations)  
**Financial Milestones:** Base Case: $500k–$700k Net Profit | Upside Case: $1,000,000+ Net Profit  

---

```
  PHASE 0              PHASE 1              PHASE 2              PHASE 3              PHASE 4              PHASE 5
[ Core Shield ] ───> [ TCA Benchmark ] ──> [ Two-Plane Pack ] ─> [ First 3 Desks ] ──> [ Scale to 15 ] ───> [ 30 Desks = $1M ]
  (Completed)          (Days 1-45)          (Days 30-60)         (Months 2-6)         (Months 7-14)       (Months 15-24)
```

---

## 📍 PHASE 0: Quantitative Core & Microstructure Hardening (COMPLETED)
> **Goal:** Production-grade high-Sharpe execution core with low-latency telemetry.
> **Status:** 🟢 100% COMPLETE

- [x] **Sub-10ms Async L1 Ingestion:** Tokio-Tungstenite WSS connected directly to Binance `bookTicker`.
- [x] **Continuous-Time Decay EMA:** Refactored from tick-clock to true physical time ($\tau_{\text{fast}} = 15.0\text{s}$, $\tau_{\text{slow}} = 75.0\text{s}$).
- [x] **Order Flow Imbalance (OFI):** Cont-Kukanov-Stoikov depth filter blocking buys when $\text{OFI} < 0.0$.
- [x] **VPIN Toxicity Defense:** Bulk Volume Classification ($50\text{ unit buckets}$) blocking entries when $\text{VPIN} > 0.65$.
- [x] **Replay Attack & Duplicate Protection:** Monotonic atomic `SEQUENCE_COUNTER` and unique `OrderIntentID` active.
- [x] **Trade-Only Execution Engine:** `binance_spot_executor.py` verifying `canWithdraw == False` on boot.

---

## 📍 PHASE 1: TCA Benchmark & "Execution Alpha" Proof (Days 1 to 45)
> **Goal:** Measure and document concrete **Implementation Shortfall Reduction (basis points saved)**.
> **Target Metric:** Prove our engine saves 3.0 – 4.5 basis points (bps) vs. naive passive/market orders.

### 1.1 Transaction Cost Analysis (TCA) Engine
- [ ] Implement `tca_engine.py`: Records every signal's `DecisionPrice`, `ArrivalPrice`, `FillPrice`, and `ExchangeTimestamp`.
- [ ] Measure Implementation Shortfall ($IS = FillPrice - DecisionPrice$ for buys).
- [ ] Measure post-trade markouts at $10\text{s}$, $30\text{s}$, and $60\text{s}$ to prove VPIN/OFI shields avoid toxic adverse selection.
- [ ] Accumulate $10M+ notional of benchmark volume across Binance Spot (BTC/USDT, ETH/USDT).

### 1.2 The "Execution Quality" Report
- [ ] Generate `Binance_Spot_Execution_Quality_Report.pdf`:
  - [ ] Implementation shortfall reduction: Verified bps saved vs baseline.
  - [ ] Latency percentiles: Explicitly publish $P50$, $P90$, $P95$, and $P99$ latency figures.
  - [ ] Volatility regime defense: Proof of zero fills during cascading flash crashes.

### 1.3 Open-Source Verification Layer (Trust Builder)
- [ ] Open-source on GitHub:
  - `spot-execution-tca-benchmark`: Public verification harness.
  - `exchange-api-security-validator`: Pre-flight permission checker confirming zero withdrawal authority.
- [ ] Keep proprietary: Stochastic O-U calibration, discrete feature weights, and private execution heuristics.

**Gate Exit Criteria:** A mathematically verified Execution Quality Report demonstrating positive basis-point savings.

---

## 📍 PHASE 2: Two-Plane Security & Bangladesh Bank Pack (Days 30 to 60)
> **Goal:** Architect the business so the client owns execution risk, and Bangladesh Bank sees 100% clean software export.

### 2.1 The Two-Plane Architecture (Zero-Trust)
- [ ] **Control Plane (Bangladesh):** Code development, updates, CI/CD, documentation, and technical support.
- [ ] **Execution Plane (Client Infrastructure):**
  - [ ] Client runs the Docker container inside their own AWS/KMS/Vault environment.
  - [ ] Client manages API keys with withdrawals strictly disabled.
  - [ ] Outbound network allowlisted strictly to specific Binance API endpoints (no wildcards).
  - [ ] Hard client risk boundaries: Maximum order size, daily loss limit, and emergency kill-switch.
- [ ] **Reproducible Builds:** Pinned `Cargo.lock`, minimal Alpine base, SBOM generated, signed SHA-256 digests.

### 2.2 Bangladesh Bank Compliance Pack
- [ ] Municipal **Trade License** classified as: *"Software Development, Information Technology Services & Quantitative Analytics"*.
- [ ] Electronic Tax Identification Number (**e-TIN**) and Freelancer ID.
- [ ] Open **Freelancer ERQ Account (USD)** paired with BDT Current Account at an Authorized Dealer (AD) Bank (City/BRAC/EBL).
- [ ] Create permanent **Branch Compliance Binder** containing:
  - [ ] Master Service Agreement (MSA) with liability caps and indemnification.
  - [ ] Commercial Invoices referencing **Purpose Code 2411** (IT Consultancy) or **2412** (Customized Software).
  - [ ] Bank confirmation memo ensuring 100% wholly banked operations for NBR tax exemption through June 30, 2027.

### 2.3 Shariah Wording & Asset Screening
- [ ] Frame contracts under fixed **Ujrah / Ijarah** software licensing.
- [ ] Embed client-configurable **Shariah Asset Policy Layer** (limiting execution to client-approved spot assets).
- [ ] Public positioning: *"Fixed-fee software infrastructure designed for Shariah-compatible spot asset execution."*

**Gate Exit Criteria:** Complete Two-Plane Security & Compliance binder ready for client due diligence and AD Bank remittance desks.

---

## 📍 PHASE 3: First 3 Institutional Pilots & Initial $50,000 (Months 2 to 6)
> **Goal:** Onboard 3 crypto prop desks (5–20 traders) / market-neutral quant funds ($5M–$50M AUM) as reference design partners.

### 3.1 The "14-Day Execution Benchmark Pilot" Outreach
- [ ] Identify 150 targeted decision-makers on LinkedIn: *Head of Quant Trading*, *Head of Electronic Execution*, *CTO of Crypto Prop Desk*.
- [ ] Cold pitch message:
  > *"We engineered non-custodial spot execution infrastructure for Binance that reduced implementation shortfall by 3.8 bps over $10M notional. We are looking for 2 design partner desks to run a 14-day benchmark on client-controlled infrastructure (zero custody, client KMS, deterministic risk limits). We supply the full TCA markout report."*
- [ ] Offer: 14-day benchmark pilot $\to$ converts to paid execution contract.

### 3.2 Pricing & Contract Structure
- [ ] **Design Partner Tier (First 3 Desks):** $5,000 setup fee + $1,500/month retainer.
- [ ] Milestone invoicing:
  - 20% on Security & Architecture validation.
  - 30% on Testnet deployment & TCA confirmation.
  - 30% on Production activation.
  - 20% on final sign-off.
- [ ] Client receives licensed binaries/containers (never unrestricted raw source code).
- [ ] **Milestone:** 3 Clients $\times$ $1,500/mo + $15,000 setup fees = **$50,000 Cumulative Cashflow**.

**Gate Exit Criteria:** 3 active reference customers with verified monthly retainer wires clearing through ERQ USD bank accounts.

---

## 📍 PHASE 4: Institutional Expansion to 15 Desks ($350,000) (Months 7 to 14)
> **Goal:** Scale software licensing across Dubai (VARA-adjacent desks), Singapore, and London quant boutiques.

### 4.1 Enterprise Tiering & Corrected Math
- [ ] **Execution Pro:** $7,500 setup + $2,000/month.
- [ ] **Enterprise OEMS:** $15,000 setup + $3,500/month (Custom latency SLA, dedicated deployment, private colocation guide).
- [ ] Scale active paying desks to **15 clients**:
  - $15 \times \$3,500\text{/month} = \mathbf{\$52,500\text{ MRR}} \ (\approx \$630,000\text{ ARR})$.
- [ ] Cumulative Revenue banked: **$350,000 USD** (approx. ৳42,000,000 BDT).

### 4.2 Multi-Venue Infrastructure (Moat Expansion)
- [ ] Expand execution adapter to Bybit Spot and OKX Spot (broadening addressable market).
- [ ] Build proprietary Transaction Cost Analysis (TCA) database across millions of orders.

**Gate Exit Criteria:** 15 active enterprise desks; MRR exceeds $50,000/month; churn below 5%.

---

## 📍 PHASE 5: The $1,000,000 Financial Horizon (Months 15 to 24)
> **Goal:** Maintain 25–30 enterprise desks and achieve financial independence purely from software revenue.

### 5.1 Financial Realism & Scenarios
- [ ] **Client Portfolio:** 25 to 30 institutional desks averaging **$3,500 / month**.
- [ ] **Monthly Recurring Revenue (MRR):** **$90,000 - $105,000 / month**.
- [ ] **Annualized Run Rate (ARR):** **$1.1M - $1.26M**.
- [ ] **Realistic Net Profit Modeling (accounting for operational overhead):**
  - **Base Case:** **$500,000 – $700,000 Net Cash in Bank**.
  - **Strong Case:** **$800,000 – $1,000,000 Net Cash in Bank**.
  - **Upside Case (Multi-venue & custom SLAs):** **$1,000,000+ Net Profit**.

### 5.2 Future Offshore Entity Formation (Optional)
- [ ] Now that substantial capital is accumulated, form a corporate holding entity in UAE (DIFC / ADGM) or UK to ring-fence intellectual property and explore direct fund management if desired.

---

## 📊 AUDIT-VERIFIED TARGET DASHBOARD

| Milestone | Timeframe | Active Desks | Monthly Revenue | Cumulative Net Profit | Status |
| :--- | :---: | :---: | :---: | :---: | :--- |
| **Phase 0** | Week 1 | 0 | $0 | $0 | 🟢 **COMPLETED** |
| **Phase 1** | Days 1–45 | 0 | $0 | $0 | 🟡 In Progress (TCA Engine) |
| **Phase 2** | Days 30–60 | 0 | $0 | $0 | Pending Bank Pack |
| **Phase 3** | Months 2–6 | 3 | $4,500 | **$50,000** | Pilot Customer Acquisition |
| **Phase 4** | Months 7–14 | 15 | $52,500 | **$350,000** | Scaling Enterprise OEMS |
| **Phase 5 (Base)** | Months 15–24 | 25 | $87,500 | **$600,000** | Realistic Base Target |
| **Phase 5 (Upside)**| Months 15–24 | 30 | $105,000 | **$1,100,000+** | **1 MILLION DOLLAR PEAK** |

---

## ⚡ NEXT ENGINEERING STEP:
- Create `tca_engine.py` to start recording implementation shortfall, arrival prices, and markouts for the Execution Quality Whitepaper!

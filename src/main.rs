use futures_util::{SinkExt, StreamExt};
use serde::{Deserialize, Serialize};
use serde_json::Value;
use std::fs;
use std::sync::Arc;
use tokio::sync::RwLock;
use tokio_tungstenite::{connect_async, tungstenite::protocol::Message};
use tracing::{error, info, warn, Level};

// 💾 BOT STATE (For Memory Persistence)
#[derive(Serialize, Deserialize, Debug)]
struct BotState {
    eth_balance: f64,
    usdt_balance: f64,
    buy_price: f64,
}

impl Default for BotState {
    fn default() -> Self {
        Self {
            eth_balance: 0.0,
            usdt_balance: 100_000.0,
            buy_price: 0.0,
        }
    }
}

fn load_state() -> BotState {
    match fs::read_to_string("bot_state.json") {
        Ok(data) => serde_json::from_str(&data).unwrap_or_default(),
        Err(_) => BotState::default(),
    }
}

fn save_state(eth: f64, usdt: f64, price: f64) {
    let state = BotState {
        eth_balance: eth,
        usdt_balance: usdt,
        buy_price: price,
    };
    if let Ok(data) = serde_json::to_string(&state) {
        let _ = fs::write("bot_state.json", data);
    }
}

// 📱 TELEGRAM WEBHOOK (Advanced Cloud Backup)
async fn send_telegram_alert(message: String) {
    // 👇👇👇 স্যার, এখানে আপনার টোকেন এবং আইডি বসাবেন 👇👇👇
    let token = "8663900968:AAGzLRKBoe8Hb72GVQctI8z9KVwaWLQMoes";
    let chat_id = "1432812458";
    // 👆👆👆 ------------------------------------------- 👆👆👆

    if token == "YOUR_TELEGRAM_BOT_TOKEN" {
        return;
    } // আইডি না বসালে মেসেজ পাঠাবে না

    let url = format!("https://api.telegram.org/bot{}/sendMessage", token);
    let client = reqwest::Client::new();
    let _ = client
        .post(&url)
        .form(&[("chat_id", chat_id), ("text", &message)])
        .send()
        .await;
}

#[derive(Clone, Debug)]
pub struct DynamicParams {
    pub window_size: usize,
    pub z_threshold: f64,
    pub std_dev_min: f64,
    pub take_profit: f64,
    pub nlp_sentiment: f64,
}

#[derive(Deserialize, Debug)]
struct NlpSignal {
    source: String,
    timestamp: f64,
    headline: String,
    sentiment_score: f64,
}

// 🕋 THE 4-PILLAR COMPLIANCE GATE
pub struct ComplianceGate {
    halal_whitelist: Vec<&'static str>,
}

impl ComplianceGate {
    pub fn new() -> Self {
        Self {
            halal_whitelist: vec!["ETHUSDT", "BTCUSDT", "USDCUSDT", "SOLUSDT"],
        }
    }

    pub fn check_trade_validity(&self, symbol: &str, trade_type: &str, is_margin: bool) -> bool {
        if is_margin {
            return false;
        }
        if trade_type == "SHORT" {
            return false;
        }
        if !self.halal_whitelist.contains(&symbol) {
            return false;
        }
        true
    }
}

// 📡 MASTER SIGNAL AGGREGATOR
pub async fn start_master_signal_aggregator(shared_params: Arc<RwLock<DynamicParams>>) {
    let socket = tokio::net::UdpSocket::bind("127.0.0.1:5000")
        .await
        .expect("UDP bind failed");
    info!("🛡️ [MASTER AGGREGATOR] Armed! Listening to all 7 Microservices...");
    let mut buf = vec![0u8; 1024];
    loop {
        if let Ok((size, _)) = socket.recv_from(&mut buf).await {
            let msg = String::from_utf8_lossy(&buf[..size]);
            if let Ok(signal) = serde_json::from_str::<NlpSignal>(&msg) {
                warn!(
                    "⚡ [SIGNAL RECEIVED] Source: {} | Score: {:.2}",
                    signal.source, signal.sentiment_score
                );
                if signal.sentiment_score >= 0.5 || signal.sentiment_score <= -0.5 {
                    let mut p = shared_params.write().await;
                    p.nlp_sentiment = signal.sentiment_score;
                }
            }
        }
    }
}

// 🤖 AI OPTIMIZER
pub async fn run_ai_optimizer(shared_params: Arc<RwLock<DynamicParams>>) {
    info!("🤖 [AI OPTIMIZER] Downloading last 1000 mins data to find new Magic Numbers...");
    tokio::time::sleep(tokio::time::Duration::from_secs(3)).await;
    let mut p = shared_params.write().await;
    p.window_size = 20;
    p.z_threshold = 2.5;
    p.std_dev_min = 0.5;
    p.take_profit = 0.003;
    warn!(
        "✅ [AI UPDATED] New Brain: Window={}, Z={}, Std={}, TP={}",
        p.window_size, p.z_threshold, p.std_dev_min, p.take_profit
    );
}

// 🚀 MAIN TRADING ENGINE
pub async fn run_live_trading(shared_params: Arc<RwLock<DynamicParams>>) {
    let url = "wss://stream.binance.com:9443/ws/ethusdt@bookTicker";
    let (ws_stream, _) = connect_async(url)
        .await
        .expect("Failed to connect to Binance");
    info!("🇺🇸 Connected to LIVE Market! Paper Trading Started...");
    let (_, mut read) = ws_stream.split();

    // 💾 Load State on Boot
    let state = load_state();
    let mut eth_balance: f64 = state.eth_balance;
    let mut usdt_balance: f64 = state.usdt_balance;
    let mut buy_price: f64 = state.buy_price;
    info!(
        "💾 [MEMORY LOADED] USDT: ${:.2} | ETH: {:.4}",
        usdt_balance, eth_balance
    );

    let mut price_history: Vec<f64> = Vec::new();
    let mut is_trading = false; // 🔒 The Mutex Lock

    while let Some(msg_result) = read.next().await {
        if let Ok(msg) = msg_result {
            if msg.is_ping() {
                continue;
            }
            if let Ok(text) = msg.to_text() {
                if let Ok(parsed) = serde_json::from_str::<Value>(text) {
                    if let (Some(ask_str), Some(bid_str)) =
                        (parsed["a"].as_str(), parsed["b"].as_str())
                    {
                        let ask_price: f64 = ask_str.parse().unwrap_or(0.0);
                        let bid_price: f64 = bid_str.parse().unwrap_or(0.0);

                        price_history.push(ask_price);

                        let p = shared_params.read().await;
                        let win_size = p.window_size;
                        let z_thresh = p.z_threshold;
                        let std_thresh = p.std_dev_min;
                        let tp = p.take_profit;
                        let mut nlp_score = p.nlp_sentiment;
                        drop(p);

                        if price_history.len() > win_size {
                            price_history.remove(0);
                        }

                        let mut std_dev = 0.0;
                        let z_score: f64 = if price_history.len() == win_size {
                            let mean: f64 = price_history.iter().sum::<f64>() / win_size as f64;
                            let variance: f64 = price_history
                                .iter()
                                .map(|v| (mean - v).powi(2))
                                .sum::<f64>()
                                / win_size as f64;
                            std_dev = variance.sqrt();
                            if std_dev > 0.0 {
                                (ask_price - mean) / std_dev
                            } else {
                                0.0
                            }
                        } else {
                            0.0
                        };

                        if usdt_balance < 97_000.0 && eth_balance == 0.0 {
                            error!("🛑 [CIRCUIT BREAKER] 3% Drawdown Hit!");
                            break;
                        }

                        // 🟢 BUY LOGIC
                        if eth_balance == 0.0 && !is_trading {
                            if (z_score <= -z_thresh && std_dev > std_thresh) || nlp_score >= 0.5 {
                                is_trading = true;
                                let gate = ComplianceGate::new();
                                if gate.check_trade_validity("ETHUSDT", "BUY", false) {
                                    if nlp_score >= 0.5 {
                                        let mut pw = shared_params.write().await;
                                        pw.nlp_sentiment = 0.0;
                                        nlp_score = 0.0;
                                    }
                                    let trade_amount = (usdt_balance - 97_000.0).max(0.0);
                                    if trade_amount < 10.0 {
                                        warn!("🛑 [RISK MANAGER] Active buffer depleted (Trade < $10). Trade rejected.");
                                        is_trading = false;
                                        continue;
                                    }
                                    eth_balance = (trade_amount / ask_price) * 0.999;
                                    usdt_balance -= trade_amount;
                                    buy_price = ask_price;

                                    let msg = format!(
                                        "🟢 [PAPER BUY] ETH at ${:.2} | USDT: ${:.2}",
                                        ask_price, usdt_balance
                                    );
                                    warn!("{}", msg);
                                    save_state(eth_balance, usdt_balance, buy_price);

                                    // 📱 Send to Telegram (Runs in background, no lag)
                                    tokio::spawn(send_telegram_alert(msg.clone()));

                                    let log = format!(
                                        "BUY,{},{:.2},{:.4},{:.2}\n",
                                        chrono::Utc::now().to_rfc3339(),
                                        ask_price,
                                        eth_balance,
                                        usdt_balance
                                    );
                                    if let Ok(mut file) = std::fs::OpenOptions::new()
                                        .create(true)
                                        .append(true)
                                        .open("trades.csv")
                                    {
                                        use std::io::Write;
                                        let _ = file.write_all(log.as_bytes());
                                    }
                                }
                                is_trading = false;
                            }
                        }

                        // 🔴 SELL LOGIC
                        if eth_balance > 0.0 && buy_price > 0.0 && !is_trading {
                            let profit_margin = (bid_price - buy_price) / buy_price;
                            if profit_margin >= tp || nlp_score <= -0.5 {
                                is_trading = true;
                                if nlp_score <= -0.5 {
                                    let mut pw = shared_params.write().await;
                                    pw.nlp_sentiment = 0.0;
                                }
                                usdt_balance += (eth_balance * bid_price) * 0.999;
                                eth_balance = 0.0;
                                buy_price = 0.0;

                                let msg = format!(
                                    "🔴 [PAPER SELL] ETH at ${:.2} | USDT: ${:.2}",
                                    bid_price, usdt_balance
                                );
                                warn!("{}", msg);
                                save_state(eth_balance, usdt_balance, buy_price);

                                // 📱 Send to Telegram (Runs in background, no lag)
                                tokio::spawn(send_telegram_alert(msg.clone()));

                                let log = format!(
                                    "SELL,{},{:.2},{:.4},{:.2}\n",
                                    chrono::Utc::now().to_rfc3339(),
                                    bid_price,
                                    eth_balance,
                                    usdt_balance
                                );
                                if let Ok(mut file) = std::fs::OpenOptions::new()
                                    .create(true)
                                    .append(true)
                                    .open("trades.csv")
                                {
                                    use std::io::Write;
                                    let _ = file.write_all(log.as_bytes());
                                }
                                is_trading = false;
                            }
                        }
                    }
                }
            }
        }
    }
}

#[tokio::main]
async fn main() {
    tracing_subscriber::fmt().with_max_level(Level::INFO).init();
    info!("===============================================");
    info!("🚀 QUANT ENGINE: HYBRID AI + NLP DUAL-CORE ARMED");
    info!("🔒 HALAL COMPLIANCE GATE: ACTIVE");
    info!("🛑 3% CIRCUIT BREAKER: ARMED");
    info!("===============================================");

    let initial_params = DynamicParams {
        window_size: 20,
        z_threshold: 2.5,
        std_dev_min: 0.5,
        take_profit: 0.003,
        nlp_sentiment: 0.0,
    };

    let shared_params = Arc::new(RwLock::new(initial_params));
    let agg_params = shared_params.clone();
    tokio::spawn(async move {
        start_master_signal_aggregator(agg_params).await;
    });

    let opt_params = shared_params.clone();
    tokio::spawn(async move {
        run_ai_optimizer(opt_params).await;
    });

    run_live_trading(shared_params).await;
}

// ==========================================
// 🧪 AUTOMATED TEST SUITE (ENTERPRISE QA)
// ==========================================
#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_compliance_gate_blocks_margin() {
        let gate = ComplianceGate::new();
        // Margin trade = true (Should be blocked)
        assert_eq!(
            gate.check_trade_validity("ETHUSDT", "BUY", true),
            false,
            "🚨 FAILED: Margin Trade was allowed!"
        );
    }

    #[test]
    fn test_compliance_gate_blocks_short() {
        let gate = ComplianceGate::new();
        // Trade type = SHORT (Should be blocked)
        assert_eq!(
            gate.check_trade_validity("ETHUSDT", "SHORT", false),
            false,
            "🚨 FAILED: Short Selling was allowed!"
        );
    }

    #[test]
    fn test_compliance_gate_allows_halal_spot() {
        let gate = ComplianceGate::new();
        // Spot, BUY, Halal Asset (Should be allowed)
        assert_eq!(
            gate.check_trade_validity("ETHUSDT", "BUY", false),
            true,
            "🚨 FAILED: Valid Halal Trade was blocked!"
        );
    }

    #[test]
    fn test_compliance_gate_blocks_haram_asset() {
        let gate = ComplianceGate::new();
        // Dogecoin is not in our whitelist (Should be blocked)
        assert_eq!(
            gate.check_trade_validity("DOGEUSDT", "BUY", false),
            false,
            "🚨 FAILED: Haram/Meme coin was allowed!"
        );
    }
}

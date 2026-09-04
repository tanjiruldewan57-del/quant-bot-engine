use reqwest;
use std::collections::HashMap;

struct QuantBrain {
    price_history: Vec<f64>,
    window_size: usize,
}

impl QuantBrain {
    fn new(window_size: usize) -> Self {
        Self {
            price_history: Vec::new(),
            window_size,
        }
    }

    fn add_price(&mut self, price: f64) {
        self.price_history.push(price);
        if self.price_history.len() > self.window_size {
            self.price_history.remove(0);
        }
    }

    fn get_stats(&self, current_price: f64) -> (f64, f64) {
        if self.price_history.len() < self.window_size {
            return (0.0, 0.0);
        }
        let mean = self.price_history.iter().sum::<f64>() / self.price_history.len() as f64;
        let variance = self
            .price_history
            .iter()
            .map(|v| (mean - v).powi(2))
            .sum::<f64>()
            / self.price_history.len() as f64;
        let std_dev = variance.sqrt();
        if std_dev == 0.0 {
            return (0.0, 0.0);
        }
        let z_score = (current_price - mean) / std_dev;
        (z_score, std_dev)
    }
}

struct Portfolio {
    usdt_balance: f64,
    assets: HashMap<String, f64>,
    buy_price: f64,
    fee_rate: f64,
    total_trades: u32,
}

impl Portfolio {
    fn new() -> Self {
        Self {
            usdt_balance: 100_000.0,
            assets: HashMap::new(),
            buy_price: 0.0,
            fee_rate: 0.001,
            total_trades: 0,
        }
    }

    fn buy(&mut self, symbol: &str, ask_price: f64, z_score: f64) {
        // BULL-RUN SIZING: মার্কেট বেশি ক্র্যাশ করলে বেশি ইনভেস্ট করবে
        let multiplier = if z_score.abs() >= 3.0 {
            10.0
        } else if z_score.abs() >= 2.5 {
            5.0
        } else {
            1.0
        };
        let trade_amount = 1000.0 * multiplier;

        if self.usdt_balance >= trade_amount {
            let coin_to_buy = trade_amount / ask_price;
            let fee = coin_to_buy * self.fee_rate;
            self.usdt_balance -= trade_amount;
            *self.assets.entry(symbol.to_string()).or_insert(0.0) += coin_to_buy - fee;
            self.buy_price = ask_price;
            self.total_trades += 1;
        }
    }

    fn sell(&mut self, symbol: &str, bid_price: f64) {
        if let Some(coin_balance) = self.assets.get_mut(symbol) {
            if *coin_balance > 0.0 {
                let usdt_received = *coin_balance * bid_price;
                let fee = usdt_received * self.fee_rate;
                self.usdt_balance += usdt_received - fee;
                *coin_balance = 0.0;
                self.buy_price = 0.0;
            }
        }
    }

    fn total_value(&self, current_price: f64, symbol: &str) -> f64 {
        let coin_value = self.assets.get(symbol).unwrap_or(&0.0) * current_price;
        self.usdt_balance + coin_value
    }
}

fn run_simulation(
    prices: &Vec<f64>,
    window_size: usize,
    z_threshold: f64,
    min_std_dev: f64,
    take_profit_pct: f64,
) -> (f64, u32) {
    let mut portfolio = Portfolio::new();
    let mut brain = QuantBrain::new(window_size);
    let symbol = "ETHUSDT";
    let mut last_price = 0.0;

    for &close_price in prices {
        last_price = close_price;
        brain.add_price(close_price);

        // Take Profit Logic (সঠিক লাভে বিক্রি করবে)
        if portfolio.assets.get(symbol).unwrap_or(&0.0) > &0.0 {
            let profit_margin = (close_price - portfolio.buy_price) / portfolio.buy_price;
            if profit_margin >= take_profit_pct {
                portfolio.sell(symbol, close_price);
                continue;
            }
        }

        if brain.price_history.len() == window_size {
            let (z_score, std_dev) = brain.get_stats(close_price);

            if portfolio.assets.get(symbol).unwrap_or(&0.0) == &0.0 {
                if z_score <= -z_threshold && std_dev > min_std_dev {
                    portfolio.buy(symbol, close_price, z_score);
                }
            }
        }
    }

    let profit = portfolio.total_value(last_price, symbol) - 100_000.0;
    (profit, portfolio.total_trades)
}

#[tokio::main]
async fn main() {
    println!("🤖 STARTING ULTIMATE BULL-RUN AI OPTIMIZER...");

    let url = "https://api.binance.us/api/v3/klines?symbol=ETHUSDT&interval=1m&limit=1000";
    let raw_text = reqwest::get(url).await.unwrap().text().await.unwrap();
    let response: Vec<Vec<serde_json::Value>> = serde_json::from_str(&raw_text).unwrap();

    let mut prices = Vec::new();
    for kline in response {
        let close_price: f64 = kline[4].as_str().unwrap().parse().unwrap();
        prices.push(close_price);
    }

    let mut max_profit = -9999.0;
    let mut best_window = 0;
    let mut best_z_score = 0.0;
    let mut best_std_dev = 0.0;
    let mut best_tp = 0.0;
    let mut best_trades = 0;

    let windows = [15, 20, 30, 40];
    let z_scores = [1.8, 2.0, 2.3, 2.5, 2.7];
    let std_devs = [0.1, 0.3, 0.5]; // হালকা মুভমেন্টেও ট্রেড করবে
    let take_profits = [0.002, 0.003, 0.005, 0.01]; // 0.2%, 0.3%, 0.5%, 1%

    for &w in &windows {
        for &z in &z_scores {
            for &s in &std_devs {
                for &tp in &take_profits {
                    let (profit, trades) = run_simulation(&prices, w, z, s, tp);

                    if profit > max_profit {
                        max_profit = profit;
                        best_window = w;
                        best_z_score = z;
                        best_std_dev = s;
                        best_tp = tp;
                        best_trades = trades;
                    }
                }
            }
        }
    }

    println!("======================================");
    println!("🏆 ULTIMATE AI OPTIMIZATION COMPLETE!");
    println!("======================================");
    println!("⭐ BEST WINDOW            : {} mins", best_window);
    println!("⭐ BEST Z-SCORE           : {:.1}", best_z_score);
    println!("⭐ DEAD MARKET FILTER     : > {:.1}", best_std_dev);
    println!("⭐ TAKE PROFIT TARGET     : {:.2}%", best_tp * 100.0);
    println!("💰 MAX PROFIT EARNED      : ${:.2}", max_profit);
    println!("🔄 TOTAL TRADES EXECUTED  : {}", best_trades);
    println!("======================================");
}

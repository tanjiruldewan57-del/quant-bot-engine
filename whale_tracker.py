import time
import json
import socket
import requests

class OnChainWhaleTracker:
    def __init__(self):
        # 3টি আলাদা পাবলিক সার্ভার, একটি ফেইল করলে অন্যটিতে অটো শিফট করবে!
        self.rpc_urls = [
            "https://eth-mainnet.public.blastapi.io",
            "https://ethereum-rpc.publicnode.com",
            "https://cloudflare-eth.com"
        ]
        self.current_rpc_index = 0
        
        self.udp_ip = "127.0.0.1"
        self.udp_port = 5000
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        
        self.last_block_checked = None
        self.whale_threshold_eth =  200.0
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)',
            'Content-Type': 'application/json'
        }
        
        print(f"[WHALE TRACKER] Armed with Multi-RPC Failover System...")

    def get_active_rpc(self):
        return self.rpc_urls[self.current_rpc_index]

    def switch_rpc(self):
        self.current_rpc_index = (self.current_rpc_index + 1) % len(self.rpc_urls)
        print(f"🔄 [RPC SWITCH] Switching to new node: {self.get_active_rpc()}")

    def get_latest_block_number(self):
        payload = {"jsonrpc":"2.0", "method":"eth_blockNumber", "params":[], "id":1}
        try:
            res = requests.post(self.get_active_rpc(), json=payload, headers=self.headers, timeout=5)
            data = res.json()
            if 'result' in data:
                return int(data['result'], 16)
            else:
                print(f"⚠️ [RPC ERROR] {data.get('error', data)}")
                self.switch_rpc()
                return None
        except Exception as e:
            print(f"⚠️ [NETWORK ERROR] Node failed responding.")
            self.switch_rpc()
            return None

    def get_block_transactions(self, block_number):
        hex_block = hex(block_number)
        payload = {"jsonrpc":"2.0", "method":"eth_getBlockByNumber", "params":[hex_block, True], "id":1}
        try:
            res = requests.post(self.get_active_rpc(), json=payload, headers=self.headers, timeout=10)
            data = res.json()
            if 'result' in data and data['result'] is not None:
                return data['result'].get('transactions', [])
            return []
        except Exception:
            return []

    def scan_for_whales(self):
        latest_block = self.get_latest_block_number()
        if not latest_block:
            return
            
        if latest_block == self.last_block_checked:
            return

        print(f"[SCANNING] Ethereum Block {latest_block}...")
        transactions = self.get_block_transactions(latest_block)
        
        whale_detected = False
        total_whale_eth = 0

        for tx in transactions:
            try:
                value_wei = int(tx.get('value', '0x0'), 16)
                value_eth = value_wei / 1e18
                
                if value_eth >= self.whale_threshold_eth:
                    whale_detected = True
                    total_whale_eth += value_eth
                    print(f"🚨 [WHALE ALERT] {value_eth:.2f} ETH moved! TX: {tx.get('hash')}")
            except Exception:
                pass

        if whale_detected:
            signal_data = {
                "source": "WHALE_BOT",
                "timestamp": time.time(),
                "headline": f"ON-CHAIN WHALE: {total_whale_eth:.2f} ETH Moved!",
                "sentiment_score":  0.60
            }
            message = json.dumps(signal_data).encode('utf-8')
            self.sock.sendto(message, (self.udp_ip, self.udp_port))
            print(f"⚡ [ACTION] Sent Whale Signal to Rust Engine!")

        self.last_block_checked = latest_block

    def run(self):
        while True:
            self.scan_for_whales()
            time.sleep(12)

if __name__ == "__main__":
    bot = OnChainWhaleTracker()
    bot.run()
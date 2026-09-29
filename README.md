# Room No 114 - Kirana Store POS & Multi-Partner Sync

A real-time Kirana Point of Sale (POS) and inventory management web application with multi-device live synchronization designed for store partners.

## 🚀 Features

- **Live Inventory Management**: Track stock levels, low-stock warnings, purchase costs, and selling prices.
- **Quick Billing / POS**: Fast sale entries with support for Cash, UPI, and Customer Credit (Khata).
- **Khata Ledger**: Customer credit book tracking with payment settlement.
- **Profit & Revenue Analytics**: Real-time gross margin and profit calculations.
- **5-Partner Live Sync**: Instant synchronization across counter PC and partners' mobile devices over Wi-Fi or public cloud link.
- **PIN Security**: Built-in 4-digit passkey protection (`0471`).

## 🛠️ How to Run Locally

1. Double-click `start_server.bat` OR run:
   ```bash
   python server.py
   ```
2. Open your browser and navigate to:
   ```
   http://localhost:8080/index.html
   ```

## 📁 Repository Structure

- `index.html`: Complete Kirana store web application frontend and local logic.
- `server.py`: Python HTTP server with live synchronization endpoint (`/api/sync`).
- `store_state.json`: Local JSON database holding inventory, sales, customers, and khata records.
- `start_server.bat`: 1-click launcher for the local server and live tunnel.

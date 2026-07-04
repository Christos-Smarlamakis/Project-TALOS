TradingAgent: Intraday Trading with S&P 500 Data
📌 Overview

This project implements an intraday trading agent using a Dueling Double DQN architecture for stock market predictions based on S&P 500 data. The agent is designed for reinforcement learning-based trading, making dynamic decisions using historical market data and a rolling window approach.

🚀 Features
   
    Dueling Double DQN Architecture for stable reinforcement learning.
    
    Rolling Window Approach allowing the agent to adapt to market conditions.
    
    Intraday Trading Simulation with position management.
    
    Experience Replay for improved training efficiency.
    
    Feature Engineering using RSI, MACD, Bollinger Bands, ATR, Stochastic Oscillator.
    
    Portfolio Management with risk assessment and profit/loss optimization.

📂 Project Structure

├── model.py           # Dueling Double DQN model with LSTM layers  
├── replay_memory.py   # Experience replay buffer for storing transitions  
├── ddqn_agent.py      # Deep Q-learning agent with target and online networks  
├── data_processing.py # Stock market data processing & feature extraction  
├── environment.py     # Trading environment with reward and risk calculations  
├── main.py            # Execution pipeline for training and trading  
├── requirements.txt   # Dependencies for running the project  
└── README.md          # Project documentation  

🔧 Installation & Setup

1️⃣ Clone the repository
git clone https://github.com/MrV0/TradingAgent.git

2️⃣ Install dependencies
pip install -r requirements.txt

3️⃣ Set up the data source

Modify data_processing.py to define the path to the dataset:
self.stock_path = r"\your_dataset.csv"  # Update file path here

In main.py, configure:
   
    Training start date (INITIAL_TRAIN_START_DATE)
    
    Dataset filename
    
    Number of trading days per episode (DAYS_PER_EPISODE)
    
    Total episodes (N_EPISODES)

🏗 Usage

Run the main script to start training and trading:
python main.py

This will initialize the reinforcement learning-based trading system, performing both training and trading phases dynamically.

📈 Methodology
    State Representation: Market indicators such as price movements, volatility, MACD, RSI, Bollinger Bands.
    
    Action Space: Buy (1), Sell (-1), Hold (0).
    
    Reward Function: Profit & loss adjustments with Sortino Ratio & Drawdown metrics.
    
    Trading Rules: Dynamic portfolio adjustments, risk mitigation, position tracking, and stop-loss handling.

🛠 Hyperparameters
| Parameter       | Value |
|---------------|------|
| Learning Rate | `1e-4` |
| Discount Factor (`GAMMA`) | `0.8` |
| Target Update (`TAU`) | `1e-3` |
| Experience Replay Size | `10,000` |
| Exploration Decay (`EPS_DECAY`) | `0.99` |

📝 Notes
    Ensure that the dataset is correctly formatted before execution.
    Fine-tune hyperparameters in main.py for improved trading performance.
    Use visualization tools within environment.py to analyze portfolio trends.

📜 License

This project is licensed under the MIT License, allowing open-source use, modification, and distribution.


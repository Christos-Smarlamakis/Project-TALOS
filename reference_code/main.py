from environment import TradingEnvironment
from ddqn_agent import DDQNAgent
from model import Dueling
from replay_memory import ReplayMemory, Transition
from data_processing import stock_reader

import time
import datetime
import numpy as np
from pandas.tseries.offsets import BDay
# Hyperparameters
EPS_START = 0.9
EPS_END = 0.05
EPS_DECAY = 0.99

LR_DQN = 1e-4
GAMMA = 0.8
TAU = 1e-3

STATE_SPACE = 37
ACTION_SPACE = 3
# Number of training-trading days per episode
DAYS_PER_EPISODE = 5
# Number episodes
N_EPISODES = 5

# Initial training start date
INITIAL_TRAIN_START_DATE = datetime.datetime.strptime('9/12/2017 09:30', '%m/%d/%Y %H:%M')

## Agent
agent = DDQNAgent(actor_net=Dueling, memory=ReplayMemory())

eps = EPS_START
act_dict = {0: -1, 1: 1, 2: 0}

te_score_min = -np.Inf

train_decisions = []
trade_decisions = []

start_time = time.time()

# Initialize total scores before episode loop
total_train_score = 0
total_trade_score = 0

for episode in range(1, N_EPISODES + 1):
    start_time1 = time.time()
    print(f"\n=== episode {episode} ===\n")

    # Reset start date at the beginning of the episode
    train_start_date = INITIAL_TRAIN_START_DATE

    # Create environments only once per episode
    reader = stock_reader(stock='dataset_CHK', # the name of file with the data
                          train_start=train_start_date.strftime('%m/%d/%Y %H:%M'),
                          train_days=DAYS_PER_EPISODE,
                          trade_days=DAYS_PER_EPISODE)
    reader.read_csv_file()

    train_env = TradingEnvironment(reader.train_days)
    trade_env = TradingEnvironment(reader.trade_days)

    total_train_score = 0
    total_trade_score = 0

    for day in range(DAYS_PER_EPISODE):
        print(f"Train Day: {train_start_date.strftime('%m/%d/%Y %H:%M')}")

        # === Training Phase ===
        # Train Phase - Extract only one day of data
        train_end_date = train_start_date.replace(hour=16, minute=0)
        train_data = reader.data.loc[train_start_date:train_end_date]
        train_env.update_data(train_data)
        # Get state based on the day
        _, state = train_env.get_state()
        # Daily score
        episode_score = 0
        steps_in_day = 0

        while True:
            actions = agent.act(state, eps)
            action = act_dict[actions]
            next_state, reward, done, _ = train_env.step(action)
            next_state = next_state.reshape(-1, STATE_SPACE)

            t = Transition(state, actions, reward, next_state, done)
            agent.memory.store(t)
            agent.learn()

            state = next_state
            episode_score += reward

            if done:
                break

        train_decisions.append(train_env.store)
        train_value = train_env.store['pnl'][-1]
        total_train_score += episode_score
        print(f"Train Score (Day): {episode_score:.5f}, Train Portfolio: ${train_value:.5f}")
        print(f"Train Score (Total): {total_train_score:.5f}")

        eps = max(EPS_END, EPS_DECAY * eps)

        # # === Trading Phase ===
        trade_date = (train_start_date + BDay(1))
        trade_end_date = trade_date.replace(hour=16, minute=0)
        trade_data = reader.data.loc[trade_date:trade_end_date]
        trade_env.update_data(trade_data)

        print(f"Trade Day: {trade_date.strftime('%m/%d/%Y %H:%M')}")

        # Get state based on the day
        _, state = trade_env.get_state()
        # Daily score
        trade_score = 0

        while True:
            actions = agent.act(state, eps)
            action = act_dict[actions]
            next_state, reward, done, _ = trade_env.step(action)
            next_state = next_state.reshape(-1, STATE_SPACE)
            state = next_state
            trade_score += reward

            if done:
                trade_env.diagram = True
                break

        trade_decisions.append(trade_env.store)
        trade_value = trade_env.store['pnl'][-1]
        total_trade_score += trade_score
        print(f"Trade Score (Day): {trade_score:.5f}, Trade Portfolio: ${trade_value:.5f}")
        print(f"Trade Score (Total): {total_trade_score:.5f}")

        # Update the date for the next train-trade
        train_start_date = (train_start_date + BDay(1))

    # === Reset environments ONLY at the end of the episode ===
    train_env.reset()
    trade_env.reset()

    end_time2 = time.time()
    minutes, seconds = divmod(end_time2 - start_time1, 60)
    print(f"Episode  {episode} Execution Time: {int(minutes)} minutes, {int(seconds)} seconds\n")

end_time = time.time()
execution_time = end_time - start_time
print(f"\n=== Total Execution Time: {execution_time:.2f} seconds ===")







import torch as t
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Trading Constants
COST = 3e-4
CAPITAL = 100_000
NEG_MUL = 1.2
ALPHA = 0.8
BETA = 0.3
GAMMA = 0.2
THRESHOLD = 5_000
DEVICE = t.device('cuda' if t.cuda.is_available() else 'cpu')
POSITION_LIMIT_COEF = 3
MAX_POSITIONS = 3
MAX_STEPS= 30

class Position:
    def __init__(self, entry_price, size):
        self.entry_price = entry_price
        self.size = size
        self.steps = 0

    def increment_steps(self):
        self.steps += 1


class TradingEnvironment:

    def __init__(self, asset_data, bank=CAPITAL, trans_coef=COST, position_limit=POSITION_LIMIT_COEF, threshold=THRESHOLD, store_flag=1, max_steps=MAX_STEPS):
        # Initializing trading parameters
        self.pnl = bank
        self.portfolio = bank
        self.long_positions = []
        self.short_positions = []
        self.closed_positions = []
        self.position_limit = position_limit
        self.trans_coef = trans_coef
        self.bank = bank
        self.max_steps = max_steps
        self.step_count = 0
        self.prev_act = 0
        self.returns = []
        self.prev_pnl = bank
        self.loss_threshold = threshold
        self.profit_threshold = threshold

        self.diagram = False

        ### data variables
        self.asset_data = asset_data
        self.terminal_idx = len(self.asset_data) - 1

        ### pointers, actions, rewards
        self.pointer = 0
        self.next_return, self.current_state = 0, None
        self.current_act = 0
        self.reward_offset = 0

        assert len(self.asset_data) > 0, "asset_data is empty!"
        assert not self.asset_data.isnull().values.any(), "Attention! There are NaNs in asset_data!"

        if self.pointer >= len(self.asset_data): raise IndexError(
            "The index is outside the bounds of the asset_data DataFrame")

        self.current_price = self.asset_data.iloc[self.pointer, :]['close']
        self.done = False

        self.store_flag = store_flag

        if self.store_flag == 1:
            self.store = {"action_store": [],
                          "close_price": [],
                          "trade": [],
                          "reward_store": [],
                          "pnl": [],
                          "position": [],
                          "portfolio": [],
                          "returns": [],
                          }

    def step(self, action):
        # Execute a trading step
        self.loss_threshold = max(self.portfolio * 0.1, THRESHOLD)
        self.profit_threshold = max(self.portfolio * 0.2, THRESHOLD)

        self.current_act = action
        assert self.pointer < len(self.asset_data), "Pointer out of bounds!"
        self.current_price = self.asset_data.iloc[self.pointer, :]['close']

        # Calculate the reward for the current action
        self.current_reward = self.calculate_reward()

        assert not np.isnan(self.current_reward), f"Reward is NaN on step {self.step_count}"

        # Update pointer, step count, and fetch the next state
        self.pointer += 1
        self.step_count += 1
        self.next_return, self.current_state = self.get_state()
        self.done = self.check_terminal()

        # Store the previous action for consistency
        self.prev_act = self.current_act

        # Terminate the episode if portfolio drops below a safety threshold
        if self.portfolio < 0.7 * self.bank:
            print(f"Portfolio dropped below 70% of initial capital: {self.portfolio}")
            self.done = True

        # Store data if the storage flag is enabled
        if not self.done and self.store_flag:
            self.store["action_store"].append(self.current_act)
            self.store["reward_store"].append(self.current_reward)
            self.store["close_price"].append(self.current_price)
            self.store["position"].append(len(self.long_positions) - len(self.short_positions))  # net position
            self.store["pnl"].append(self.pnl)
            self.store["portfolio"].append(self.portfolio)
            info = self.store
        else:
            info = None

        # Finalize all remaining positions if the episode is done
        if self.done:
            self.reward_offset = 0
            for position in self.long_positions[:]:
                self.finalize_trade(position)
            for position in self.short_positions[:]:
                self.finalize_trade(position)

            self.store["action_store"].append(self.current_act)
            self.store["reward_store"].append(self.current_reward)
            self.store["close_price"].append(self.current_price)
            self.long_positions = []
            self.short_positions = []
            self.store["position"].append(0)
            self.store["pnl"].append(self.pnl)
            self.store["portfolio"].append(self.portfolio)
            if self.diagram:

                fig, axs = plt.subplots(3, 1, figsize=(14, 18))

                for ax in axs:
                    ax.set_facecolor('#e5e5e5')

                    # Portfolio Value
                axs[0].plot(self.store['portfolio'], label='Portfolio Value', color='#6a4145',
                            linewidth=2)
                axs[0].axhline(y=self.bank, color='#171717', linestyle='--', linewidth=1,
                               label='Initial Capital')

                axs[0].set_title('Portfolio Wealth for F Stock', fontsize=14)
                axs[0].legend(fontsize=10)
                axs[0].grid(color='white', alpha=0.6)

                # Close Price  Buy/Sell Signals
                prices = self.store["close_price"]
                actions = self.store["action_store"]
                buy_signals = [price if action == 1 else np.nan for price, action in zip(prices, actions)]
                sell_signals = [price if action == -1 else np.nan for price, action in zip(prices, actions)]

                axs[1].plot(prices, label='Asset Price', color='#0055ff', linewidth=1.5)
                axs[1].scatter(range(len(buy_signals)), buy_signals, label='Buy', marker='^', color='#22c917',
                               s=80)
                axs[1].scatter(range(len(sell_signals)), sell_signals, label='Sell', marker='v', color='#c92217',
                               s=80)
                axs[1].set_title("Trade Signals", fontsize=14)
                axs[1].legend(fontsize=10)
                axs[1].grid(color='white', alpha=0.6)

                # Net Position
                axs[2].plot(self.store["position"], label='Positions', color='#c19193',
                            linewidth=1.5)
                axs[2].set_title("Positions Over Time", fontsize=14)
                axs[2].set_xlabel("Steps", fontsize=12)
                axs[2].grid(color='white', alpha=0.6)
                axs[2].legend(fontsize=10)

                plt.tight_layout()
                plt.show()

        return self.current_state, self.current_reward, self.done, info

    def update_data(self, new_data):
        """
        Updates the environment's data for the new day.
        """
        self.asset_data = new_data
        self.pointer = 0  # Reset the pointer to the beginning of the new data
        self.done = False
        self.terminal_idx = len(self.asset_data) - 1

    def reset(self):
        # Reset environment to initial state
        print("Reset function called!")
        self.pnl = self.bank
        self.portfolio = self.bank
        self.loss_threshold = THRESHOLD
        self.profit_threshold = THRESHOLD
        self.long_positions = []
        self.short_positions = []
        self.closed_positions = []
        self.reward = 0
        self.reward_offset = 0
        self.returns = []
        self.prev_pnl = self.bank

        self.pointer = 0
        self.next_return, self.current_state = self.get_state()
        self.current_act = 0

        if self.pointer >= len(self.asset_data): raise IndexError(
            "The index is outside the bounds of the asset_data DataFrame")

        self.current_price = self.asset_data.iloc[self.pointer, :]['close']
        self.done = False
        self.step_count = 0
        self.prev_act = 0

        if self.store_flag == 1:
            self.store = {"action_store": [],
                          "close_price": [],
                          "trade": [],
                          "reward_store": [],
                          "pnl": [],
                          "position": [],
                          "portfolio": [],
                          "returns": [],
                          }

        return self.current_state

    def open_position(self, entry_price, size):
        # Create and return a new Position object
        return Position(entry_price, size)

    def choose_position_to_close(self, positions, position_type):
        if not positions:
            return None

        for pos in positions:
            if pos.steps >= self.max_steps:
                return pos, position_type

        for pos in positions:
            profit_loss = self.calculate_reward_for_position(pos)
            if profit_loss < -self.loss_threshold or profit_loss > self.profit_threshold:
                return pos, position_type

        min_reward_position = min(positions, key=lambda x: self.calculate_reward_for_position(x))

        return min_reward_position, position_type

    def calculate_reward_for_position(self, position):
        # Calculate reward for a given position
        entry_price, size = position.entry_price, position.size
        current_value = size * self.current_price
        entry_value = size * entry_price
        trans_cost = abs(size) * entry_price * self.trans_coef
        reward = (current_value - entry_value) - trans_cost
        assert not np.isnan(reward), f"NaN reward in position: {position}"

        return reward

    def finalize_trade(self, position):
         # Finalize trade and update portfolio
        entry_price, size = position.entry_price, position.size
        profit_or_loss = size * (self.current_price - entry_price) - abs(size) * entry_price * self.trans_coef
        self.portfolio += profit_or_loss

        # Ensure position is removed from active lists
        if position in self.long_positions:
            self.long_positions.remove(position)
        elif position in self.short_positions:
            self.short_positions.remove(position)

        # Add position to closed positions for tracking
        self.closed_positions.append(position)

    def calculate_sortino_ratio(self):

        negative_returns = [r for r in self.returns if r < 0]

        if len(negative_returns) == 0:
            return 0

        if len(self.returns) > 1:
            returns = np.array(self.returns)
            downside_returns = returns[returns < 0]
            downside_deviation = np.std(downside_returns) if len(downside_returns) > 0 else 0
            mean_return = np.mean(returns)
            risk_free_rate = 0

            if downside_deviation != 0:
                sortino_ratio = (mean_return - risk_free_rate) / downside_deviation
            else:
                sortino_ratio = 0

            return sortino_ratio
        else:
            return 0

    def calculate_drawdown(self):
        if not self.store["portfolio"]:
            return 0

        max_portfolio_value = np.maximum.accumulate(self.store["portfolio"])
        current_portfolio_value = self.store["portfolio"][-1]

        drawdown = (max_portfolio_value[-1] - current_portfolio_value) / (max_portfolio_value[-1] + 1e-6)
        return drawdown

    def calculate_reward(self):
        risk_factor = 1.0 + (self.pnl / (abs(self.pnl) + 1e-8)) * 0.001
        self.order_size = max(1.0, self.portfolio * 0.0001 * risk_factor)
        investment = self.order_size * self.current_price
        trans_cost = investment * self.trans_coef
        total_cost = investment + trans_cost

        reward = 0
        reward_offset = 0
        trade = False
        total_positions = len(self.long_positions) + len(self.short_positions)

        for pos in self.long_positions + self.short_positions:
            if pos.steps >= self.max_steps:
                self.finalize_trade(pos)

        if total_positions >= self.position_limit:
            all_positions = self.long_positions + self.short_positions
            position_to_close, position_type = self.choose_position_to_close(all_positions, None)

            if position_to_close:
                self.finalize_trade(position_to_close)

        if len(self.long_positions) + len(self.short_positions) < self.position_limit:
            if self.current_act == 1:
                trade = True
                new_position = self.open_position(self.current_price, self.order_size)
                self.long_positions.append(new_position)
                self.portfolio -= total_cost
            elif self.current_act == -1:
                trade = True
                new_position = self.open_position(self.current_price, -self.order_size)
                self.short_positions.append(new_position)
                self.portfolio += investment - trans_cost
            else:
                if self.current_act == self.prev_act:
                    reward_offset += -0.1

        for position in self.long_positions + self.short_positions:
            position.increment_steps()

        self.store["trade"].append(trade)

        # Recalculate PnL including only active positions
        active_positions_pnl = sum(
            self.calculate_reward_for_position(pos) for pos in self.long_positions + self.short_positions)
        self.pnl = self.portfolio + active_positions_pnl

        if self.current_act != self.prev_act:
            reward = (self.pnl - self.prev_pnl) / max(abs(self.prev_pnl), 1e-8)

        if self.step_count > 0:
            current_return = (self.pnl - self.prev_pnl) / max(abs(self.prev_pnl), 1e-8)
            self.returns.append(current_return)

        self.next_return = np.clip(np.nan_to_num(self.next_return, nan=0.0), -1, 1)

        if reward == 0:
            reward = 100 * self.next_return * self.current_act

        reward += reward_offset
        if reward < 0:
            reward *= NEG_MUL

        sortino_ratio = np.nan_to_num(self.calculate_sortino_ratio(), nan=0.0)
        drawdown = np.nan_to_num(self.calculate_drawdown(), nan=0.0)
        combined_reward = ALPHA * reward + BETA * sortino_ratio - GAMMA * drawdown
        reward = max(-10, min(combined_reward, 10))

        self.prev_pnl = self.pnl

        return reward

    def check_terminal(self):
        return self.pointer == self.terminal_idx

    def get_state(self):
        state = []
        observation = ['r-1', 'r-2', 'r-5', 'r-10', 'r-20', 'r-40',
                       'v-1', 'v-2', 'v-5', 'v-10', 'v-20', 'v-40',
                           'sig-2', 'sig-5', 'sig-10', 'sig-20', 'sig-40',
                           'bollinger', 'low_bollinger', 'high_bollinger',
                           'rsi', 'macd_lmw', 'macd_smw', 'macd_bl', 'macd',
                           'macd_signal', 'macd_histogram', 'stc', 'stc_smoothed',
                           'TR', '%K', '%D', 'ATR']

        observation = [obs + '_norm' for obs in observation]

        long_positions_sign = sum([1 if pos.size > 0 else 0 for pos in self.long_positions])
        short_positions_sign = sum([1 if pos.size < 0 else 0 for pos in self.short_positions])

        port_state = [
            self.pnl / self.bank,
            self.portfolio / self.pnl,
            (long_positions_sign - short_positions_sign) * self.current_price / self.bank,
            self.prev_act
        ]

        for column in observation:
            value = self.asset_data.loc[self.asset_data.index[self.pointer], column]
            if isinstance(value, (float, int)) and pd.isna(value):
                print(f"Warning: NaN detected in {column}, replacing with 0.")
                value = 0
            if isinstance(value, pd.Series):
                value = value.iloc[0]
            state.append(value)

        state.extend(port_state)

        try:
            nan_values = [(i, x) for i, x in enumerate(state) if isinstance(x, (float, int)) and np.isnan(x)]

            for index, value in nan_values:
                print(f"NaN value at index {index}: {value}")

            state = np.array([0 if isinstance(x, (float, int)) and np.isnan(x) else x for x in state])

        except Exception as e:
            print("Error converting to np.array:", e)
            raise

        assert all(not np.isnan(x) for x in state), f"NaN detected in state: {state}"

        next_ret = self.asset_data['next_state_return'].iloc[self.pointer]

        return next_ret, state

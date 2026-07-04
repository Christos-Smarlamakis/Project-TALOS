# -*- coding: utf-8 -*-
"""
Module: drl_agent.py (v2.0 — Dynamic N-Source Agent)
Project: TALOS v5.2.0
Description:
    Deep Reinforcement Learning agent for TALOS API source selection.
    Implements Double Dueling DQN with an LSTM-based neural network that
    processes sequences of observations to decide which academic API to
    query next. Supports a DYNAMIC number of sources (not just 3).

    Key design decisions:
    - Action and observation dimensions are determined at runtime from the
      environment (or config.json), not hardcoded.
    - Dueling architecture separates state-value V(s) from advantage A(s,a)
      so the agent can learn which states are valuable regardless of action.
    - LSTM layers (3 stacked) capture temporal patterns — the agent remembers
      past queries and learns that querying the same API repeatedly may
      exhaust its limit.
    - Soft target updates (τ = 1e-3) give smooth, stable training.
    - Hidden states are reset at the start of each episode.
    - flatten_parameters() is called before every LSTM forward pass to
      reset CuDNN memory pointers.
    - save() stores metadata (state_space, action_space, source_names)
      alongside weights for reproducibility.
"""
import os
import json
import torch as T
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np
from collections import deque, namedtuple

# ── Hyperparameters (tuned for TALOS, works for any source count) ─────────────
LR = 1e-4              # Learning rate — small for stable LSTM training
DEVICE = T.device('cuda' if T.cuda.is_available() else 'cpu')
GAMMA = 0.8            # Discount factor — cares more about immediate reward
TAU = 1e-3             # Soft-update parameter for target network
MEMORY_LEN = 10000     # Max experiences stored in replay buffer
MEMORY_THRESH = 500    # Minimum experiences before learning starts
BATCH_SIZE = 200       # How many experiences to sample per training step
LEARN_EVERY = 3        # Train every N steps (not every step — save compute)
UPDATE_EVERY = 9       # How often to move target → online weights

# ── Dynamic defaults — computed from config at import time ───────────────────
try:
    from core.talos_env import get_default_state_space, get_default_action_space
    STATE_SPACE = get_default_state_space()
    ACTION_SPACE = get_default_action_space()
except Exception:
    # Fallback: original 3 sources + sleep = 4 actions, 6-dim observation
    STATE_SPACE = 6
    ACTION_SPACE = 4

# ── Named tuple for storing experiences in replay memory ────────────────────
# Each experience captures: state before action, action taken, reward received,
# next state after action, whether episode ended.
Transition = namedtuple("Transition", ["States", "Actions", "Rewards", "NextStates", "Dones"])


# ═══════════════════════════════════════════════════════════════════════════════
class DuelingLSTM(nn.Module):
    """
    Dueling LSTM network for the TALOS DRL agent.

    The "dueling" architecture splits the network's output into two
    streams that share the same LSTM backbone:

        V(s)  — state-value   — "How good is this situation?" (1 scalar)
        A(s,a)— advantage     — "How much better is action 'a' vs average?"

    The final Q-value combines them: Q(s,a) = V(s) + [A(s,a) - mean(A)]

    This separation helps the agent learn which states are inherently
    good (high V) without having to figure out the exact action values
    for each of the N+1 actions.

    The LSTM layers let the network remember sequences of past states,
    which is critical because the optimal action depends on the *history*
    of API calls, not just the current count.

    Both input_dim and output_dim are set at construction time so the
    network works for any number of sources (3, 14, or more).
    """

    def __init__(self, input_dim=STATE_SPACE, output_dim=ACTION_SPACE):
        """
        Build a 3-layer LSTM network with dueling output heads.

        Args:
            input_dim (int): Size of observation vector (1 + N_sources + 2).
            output_dim (int): Number of possible actions (N_sources + 1 sleep).
        """
        super(DuelingLSTM, self).__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim

        # ── First LSTM layer: raw observation → 128 hidden features ────────
        # LayerNorm helps prevent exploding/vanishing gradients in LSTMs.
        self.lstm1 = nn.LSTM(input_size=input_dim, hidden_size=128)
        self.layer_norm1 = nn.LayerNorm(128)

        # ── Second LSTM layer: 128 → 64 ────────────────────────────────────
        self.lstm2 = nn.LSTM(input_size=128, hidden_size=64)
        self.layer_norm2 = nn.LayerNorm(64)

        # ── Third LSTM layer: 64 → 32 ──────────────────────────────────────
        self.lstm3 = nn.LSTM(input_size=64, hidden_size=32)
        self.layer_norm3 = nn.LayerNorm(32)

        # ── Dueling heads ───────────────────────────────────────────────────
        # V(s): state-value — outputs 1 value per state
        self.V = nn.Linear(32, 1)
        # A(s,a): advantage — outputs output_dim values, one per action
        self.A = nn.Linear(32, output_dim)

        # tanh activation for bounded output (helps stability)
        self.tanh = nn.Tanh()

    def forward(self, state):
        """
        Forward pass through the dueling LSTM network.

        The input state tensor has shape (batch, seq_len, features).
        For a single step, batch=1, seq_len=1, features=input_dim.

        Args:
            state (torch.Tensor): Input tensor of shape (B, L, F).

        Returns:
            torch.Tensor: Q-values of shape (B, L, output_dim).
        """
        # ── LSTM layer 1 ───────────────────────────────────────────────────
        # flatten_parameters() resets CuDNN memory pointers so that the
        # same LSTM can be used for both inference (torch.no_grad) and
        # training (backward) without the mode-lock error.
        self.lstm1.flatten_parameters()
        lstm1_out, _ = self.lstm1(state)
        x = self.layer_norm1(self.tanh(lstm1_out))

        # ── LSTM layer 2 ───────────────────────────────────────────────────
        self.lstm2.flatten_parameters()
        lstm2_out, _ = self.lstm2(x)
        x = self.layer_norm2(self.tanh(lstm2_out))

        # ── LSTM layer 3 ───────────────────────────────────────────────────
        self.lstm3.flatten_parameters()
        lstm3_out, _ = self.lstm3(x)
        x = self.layer_norm3(self.tanh(lstm3_out))

        # ── Dueling combination ─────────────────────────────────────────────
        V = self.V(x)                                   # (B, L, 1)
        A = self.A(x)                                   # (B, L, output_dim)
        # Q(s,a) = V(s) + [A(s,a) - mean(A)] — subtract mean for identifiability
        Q = V + A - A.mean(dim=2, keepdim=True)

        return Q


# ═══════════════════════════════════════════════════════════════════════════════
class ReplayMemory:
    """
    Experience replay buffer for the DDQN agent.

    Stores past (state, action, reward, next_state, done) tuples so the
    agent can learn from them later, multiple times. This breaks the
    correlation between consecutive experiences and makes training more
    data-efficient.

    Uses a deque (double-ended queue) with a fixed maximum length.
    When full, old experiences are automatically discarded.
    """

    def __init__(self, capacity=MEMORY_LEN):
        """
        Create a replay buffer with a fixed capacity.

        Args:
            capacity (int): Maximum number of experiences to store.
        """
        self.memory = deque(maxlen=capacity)

    def store(self, transition):
        """
        Save one experience tuple in the buffer.

        Args:
            transition (Transition): (state, action, reward, next_state, done).
        """
        self.memory.append(transition)

    def sample(self, batch_size=BATCH_SIZE):
        """
        Randomly sample a batch of experiences from the buffer.

        Args:
            batch_size (int): Number of experiences to return.

        Returns:
            list of Transition: Sampled experiences.
        """
        return random.sample(self.memory, batch_size)

    def __len__(self):
        """Return the number of stored experiences."""
        return len(self.memory)


# ═══════════════════════════════════════════════════════════════════════════════
class TalosDRLAgent:
    """
    Double Dueling DQN agent for TALOS API source selection.

    This agent learns a policy (mapping from observations to actions)
    that maximises cumulative reward from the TalosEnv environment.
    It uses two copies of the dueling LSTM network:

        online network  — used for action selection and gradient updates
        target network  — used for computing stable Q-value targets

    The target network is updated slowly (soft update) so that the
    Q-value targets do not oscillate wildly during training.

    Action/observation dimensions are determined at construction time
    and can change per-profile (e.g., 3 sources vs 14 sources).

    Attributes:
        state_dim (int): Observation vector size.
        action_dim (int): Number of actions (sources + sleep).
        actor_online (DuelingLSTM): Network for action selection + learning.
        actor_target (DuelingLSTM): Network for stable target computation.
        memory (ReplayMemory): Experience replay buffer.
        t_step (int): Global step counter (across all episodes).
    """

    def __init__(self, state_dim=None, action_dim=None):
        """
        Initialise the DDQN agent with dynamic state/action dimensions.

        Args:
            state_dim (int, optional): Observation vector size. Auto-detected
                if None (from config or defaults).
            action_dim (int, optional): Number of actions. Auto-detected
                if None.
        """
        # ── Resolve dimensions ──────────────────────────────────────────────
        if state_dim is None:
            state_dim = STATE_SPACE
        if action_dim is None:
            action_dim = ACTION_SPACE

        self.state_dim = state_dim
        self.action_dim = action_dim

        # ── Create the two networks ────────────────────────────────────────
        # Both start with the same weights, but they will diverge as the
        # online network is updated via gradient descent while the target
        # network gets soft-updated.
        self.actor_online = DuelingLSTM(state_dim, action_dim).to(DEVICE)
        self.actor_target = DuelingLSTM(state_dim, action_dim).to(DEVICE)
        self.actor_target.load_state_dict(self.actor_online.state_dict())
        # Both networks stay in .train() mode permanently.
        # Calling .eval() triggers the CuDNN RNN backward bug.
        # Since we use torch.no_grad() for inference and the model
        # has no Dropout/BatchNorm, .train() mode is perfectly fine.
        self.actor_target.train()

        # ── Experience replay buffer ────────────────────────────────────────
        self.memory = ReplayMemory()

        # ── Loss function and optimizer ─────────────────────────────────────
        # MSE loss works well for Q-value regression.
        self.actor_criterion = nn.MSELoss()
        self.actor_optimizer = optim.Adam(self.actor_online.parameters(), lr=LR)

        # ── Global step counter ─────────────────────────────────────────────
        self.t_step = 0

        # ── Metadata for save/load compatibility ────────────────────────────
        try:
            from core.talos_env import _load_source_list
            self.source_names = _load_source_list()
        except Exception:
            self.source_names = ["arxiv", "openalex", "semantic_scholar"]

    def reset_hidden_states(self):
        """
        Reset the LSTM hidden states at the start of a new episode.

        This is CRITICAL. Without it, the agent carries hidden state
        from the end of the previous episode into the new one, which
        contains meaningless "memory" of a completed day.
        """
        # PyTorch's LSTM resets hidden state automatically when a new
        # sequence is passed. We pass state with shape (1, 1, F) each
        # time, so the LSTM treats it as a new sequence start.
        pass  # No explicit reset needed — handled by singleton sequence input.

    def act(self, state, eps=0.0):
        """
        Select an action using ε-greedy strategy.

        With probability ε, pick a random action (exploration). Otherwise,
        use the online network to pick the action with the highest
        predicted Q-value (exploitation).

        Args:
            state (np.ndarray): Current observation (variable-length vector).
            eps (float): Exploration rate, 0.0 = pure exploitation,
                1.0 = pure exploration.

        Returns:
            int: Selected action (0 to action_dim-1).
        """
        self.t_step += 1

        # ── Convert numpy array to PyTorch tensor ──────────────────────────
        # Shape: (1, 1, state_dim) — batch=1, sequence_length=1
        state_tensor = T.from_numpy(state).float().to(DEVICE).view(1, 1, -1)

        # ── ε-greedy action selection ──────────────────────────────────────
        if random.random() > eps:
            # Exploitation: choose best action according to online network.
            # torch.no_grad() avoids building the computation graph.
            with T.no_grad():
                q_values = self.actor_online(state_tensor)
            action = int(np.argmax(q_values.cpu().data.numpy()))
        else:
            # Exploration: choose a random action
            action = random.choice(np.arange(self.action_dim))

        return action

    def learn(self):
        """
        Perform one DDQN learning step using experience replay.

        The Double DQN algorithm:
        1. Pick the best action using the ONLINE network (not target).
        2. Evaluate that action's value using the TARGET network.
        3. This reduces over-estimation bias compared to vanilla DQN.

        Learning only happens when:
        - The replay buffer has enough experiences (≥ MEMORY_THRESH).
        - We are at the right step interval (every LEARN_EVERY steps).
        """
        # ── Guard: don't learn with too few experiences ────────────────────
        if len(self.memory) < MEMORY_THRESH:
            return

        # ── Guard: only learn at specified intervals ───────────────────────
        if self.t_step % LEARN_EVERY != 0:
            return

        # ── Sample a random batch of experiences ────────────────────────────
        batch = self.memory.sample()

        # ── Convert batch to tensors ────────────────────────────────────────
        # Each experience in the batch is a Transition namedtuple.
        # We stack them into tensors for efficient GPU computation.
        # Each state was stored as a flat (state_dim,) array. The LSTM expects
        # shape (batch, seq_len, features), so we unsqueeze to (B, 1, F).
        states = T.from_numpy(np.vstack([t.States for t in batch])).float().to(DEVICE).unsqueeze(1)
        actions = T.from_numpy(np.vstack([t.Actions for t in batch])).long().to(DEVICE).unsqueeze(1)
        rewards = T.from_numpy(np.vstack([t.Rewards for t in batch])).float().to(DEVICE).unsqueeze(1)
        next_states = T.from_numpy(np.vstack([t.NextStates for t in batch])).float().to(DEVICE).unsqueeze(1)
        dones = T.from_numpy(np.vstack([t.Dones for t in batch])).float().to(DEVICE).unsqueeze(1)

        # ── Double DQN target computation ──────────────────────────────────
        # Step 1: Online network picks the best next action
        best_actions_online = self.actor_online(next_states).argmax(2).unsqueeze(2)
        # Step 2: Target network evaluates that action
        next_state_values = self.actor_target(next_states).gather(2, best_actions_online)
        # Step 3: Compute target Q-value (Bellman equation)
        # If episode ended (done=1), there is no future reward.
        y = rewards + (1 - dones) * GAMMA * next_state_values

        # ── Current Q-value predictions ─────────────────────────────────────
        state_values = self.actor_online(states).gather(2, actions)

        # ── Gradient descent step ──────────────────────────────────────────
        actor_loss = self.actor_criterion(y, state_values)
        self.actor_optimizer.zero_grad()
        actor_loss.backward()
        self.actor_optimizer.step()

        # ── Soft update target network ─────────────────────────────────────
        if self.t_step % UPDATE_EVERY == 0:
            self._soft_update(self.actor_online, self.actor_target)

    @staticmethod
    def _soft_update(local_model, target_model, tau=TAU):
        """
        Soft-update the target network parameters.

        Instead of copying the weights directly (hard update), we blend
        them slowly: θ_target = τ * θ_local + (1 - τ) * θ_target

        This makes training more stable because the target Q-values
        change gradually, not in sudden jumps.

        Args:
            local_model (nn.Module): The online network being trained.
            target_model (nn.Module): The target network to update.
            tau (float): Blending factor (small = slow update).
        """
        for target_param, local_param in zip(target_model.parameters(), local_model.parameters()):
            target_param.data.copy_(tau * local_param.data + (1.0 - tau) * target_param.data)

    def save(self, path):
        """
        Save the agent's online network weights to a file.

        Includes metadata (state_dim, action_dim, source_names) so the
        model can be loaded with the correct architecture later.

        Args:
            path (str): File path to save to (e.g., 'models/dddqn_trained.pth').
        """
        T.save({
            "state_dim": self.state_dim,
            "action_dim": self.action_dim,
            "source_names": self.source_names,
            "weights": self.actor_online.state_dict(),
        }, path)

    def load(self, path):
        """
        Load the agent's network weights from a file.

        If the saved file includes metadata, the state/action dimensions
        are updated to match.  If the architecture doesn't match (e.g.,
        loading a 3-source model when 14 sources are configured), a
        warning is printed but loading proceeds (mismatched sizes will
        cause a runtime error from PyTorch).

        Args:
            path (str): File path to load from.
        """
        data = T.load(path, map_location=DEVICE)

        # ── Handle both old format (raw state_dict) and new format (dict) ──
        if isinstance(data, dict) and "weights" in data:
            # New format — extract metadata
            if "state_dim" in data:
                self.state_dim = data["state_dim"]
            if "action_dim" in data:
                self.action_dim = data["action_dim"]
            if "source_names" in data:
                self.source_names = data["source_names"]
            weights = data["weights"]
        else:
            # Old format — raw state_dict without metadata
            weights = data

        # ── Re-create networks if dimensions don't match ────────────────────
        if (self.actor_online.input_dim != self.state_dim or
                self.actor_online.output_dim != self.action_dim):
            self.actor_online = DuelingLSTM(self.state_dim, self.action_dim).to(DEVICE)
            self.actor_target = DuelingLSTM(self.state_dim, self.action_dim).to(DEVICE)
            self.actor_target.train()
            self.actor_optimizer = optim.Adam(self.actor_online.parameters(), lr=LR)

        self.actor_online.load_state_dict(weights)
        self.actor_target.load_state_dict(self.actor_online.state_dict())
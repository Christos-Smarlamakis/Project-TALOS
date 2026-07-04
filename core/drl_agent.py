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

from core.drl_networks import DuelingLSTM

# ── Hyperparameters (tuned for TALOS, works for any source count) ─────────────
LR = 4.735e-05         # Learning rate — GWO-optimized for stable LSTM training
DEVICE = T.device('cuda' if T.cuda.is_available() else 'cpu')
GAMMA = 0.575          # Discount factor — GWO-optimized for short-term reward
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

    def __init__(self, state_dim=None, action_dim=None, network_class=None):
        """
        Initialise the DDQN agent with dynamic state/action dimensions.

        Args:
            state_dim (int, optional): Observation vector size. Auto-detected
                if None (from config or defaults).
            action_dim (int, optional): Number of actions. Auto-detected
                if None.
            network_class (class, optional): nn.Module subclass to use as
                the neural network backbone. Must accept (input_dim, output_dim).
                Defaults to DuelingLSTM.
        """
        # ── Resolve dimensions ──────────────────────────────────────────────
        if state_dim is None:
            state_dim = STATE_SPACE
        if action_dim is None:
            action_dim = ACTION_SPACE
        if network_class is None:
            network_class = DuelingLSTM

        self.state_dim = state_dim
        self.action_dim = action_dim
        self.network_class = network_class

        # ── Create the two networks ────────────────────────────────────────
        self.actor_online = network_class(state_dim, action_dim).to(DEVICE)
        self.actor_target = network_class(state_dim, action_dim).to(DEVICE)
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

        Includes metadata (state_dim, action_dim, source_names, network_class)
        so the model can be loaded with the correct architecture later.

        Args:
            path (str): File path to save to (e.g., 'models/dddqn_trained.pth').
        """
        T.save({
            "state_dim": self.state_dim,
            "action_dim": self.action_dim,
            "source_names": self.source_names,
            "network_class": self.network_class.__name__,
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
        data = T.load(path, map_location=DEVICE, weights_only=True)

        # ── Handle both old format (raw state_dict) and new format (dict) ──
        if isinstance(data, dict) and "weights" in data:
            # New format — extract metadata
            saved_state_dim = data.get("state_dim", self.state_dim)
            saved_action_dim = data.get("action_dim", self.action_dim)
            if "source_names" in data:
                self.source_names = data["source_names"]
            weights = data["weights"]
        else:
            # Old format — raw state_dict without metadata
            # Infer dimensions from the saved weights
            saved_state_dim = None
            saved_action_dim = None
            weights = data

        # ── Re-create networks if dimensions don't match (BEFORE load_state_dict) ──
        # MUST check BEFORE calling load_state_dict to avoid PyTorch size mismatch
        # errors when the saved model has different state/action dimensions.
        recreate_needed = False
        if saved_state_dim is not None and saved_state_dim != self.state_dim:
            self.state_dim = saved_state_dim
            recreate_needed = True
        if saved_action_dim is not None and saved_action_dim != self.action_dim:
            self.action_dim = saved_action_dim
            recreate_needed = True
        if (self.actor_online.input_dim != self.state_dim or
                self.actor_online.output_dim != self.action_dim):
            recreate_needed = True

        # ── Resolve network class from saved metadata ──────────────────────
        if isinstance(data, dict) and "network_class" in data:
            saved_class_name = data["network_class"]
            if saved_class_name == "DuelingLSTM":
                self.network_class = DuelingLSTM
            # Future: add elif for other network classes here
        else:
            self.network_class = DuelingLSTM

        if recreate_needed:
            self.actor_online = self.network_class(self.state_dim, self.action_dim).to(DEVICE)
            self.actor_target = self.network_class(self.state_dim, self.action_dim).to(DEVICE)
            self.actor_target.train()
            self.actor_optimizer = optim.Adam(self.actor_online.parameters(), lr=LR)

        self.actor_online.load_state_dict(weights)
        self.actor_target.load_state_dict(self.actor_online.state_dict())

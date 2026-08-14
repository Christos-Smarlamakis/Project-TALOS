# -*- coding: utf-8 -*-
"""
Module: drl_networks.py (v1.0)
Project: TALOS v5.9.15
Description:
    Neural network architectures for the TALOS Deep Reinforcement Learning
    agent. This module is designed to be PLUGGABLE — any network with the
    signature `__init__(input_dim, output_dim)` and `forward(state) -> Q`
    can be dropped in. The agent selects which network to use via the
    `network_class` parameter in TalosDRLAgent.

    Currently implemented:
    - DuelingLSTM: 3-layer LSTM with dueling heads (V + A). Default.

    Future candidates:
    - DuelingTransformer: Multi-head attention + positional encoding
    - DuelingxLSTM: Extended LSTM (Beck et al., 2024)

    Key design decision:
    - The dueling architecture (separate V and A streams) is BUILT INTO
      each network class, not applied as a wrapper. This gives each
      architecture full control over how value and advantage are computed.
    - All networks accept (input_dim, output_dim) at construction so the
      agent can vary dimensions dynamically (3 sources vs 14 sources).
"""
import torch as T
import torch.nn as nn


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

    def __init__(self, input_dim, output_dim):
        """
        Build a 3-layer LSTM network with dueling output heads.

        Args:
            input_dim (int): Size of observation vector (1 + N_sources + 2 + 4).
            output_dim (int): Number of possible actions (N_sources + 1 sleep).
        """
        super(DuelingLSTM, self).__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim

        # ── First LSTM layer: raw observation → 128 hidden features ────────
        self.lstm1 = nn.LSTM(input_size=input_dim, hidden_size=128)
        self.layer_norm1 = nn.LayerNorm(128)

        # ── Second LSTM layer: 128 → 64 ────────────────────────────────────
        self.lstm2 = nn.LSTM(input_size=128, hidden_size=64)
        self.layer_norm2 = nn.LayerNorm(64)

        # ── Third LSTM layer: 64 → 32 ──────────────────────────────────────
        self.lstm3 = nn.LSTM(input_size=64, hidden_size=32)
        self.layer_norm3 = nn.LayerNorm(32)

        # ── Dueling heads ───────────────────────────────────────────────────
        self.V = nn.Linear(32, 1)           # state-value
        self.A = nn.Linear(32, output_dim)  # advantage

        self.tanh = nn.Tanh()

    def forward(self, state):
        """
        Forward pass through the dueling LSTM network.

        Args:
            state (torch.Tensor): Input tensor of shape (B, L, F).

        Returns:
            torch.Tensor: Q-values of shape (B, L, output_dim).
        """
        # ── LSTM layer 1 ───────────────────────────────────────────────────
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
        Q = V + A - A.mean(dim=2, keepdim=True)

        return Q
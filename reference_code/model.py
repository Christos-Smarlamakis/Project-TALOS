import torch.nn as nn

STATE_SPACE = 37
ACTION_SPACE = 3

class Dueling(nn.Module):
    """Dueling architecture with LSTM layers."""

    def __init__(self, input_dim=STATE_SPACE, output_dim=ACTION_SPACE):
        super(Dueling, self).__init__()
        self.input_dim = input_dim
        self.output_dim = output_dim

        # First LSTM layer with Layer Normalization
        self.lstm1 = nn.LSTM(input_size=input_dim, hidden_size=128)
        self.layer_norm1 = nn.LayerNorm(128)

        # Second LSTM layer with Layer Normalization
        self.lstm2 = nn.LSTM(input_size=128, hidden_size=64)
        self.layer_norm2 = nn.LayerNorm(64)

        # Third LSTM layer with Layer Normalization
        self.lstm3 = nn.LSTM(input_size=64, hidden_size=32)
        self.layer_norm3 = nn.LayerNorm(32)

        # Fully connected layers for state-value (V) and advantage (A) streams
        self.V = nn.Linear(32, 1) # State-value function
        self.A = nn.Linear(32, self.output_dim) # Advantage function

        self.tanh = nn.Tanh()

    def forward(self, state):
        """Forward pass through the network."""

        # Pass state through the first LSTM layer
        lstm1_output, _ = self.lstm1(state)
        x = self.layer_norm1(self.tanh(lstm1_output))

        # Pass through the second LSTM layer
        lstm2_output, _ = self.lstm2(x)
        x = self.layer_norm2(self.tanh(lstm2_output))

        # Pass through the third LSTM layer
        lstm3_output, _ = self.lstm3(x)
        x = self.layer_norm3(self.tanh(lstm3_output))

        # Compute state-value (V) and advantage (A)
        V = self.V(x)
        A = self.A(x)

        # Combine state-value and advantage using the dueling architecture
        x = V + A - A.mean(dim=1, keepdim=True)

        return x
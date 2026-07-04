import torch as T
import torch.nn as nn
import torch.optim as optim
import random
import numpy as np

# Hyperparameters
LR_DQN = 1e-4
DEVICE = T.device('cuda' if T.cuda.is_available() else 'cpu')
LEARN_AFTER = 500 # Minimum memory size before learning starts
LEARN_EVERY = 3 # Learning frequency
UPDATE_EVERY = 9 # Target network update frequency
STATE_SPACE = 37
ACTION_SPACE = 3
GAMMA = 0.8 # Discount factor
TAU = 1e-3 # Soft update parameter

class DDQNAgent():
    def __init__(self, actor_net, memory):
        self.actor_online = actor_net(STATE_SPACE, ACTION_SPACE).to(DEVICE)
        self.actor_target = actor_net(STATE_SPACE, ACTION_SPACE).to(DEVICE)
        self.actor_target.load_state_dict(self.actor_online.state_dict())
        self.actor_target.eval()

        # Replay memory for experience replay
        self.memory = memory

        # Loss function and optimizer
        self.actor_criterion = nn.MSELoss()
        self.actor_op = optim.Adam(self.actor_online.parameters(), lr=LR_DQN)

        self.t_step = 0

    def act(self, state, eps=0.):
        """Select an action using epsilon-greedy strategy."""
        self.t_step += 1

        state = T.from_numpy(state).float().to(DEVICE).view(1, 1, -1)

        self.actor_online.eval()
        with T.no_grad():
            actions = self.actor_online(state) # Forward pass
        self.actor_online.train()

        # Epsilon-greedy action selection
        if random.random() > eps:
            act = np.argmax(actions.cpu().data.numpy())
        else:
            act = random.choice(np.arange(ACTION_SPACE))
        return int(act)

    def learn(self):
        if len(self.memory) <= LEARN_AFTER:
            return 0

        # Sample experiences from memory at defined intervals
        if self.t_step > LEARN_AFTER and self.t_step % LEARN_EVERY == 0:

            batch = self.memory.sample()

            # Convert batch to tensors
            states = T.from_numpy(np.vstack([t.States for t in batch])).float().to(DEVICE)
            actions = T.from_numpy(np.vstack([t.Actions for t in batch])).long().to(DEVICE)
            rewards = T.from_numpy(np.vstack([t.Rewards for t in batch])).float().to(DEVICE)
            next_states = T.from_numpy(np.vstack([t.NextStates for t in batch])).float().to(DEVICE)
            dones = T.from_numpy(np.vstack([t.Dones for t in batch])).float().to(DEVICE)

            # Compute target Q-values using Double DQN approach
            best_actions_online = self.actor_online(next_states).argmax(1).unsqueeze(1)
            next_state_values = self.actor_target(next_states).gather(1, best_actions_online)
            y = rewards + (1 - dones) * GAMMA * next_state_values
            state_values = self.actor_online(states).gather(1, actions.long())

            # Compute loss and optimize network
            actor_loss = self.actor_criterion(y, state_values)
            self.actor_op.zero_grad()
            actor_loss.backward()
            self.actor_op.step()

            # Update target network periodically
            if self.t_step % UPDATE_EVERY == 0:
                self.soft_update(self.actor_online, self.actor_target)

    def soft_update(self, local_model, target_model, tau=TAU):
        """Soft update target network parameters."""
        for target_param, local_param in zip(target_model.parameters(), local_model.parameters()):
            target_param.data.copy_(tau * local_param.data + (1.0 - tau) * target_param.data)

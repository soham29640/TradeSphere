import torch.nn as nn


class LSTMModel(nn.Module):
    """
    2-layer LSTM with dropout for volatility-aware price prediction.
    input_size matches the number of features fed by the scaler (default=1 for Close-only).
    """

    def __init__(
        self,
        input_size: int = 1,
        hidden_size: int = 64,
        num_layers: int = 2,
        output_size: int = 1,
        dropout: float = 0.2,
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers  = num_layers

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=dropout if num_layers > 1 else 0.0,
        )
        self.dropout = nn.Dropout(dropout)
        self.fc      = nn.Linear(hidden_size, output_size)

    def forward(self, x):
        lstm_out, _ = self.lstm(x)          # (batch, seq, hidden)
        last_out    = lstm_out[:, -1, :]    # take last time-step
        return self.fc(self.dropout(last_out))
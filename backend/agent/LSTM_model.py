import torch
import torch.nn as nn


class LSTMModel(nn.Module):
    """
    Two-layer LSTM followed by a linear output layer.

    Fixes:
    - dropout=0.0 is now explicitly set when num_layers == 1; PyTorch raises a
      UserWarning (and in strict mode an error) if dropout > 0 is passed to a
      single-layer LSTM because there is no inter-layer dropout to apply.
    - Added a `predict` convenience method that handles tensor creation and
      .eval() mode so callers don't have to repeat boilerplate.
    """

    def __init__(
        self,
        input_size: int = 9,
        hidden_size: int = 64,
        num_layers: int = 2,
        output_size: int = 1,
        dropout: float = 0.2,
    ):
        super().__init__()

        lstm_dropout = dropout if num_layers > 1 else 0.0

        self.lstm = nn.LSTM(
            input_size=input_size,
            hidden_size=hidden_size,
            num_layers=num_layers,
            batch_first=True,
            dropout=lstm_dropout,
        )
        self.fc = nn.Linear(hidden_size, output_size)

    # ------------------------------------------------------------------
    def forward(self, x: torch.Tensor) -> torch.Tensor:
        lstm_out, _ = self.lstm(x)          # (batch, seq, hidden)
        return self.fc(lstm_out[:, -1, :])  # use last time-step

    # ------------------------------------------------------------------
    def predict(self, x: torch.Tensor) -> float:
        """Run a single forward pass in eval mode and return a scalar."""
        self.eval()
        with torch.no_grad():
            return self.forward(x).item()
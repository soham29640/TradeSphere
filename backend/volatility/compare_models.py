import pandas as pd
import matplotlib.pyplot as plt

df = pd.read_csv("outputs/predictions/evaluation_metrics.csv")

plt.figure(figsize=(8, 5))
plt.bar(df["Model"], df["RMSE"], color=['skyblue', 'lightgreen', 'salmon'])
plt.title("RMSE Comparison Between Models")
plt.ylabel("RMSE")
plt.grid(axis='y')
plt.tight_layout()
plt.savefig("outputs/plots/evaluation.png")
plt.show()

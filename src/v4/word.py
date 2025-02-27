import matplotlib.pyplot as plt
import numpy as np

# Define criteria labels
criteria = [
    "Sensory Feedback", "Responsiveness", "Multitouch Capability", "Expressive Potential",
    "Flexibility of Mapping", "Timbral Options", "Cognitive Load", "Aesthetic Appeal",
    "Portability", "Durability", "Repair & Reusability", "Cost Effectiveness", "Ergonomics"
]

# Example scores for a given instrument version (scale of 1-4)
scores = [3, 4, 3, 3, 4, 3, 3, 4, 4, 3, 3, 3, 4]

# Convert to a circular format
angles = np.linspace(0, 2 * np.pi, len(criteria), endpoint=False).tolist()

# Close the circle by repeating the first value
scores += scores[:1]
angles += angles[:1]

# Create the radar chart
fig, ax = plt.subplots(figsize=(8, 8), subplot_kw=dict(polar=True))
ax.fill(angles, scores, color='blue', alpha=0.3)
ax.plot(angles, scores, color='blue', linewidth=2, linestyle='solid')

# Add labels
ax.set_xticks(angles[:-1])
ax.set_xticklabels(criteria, fontsize=10)
ax.set_yticklabels(["1", "2", "3", "4"], fontsize=9)

# Title
ax.set_title("Instrument Design Evaluation - Radar Chart",
             fontsize=14, fontweight='bold')

# Show the radar chart
plt.show()

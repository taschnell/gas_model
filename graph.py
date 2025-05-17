import matplotlib.pyplot as plt
import time

# Constants
BOLTZMANN_CONSTANT = 1.380649e-23  # J/K
mass = 4.65e-26 # kg (mass of Nitrogen)


def read_speeds_from_file(filename):
    with open(filename, "r") as file:
        return [float(line.strip()) for line in file if line.strip()]

def live_plot_histogram(filename, interval=1, mass=mass):
    plt.ion()  # Turn on interactive mode
    fig, ax = plt.subplots(figsize=(10, 6))

    while True:
        ax.clear()
        speeds = read_speeds_from_file(filename)

        if not speeds:
            ax.set_title("No data available")
        else:
            average_speed = sum(speeds) / len(speeds)
            average_ke = sum(0.5 * mass * v**2 for v in speeds) / len(speeds)

            # Convert KE to temperature
            temperature = (2 / 3) * (average_ke / BOLTZMANN_CONSTANT)

            ax.hist(speeds, bins=50, color='skyblue', edgecolor='black')
            ax.set_title("Live Particle Speed Histogram")
            ax.set_xlabel("Speed")
            ax.set_ylabel("Frequency")
            ax.grid(True, axis='y', linestyle='--', alpha=0.7)

            # Show average speed line
            ax.axvline(average_speed, color='red', linestyle='--', linewidth=2, label=f"Avg Speed: {average_speed:.2f} m/s")
            ax.legend()

            # Display values
            ax.text(0.95, 0.95,
                    f"Avg Speed: {average_speed:.2f}\n"
                    f"Avg KE: {average_ke:.2e} J\n"
                    f"Temp: {temperature:.2e} K",
                    transform=ax.transAxes, fontsize=12,
                    verticalalignment='top', horizontalalignment='right',
                    bbox=dict(facecolor='white', alpha=0.6, edgecolor='gray'))

        plt.tight_layout()
        plt.pause(0.01)
        time.sleep(interval)

if __name__ == "__main__":
    live_plot_histogram("speeds.csv", interval=1)

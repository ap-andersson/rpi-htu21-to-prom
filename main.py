import signal
import time
import os
import sys

# Imports for the temp sensor on the GPIO pins
import board
import adafruit_htu21d

# Imports for proemtheus
from prometheus_client import Gauge, start_http_server, REGISTRY, GC_COLLECTOR, PLATFORM_COLLECTOR, PROCESS_COLLECTOR

# Remove default metrics
REGISTRY.unregister(GC_COLLECTOR)
REGISTRY.unregister(PLATFORM_COLLECTOR)
REGISTRY.unregister(PROCESS_COLLECTOR)

# Create Prometheus gauges
gh = Gauge('humidity', 'Humidity percentage measured by the sensor')
gt = Gauge('temperature', 'Temperature measured by the sensor in celsius')
ct = Gauge('cpu_temp', 'RPI CPU Temp')

# Some config for the temp sensor
port = 1
address = 0x40
i2c = board.I2C()

# A global flag to control the main loop
keep_running = True

class GracefulKiller:
    """
    A class to handle SIGINT and SIGTERM signals gracefully.
    It sets the 'keep_running' flag to False.
    """
    def __init__(self):
        # Register the signal handlers for SIGINT and SIGTERM
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def exit_gracefully(self, signum, frame):
        """
        Signal handler that sets the global flag to stop the loop.
        """
        global keep_running
        # You can add logging here to record that a signal was received
        print(f"Received signal: {signum}. Shutting down...", flush=True)
        keep_running = False

def collect(sensor):
    
    try:
        t = sensor.temperature
        h = sensor.relative_humidity
    except Exception as e:
        print(f"Error reading sensor: {e}")
        return
    
    cpu_temp = get_cpu_temperature()
    if cpu_temp is None:
        return
    
    humidity = round(h)
    temperature = round(t, 1)
    cpu = round(cpu_temp, 1)
    
    gh.set(humidity)
    gt.set(temperature)
    ct.set(cpu)

    print(f"Data collected and set. Humidity: {humidity}%. Temperature: {temperature}C. Cpu: {cpu}C", flush=True)

def get_cpu_temperature():
    """
    Reads the CPU temperature from the system file.
    """
    try:
        with open("/sys/class/thermal/thermal_zone0/temp", "r") as f:
            temp_str = f.read().strip()
            return float(temp_str) / 1000.0
    except FileNotFoundError:
        return None  # Or handle the error as you see fit
    except Exception as e:
        print(f"Error while reading CPU temp: {e}")
        return None

def main():
    """
    The main application entry point.
    """
    # Get the interval from an environment variable for flexibility,
    # defaulting to 60 seconds.
    try:
        # It's good practice to make configuration external
        run_interval_seconds = int(os.getenv("RUN_INTERVAL_SECONDS", "60"))
    except ValueError:
        print("Error: RUN_INTERVAL_SECONDS environment variable must be an integer.", file=sys.stderr)
        sys.exit(1)

    print(f"Application starting. Tasks will run every {run_interval_seconds} seconds.", flush=True)
    print("Press Ctrl+C to exit.", flush=True)
    
    sensor = adafruit_htu21d.HTU21D(i2c)
    
    # Expose metrics
    metrics_port = 8000
    start_http_server(metrics_port)
    print("Serving sensor metrics on :{}".format(metrics_port))
    

    # The main loop that continues as long as `keep_running` is True
    while keep_running:
        
        try:
            collect(sensor)
        except Exception as e:
            print(f"Error while collecting, will try again next time. Error: {e}", flush=True)

        # Wait for the next interval, but check for the shutdown signal frequently.
        # This makes the container stop much faster if a shutdown is requested
        # during the sleep period.
        sleep_chunk = 1 # sleep for 1 second at a time
        for _ in range(run_interval_seconds // sleep_chunk):
            if not keep_running:
                break
            time.sleep(sleep_chunk)
        
        # This handles any remainder if the interval isn't a multiple of the chunk
        if keep_running:
            time.sleep(run_interval_seconds % sleep_chunk)


    # This part of the code is executed after the loop has been broken.
    print("Application shutting down.", flush=True)
    
    # Cleanup here if needed
    
    sys.exit(0)


if __name__ == "__main__":
    # Initialize the killer to start listening for signals
    killer = GracefulKiller()
    main()
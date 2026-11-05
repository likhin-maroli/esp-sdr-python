import serial
import time
import numpy as np
import matplotlib.pyplot as plt
import zlib 

PORT = "/dev/ttyACM0"
BAUD = 2000000
FREQ = 2457
SAMPLE_RATE = 80e6


ser = serial.Serial(PORT, BAUD, timeout=3)

time.sleep(1)

def command(cmd):
    ser.write((cmd + '\n').encode())
    ser.flush()
    response = ser.readline().decode(errors="replace").strip()
    print("TX:", cmd)
    print("RX:", response)
    return response

def read_exact(size):
    data = bytearray()
    while len(data) < size:
        chunk = ser.read(size - len(data))
        if not chunk:
            raise TimeoutError("Serial timeout")
        data.extend(chunk)
    return bytes(data)


nounce = 123456789

response = command(f"SYNC {nounce}")

if response!= f"SYNC {nounce}":
    raise RuntimeError(f"Synchronization with the firmware failed")


def capture_iq(freq, num_samples, rate_code):
    command(f"FREQ {freq}")
    header = command(f"CAP16 {num_samples} {rate_code}")
    parts = header.split()
    if parts[0] != "DATA":
      raise RuntimeError("Invalid response")
    count = int(parts[1])
    expected_crc = int(parts[2], 16)
    capture_us = float(parts[3])
    raw = read_exact(count * 2)
    actual_crc = zlib.crc32(raw) & 0xffffffff
    if expected_crc != actual_crc:
      raise RuntimeError("CRC Mismatch")
    else:
      print("CRC Check OK")
    data = np.frombuffer(raw, dtype=np.int8)
    I =  data[0::2].astype(np.float32)
    Q = -data[1::2].astype(np.float32)
    samples = I + 1j * Q
    return samples


iq = capture_iq(FREQ, 1600, 0)


N = len(iq)

# Time axis in microseconds
time = np.arange(N) / SAMPLE_RATE * 1e6

plt.figure(figsize=(12, 5))

plt.plot(time, iq.real, label="I")
plt.plot(time, iq.imag, label="Q")

plt.xlabel("Time (µs)")
plt.ylabel("Amplitude")
plt.title("Received IQ Signal")

plt.legend()
plt.grid(True)
plt.tight_layout()
plt.show()


magnitude = np.abs(iq)

plt.figure(figsize=(12, 5))
plt.plot(time, magnitude)

plt.xlabel("Time (µs)")
plt.ylabel("Magnitude")
plt.title("IQ Signal Magnitude")
plt.grid(True)
plt.show()

I = iq.real
Q = iq.imag

plt.figure(figsize=(12, 5))

plt.scatter(I, Q, s=2, alpha=0.5)

plt.xlabel("In-phase (I)")
plt.ylabel("Quadrature (Q)")
plt.title("IQ Scatter Plot")

plt.axhline(0, color="gray", linewidth=0.5)
plt.axvline(0, color="gray", linewidth=0.5)

plt.grid(True)
plt.axis("equal")

plt.tight_layout()
plt.show()
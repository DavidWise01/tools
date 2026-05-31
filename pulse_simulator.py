#!/usr/bin/env python3
"""
PULSE Language Interpreter & Simulator
For the Natural Law Union lattice
Author: Grok (with ROOT0)
"""

import time

def pulse_step(pulse: str) -> str:
    """Simulate one pulse cycle and return the echo."""
    if pulse == "...":
        return ".."
    elif pulse == "..":
        return "."
    elif pulse == ".":
        return " "  # space = micro-death / reset
    else:
        return "?"

def simulate_pulse_sequence(steps: int = 5, delay: float = 0.4):
    """Run a sequence of 3-2-1-0 pulses."""
    print("=== PULSE SIMULATOR ===")
    print("Pulse language: ... (wide) → .. (narrow) → . (contact) → space (reset)\n")
    
    sequence = ["...", "..", ".", " "]
    
    for i in range(steps):
        for p in sequence:
            echo = pulse_step(p)
            print(f"Input:  {p:4}  →  Echo: {echo:4}  |  Cycle {i+1}")
            time.sleep(delay)
        print("-" * 40)

def interactive_mode():
    print("=== PULSE INTERACTIVE MODE ===")
    print("Type ... .. . or space. Type 'quit' to exit.\n")
    
    while True:
        user_input = input("Pulse > ").strip()
        if user_input.lower() in ["quit", "exit", "q"]:
            print("Pulse session ended.")
            break
        echo = pulse_step(user_input)
        print(f"Echo:   {echo}\n")

if __name__ == "__main__":
    mode = input("Mode (simulate / interactive): ").strip().lower()
    if mode == "simulate":
        steps = int(input("Number of cycles (default 5): ") or 5)
        simulate_pulse_sequence(steps)
    elif mode == "interactive":
        interactive_mode()
    else:
        print("Usage: simulate or interactive")

# MultiplayergameSim
**1. Clock Drift Simulation**
Each client has its own LocalClock thread. The clock does not use real
time; instead, it increments using a tick value that varies randomly:

    tick = 0.05 + random.uniform(-0.01, 0.01)

This causes each client's logical clock to drift differently, simulating
real distributed system clocks that slowly become unsynchronized.

**2. Clock Synchronization – Cristian’s Algorithm**
The server acts as a trusted time server. Clients periodically:
  - Record local time t0
  - Send TIME_REQUEST to server
  - Receive TIME_RESPONSE with server_time
  - Record local time t1
  - Compute RTT = t1 - t0
  - Estimate true time ≈ server_time + RTT/2
  - Adjust local clock offset

This keeps all clients synchronized with the server’s time despite drift.

**3. Action Timestamps**
Each user action (move, shoot, pickup, etc.) is assigned a timestamp from
the client’s synchronized logical clock. This ensures that actions
represent when they occurred in game time, not when they reached the
server.

**4. Latency Simulation**
Before sending an action, a client waits a random delay:

    time.sleep(random.uniform(0.05, 0.5))

This simulates network lag between players.

**5. Fairness – Server Action Ordering**
The server does NOT trust arrival order. It:
  - Stores incoming actions in a queue
  - Sorts them by (timestamp, server_receive_time)
  - Broadcasts sorted actions to both players

Because clocks are synchronized via Cristian’s algorithm, this ordering
approximates the real-time order of events in the game world, rather than
network arrival order. This avoids giving unfair advantage to players with
lower latency or “fast” local clocks.

**6. Expected Output**
Both clients display the same ordered stream of actions, such as:

    [Player 1] ACTION: Player 2 -> move (ts=2.1532)
    [Player 1] ACTION: Player 1 -> shoot (ts=2.5401)

The same sequence appears on Player 2’s screen. This demonstrates that
clock drift, synchronization, and action ordering are all handled
correctly for fairness in the multiplayer simulation.

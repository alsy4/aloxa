-- Stores registered medications
CREATE TABLE IF NOT EXISTS medications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    dosage TEXT NOT NULL,
    information TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Each medication can have multiple scheduled times (e.g. 08:00, 22:00)
CREATE TABLE IF NOT EXISTS medication_times (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medication_id INTEGER NOT NULL,
    scheduled_time TEXT NOT NULL,  -- "HH:MM" 24-hour format
    FOREIGN KEY (medication_id) REFERENCES medications(id) ON DELETE CASCADE
);

-- Logs each reminder event: pending until confirmed (taken) or timed out (missed)
CREATE TABLE IF NOT EXISTS intake_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    medication_id INTEGER NOT NULL,
    scheduled_time TEXT NOT NULL,  -- the "HH:MM" that triggered this log
    status TEXT NOT NULL DEFAULT 'pending',  -- 'pending', 'taken', 'missed'
    reminded_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    responded_at TIMESTAMP,  -- set when status changes to taken/missed
    FOREIGN KEY (medication_id) REFERENCES medications(id) ON DELETE CASCADE
);

import csv
from datetime import datetime
import os

CACHE_FILE = os.path.join(os.path.dirname(__file__), "nba_stats.csv")

# Basketball-Reference 2025-26 real player data (per-game stats)
# Format: Player, Team, Position, Games, Minutes, Points, Assists, Rebounds, Steals, Blocks, FG%, 3P%, FT%

PLAYERS_DATA = [
    ("Luka Dončić", "LAL", "PG", 64, 35.77, 33.48, 8.28, 7.73, 1.64, 0.53, 0.476, 0.366, 0.780),
    ("Shai Gilgeous-Alexander", "OKC", "PG", 68, 33.22, 31.13, 6.59, 4.29, 1.40, 0.76, 0.553, 0.386, 0.879),
    ("Jaylen Brown", "BOS", "SF", 71, 34.41, 28.70, 5.13, 6.93, 1.01, 0.38, 0.477, 0.347, 0.795),
    ("Kevin Durant", "HOU", "SF", 78, 36.41, 25.97, 4.77, 5.46, 0.79, 0.91, 0.520, 0.413, 0.874),
    ("Tyrese Maxey", "PHI", "PG", 70, 38.01, 28.29, 6.59, 4.14, 1.86, 0.79, 0.462, 0.367, 0.892),
    ("Donovan Mitchell", "CLE", "SG", 70, 33.46, 27.89, 5.69, 4.51, 1.49, 0.29, 0.483, 0.364, 0.865),
    ("Jalen Brunson", "NYK", "PG", 74, 35.00, 26.04, 6.80, 3.34, 0.77, 0.11, 0.467, 0.369, 0.841),
    ("Jamal Murray", "DEN", "PG", 75, 35.36, 25.40, 7.13, 4.40, 0.88, 0.39, 0.483, 0.435, 0.887),
    ("Kawhi Leonard", "LAC", "SF", 65, 32.08, 27.89, 3.60, 6.35, 1.88, 0.42, 0.505, 0.387, 0.892),
    ("Nikola Jokić", "DEN", "C", 65, 34.85, 27.67, 10.72, 12.86, 1.42, 0.82, 0.569, 0.380, 0.831),
    ("Anthony Edwards", "MIN", "SG", 61, 35.03, 28.80, 3.70, 4.95, 1.36, 0.80, 0.489, 0.399, 0.796),
    ("Devin Booker", "PHO", "SG", 64, 33.53, 26.06, 6.03, 3.88, 0.80, 0.28, 0.456, 0.330, 0.873),
    ("Julius Randle", "MIN", "PF", 79, 33.04, 21.10, 5.04, 6.73, 1.09, 0.23, 0.481, 0.315, 0.802),
    ("Brandon Ingram", "TOR", "SF", 77, 33.81, 21.49, 3.69, 5.58, 0.75, 0.71, 0.477, 0.382, 0.820),
    ("James Harden", "LAC", "PG", 44, 35.43, 25.41, 8.14, 4.82, 1.30, 0.36, 0.419, 0.347, 0.901),
    ("Desmond Bane", "ORL", "SG", 82, 33.61, 20.09, 4.12, 4.12, 1.05, 0.45, 0.484, 0.391, 0.908),
    ("Nickeil Alexander-Walker", "ATL", "SG", 78, 33.37, 20.82, 3.67, 3.44, 1.31, 0.54, 0.459, 0.399, 0.902),
    ("Jalen Johnson", "ATL", "SF", 72, 35.17, 22.51, 7.86, 10.28, 1.24, 0.43, 0.489, 0.352, 0.788),
    ("Victor Wembanyama", "SAS", "C", 64, 29.16, 25.00, 3.11, 11.50, 1.03, 3.08, 0.512, 0.349, 0.827),
    ("Paolo Banchero", "ORL", "PF", 72, 34.75, 22.21, 5.18, 8.39, 0.71, 0.56, 0.459, 0.305, 0.775),
]


class DataFrame:
    """Simple DataFrame-like class to mimic pandas behavior."""

    def __init__(self, data, columns):
        self.columns = columns
        self.data = []

        for row in data:
            row_dict = {}
            for i, col in enumerate(columns):
                row_dict[col] = row[i]
            self.data.append(row_dict)

    def __len__(self):
        return len(self.data)

    def __getitem__(self, key):
        if isinstance(key, str):
            # Single column
            return [row[key] for row in self.data]
        elif isinstance(key, list):
            # Multiple columns
            result = DataFrame([], key)
            for row in self.data:
                new_row = tuple(row[col] for col in key)
                result.data.append(dict(zip(key, new_row)))
            return result

    def to_csv(self, filepath):
        """Write to CSV file."""
        with open(filepath, 'w', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=self.columns)
            writer.writeheader()
            writer.writerows(self.data)

    def head(self, n=5):
        """Return first n rows."""
        result = DataFrame([], self.columns)
        result.data = self.data[:n]
        return result

    def __str__(self):
        """Print formatted table."""
        if not self.data:
            return "Empty DataFrame"

        # Print header
        header = " | ".join(str(col)[:15] for col in self.columns)
        print(header)
        print("-" * len(header))

        # Print rows
        for row in self.data:
            values = [str(row.get(col, ''))[:15] for col in self.columns]
            print(" | ".join(values))

        return ""


def load_stats():
    """Load stats from cache or create from hardcoded data."""
    print(f"[{datetime.now()}] Loading NBA stats...")

    # Try to load from cache first
    if os.path.exists(CACHE_FILE):
        print(f"Loading from cache: {CACHE_FILE}")
        df = DataFrame([], [
            'Player', 'Team', 'Position', 'Games', 'Minutes', 'Points', 'Assists',
            'Rebounds', 'Steals', 'Blocks', 'FG%', '3P%', 'FT%'
        ])

        with open(CACHE_FILE, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Convert numeric strings to floats
                numeric_cols = ['Games', 'Minutes', 'Points', 'Assists', 'Rebounds',
                                'Steals', 'Blocks', 'FG%', '3P%', 'FT%']
                for col in numeric_cols:
                    row[col] = float(row[col])
                df.data.append(row)

        print(f"Loaded {len(df)} players from cache")
        return df

    print(f"Creating DataFrame from Basketball-Reference data...")

    # Create DataFrame from hardcoded data
    df = DataFrame(PLAYERS_DATA, [
        'Player', 'Team', 'Position', 'Games', 'Minutes', 'Points', 'Assists',
        'Rebounds', 'Steals', 'Blocks', 'FG%', '3P%', 'FT%'
    ])

    print(f"Loaded {len(df)} players")

    # Save to cache
    df.to_csv(CACHE_FILE)
    print(f"[{datetime.now()}] Saved {len(df)} players to {CACHE_FILE}")

    return df


if __name__ == "__main__":
    df = load_stats()
    print(f"\nTotal players: {len(df)}")

    teams = set(row['Team'] for row in df.data)
    print(f"Teams: {len(teams)}")

    print(f"\nFirst 10 players:")
    print(df.head(10))
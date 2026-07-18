# Dedup — Find and Organize Duplicate Files

Dedup is a simple tool that helps you **find duplicate files** across
your computer — even if they are spread across different folders,
different drives, or different Windows user accounts.

It works especially well with **OneDrive**, which often stores files as
“cloud‑only” placeholders. Dedup makes sure everything is downloaded
locally before scanning so you get accurate results.

Dedup never deletes anything automatically.
You stay in control.

---

## 🌟 What Dedup Does

- Looks through the folders you choose
- Downloads any OneDrive files that are still “cloud‑only”
- Creates a fingerprint for each file
- Finds files that are **exactly identical**, even if names differ
- Gives you a clean report of duplicates

It’s perfect for:

- Cleaning up old photo collections
- Merging files from multiple Windows accounts
- Organizing backups from external drives
- Finding duplicates across OneDrive and local folders

---

## 📁 Before You Start

You’ll need:

- Python installed
- The Dedup project folder
- A `.env` file that tells Dedup which folders to scan

### Example `.env` file

```env
# --- Path to your conda environment ---
# Update the username and env name if needed
CONDA_PREFIX=C:\Users\alterego\miniforge3\envs\dedup-py311

# --- Ensure VS Code uses the correct Python interpreter ---
PYTHON_EXECUTABLE=C:\Users\alterego\miniforge3\envs\dedup-py311\python.exe

# --- Make your project importable (dedup/ folder) ---
PYTHONPATH=${workspaceFolder}\dedup

# --- Optional: database definitions ---
DEDUP_DB_BACKEND=postgres
DEDUP_DB_PG_URL=postgresql://dedup_usr:L6rvwemlBTMyJsNzVLKf@localhost:5432/dedup
DEDUP_DB_SQLite_location=C:\DedupDb\sqlite\index.db

# --- Optional: disk mount points (Windows style) ---
DEDUP_SCAN_ROOT_1=C:\Users\alterego\OneDrive
DEDUP_SCAN_ROOT_2=C:\shared\jpjofresm@hotmail.com
#DEDUP_SCAN_ROOT_3=C:\Public

# --- Optional: hash selection ---
# --- defaults to SHA256 if blake is not available
HASH_ALGO=blake3
```

---

## 🚀 How to Use Dedup

You run Dedup from a terminal (Command Prompt or the VS Code terminal).

### 1. Create the database (only once)

```shell
python -m dedup.cli init-db
```

### 2. Make sure OneDrive files are downloaded (only if files are in OneDrive)

OneDrive sometimes keeps files “in the cloud” until you open them.
Dedup needs the real files to compare them.

Run:

```shell
python -m dedup.cli hydrate
```

This will download any cloud‑only files in your scan folders.

### 3. Scan your folders

This step finds all the files and records them in the database.

```shell
python -m dedup.cli scan
```

### 4. Hash the files

This step creates a fingerprint for each file so Dedup can compare them.

```shell
python -m dedup.cli hash
```

You can speed it up by processing more files at once:

```shell
python -m dedup.cli hash --batch 500
```

### 5. See your duplicates

```shell
python -m dedup.cli report-dups
```

You’ll get a list like:

```text
abc123... -> 4 files
def456... -> 2 files
```

Future versions will include a visual viewer to help you decide what to delete.

## 💡 Tips for Windows Users

**OneDrive users**:

- Right‑click your OneDrive folders and choose: *Always keep on this device*

This makes things faster and avoids missing files.

**Multiple Windows accounts**:

If you want to scan files from another user account, create a shared folder and use NTFS junctions and
give propper acces to the user running the code to read the files:

```cmd
mklink /J C:\SharedData\User2_OneDrive C:\Users\User2\OneDrive

icacls "C:\Users\OtherUser\OneDrive" /grant ThisUser:(RX) /T

```

Then point Dedup to the shared folder in .env.

## 🔒 What Dedup Does Not Do

It does not delete files

It does not modify your folders

It does not upload anything

It does not require admin rights

It simply analyzes your files and tells you which ones are duplicates.

## 🛠 Troubleshooting

> “Some files are missing”

Run:

```shell
python -m dedup.cli hydrate
```

> “I can’t access another user’s OneDrive folder”

Use a shared folder and NTFS junctions.

> “Hashing is slow”

Increase batch size:

```shell
python -m dedup.cli hash --batch 1000
```

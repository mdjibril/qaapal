import os
import json
import glob
import re
import argparse
from auth_utils import get_admin_supabase

def _find_json_files():
    files = []
    files.extend(glob.glob("data/nos/*.json"))
    files.extend(glob.glob("data/nos/**/*.json", recursive=True))
    files.extend(glob.glob("data/level-*/*.json"))
    files.extend(glob.glob("data/level-*/**/*.json", recursive=True))

    # Preserve order while removing duplicates
    seen = set()
    unique_files = []
    for path in files:
        if path not in seen:
            seen.add(path)
            unique_files.append(path)
    return unique_files

def _infer_level(file_path, data):
    if isinstance(data.get("level"), int):
        return data["level"]
    if isinstance(data.get("level"), str) and data["level"].isdigit():
        return int(data["level"])

    level_match = re.search(r"level[-_ ]?(\d+)", file_path, re.IGNORECASE)
    if level_match:
        return int(level_match.group(1))

    level_match = re.search(r"levels?\s*(\d+)", os.path.basename(file_path), re.IGNORECASE)
    if level_match:
        return int(level_match.group(1))

    return None

def _check_supabase_connection(client):
    """Fail fast when the Supabase host is unreachable or misconfigured."""
    try:
        client.table("trades").select("id").limit(1).execute()
        return True
    except Exception as e:
        print("❌ Could not connect to Supabase.")
        print(f"   Reason: {e}")
        print("   Check PROJECT_URL, DNS/network access, and SERVICE_ROLE_KEY.")
        return False

def seed_nos_data():
    """
    Reads JSON files from the data directory and populates the Supabase database.
    """
    parser = argparse.ArgumentParser(description="Seed NOS data into Supabase.")
    parser.add_argument(
        "--file",
        dest="file_path",
        help="Seed only one NOS JSON file instead of scanning the data directory.",
    )
    parser.add_argument(
        "--trade",
        dest="trade_name",
        help="Seed only files whose trade_name matches this value.",
    )
    parser.add_argument(
        "--level",
        dest="level",
        type=int,
        help="Seed only files for this NOS level.",
    )
    args, _ = parser.parse_known_args()

    client = get_admin_supabase()

    if not _check_supabase_connection(client):
        return
    
    if not os.path.exists("data"):
        os.makedirs("data")
        print("📂 Created 'data' directory. Please place your JSON files there.")

    if args.file_path:
        json_files = [args.file_path]
    else:
        json_files = _find_json_files()
    
    if not json_files:
        print("⚠️ No JSON files found in data/. Please add your extracted NOS files there.")
        return

    stats = {
        "trades": 0,
        "trade_levels": 0,
        "units": 0,
        "learning_outcomes": 0,
        "performance_criteria": 0,
    }
    matched_files = 0
    trade_filter = args.trade_name.strip().lower() if args.trade_name else None

    for file_path in json_files:
        print(f"🔍 Processing {file_path}...")

        try:
            with open(file_path, 'r') as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"❌ Skipping {file_path}: invalid JSON ({e})")
            continue
            
        trade_name = data.get("trade_name")
        level = _infer_level(file_path, data)
        units = data.get("units", [])

        if not trade_name:
            print(f"Skipping {file_path}: Missing trade_name")
            continue
        if trade_filter and trade_name.strip().lower() != trade_filter:
            print(f"Skipping {file_path}: trade_name '{trade_name}' does not match '{args.trade_name}'.")
            continue
        if level is None:
            print(f"Skipping {file_path}: Missing level and unable to infer it from the file name/path.")
            continue
        if args.level is not None and level != args.level:
            print(f"Skipping {file_path}: level {level} does not match requested level {args.level}.")
            continue

        matched_files += 1

        try:
            # 1. Handle Trade
            trade_res = client.table("trades").select("id").eq("name", trade_name).execute()
            if trade_res.data:
                trade_id = trade_res.data[0]['id']
                print(f"✅ Trade '{trade_name}' verified (ID: {trade_id})")
            else:
                print(f"➕ Inserting Trade: {trade_name}")
                ins_trade = client.table("trades").insert({"name": trade_name}).execute()
                trade_id = ins_trade.data[0]['id']
                stats["trades"] += 1

            # 1b. Handle Trade Level
            level_display_name = data.get("display_name") or f"{trade_name} - Level {level}"
            trade_level_res = (
                client.table("trade_levels")
                .select("id")
                .eq("trade_id", trade_id)
                .eq("level", level)
                .execute()
            )
            if trade_level_res.data:
                trade_level_id = trade_level_res.data[0]["id"]
                print(f"✅ Trade level '{level_display_name}' verified (ID: {trade_level_id})")
            else:
                print(f"➕ Inserting Trade Level: {level_display_name}")
                ins_trade_level = client.table("trade_levels").insert({
                    "trade_id": trade_id,
                    "level": level,
                    "display_name": level_display_name,
                    "source_file": os.path.basename(file_path),
                }).execute()
                trade_level_id = ins_trade_level.data[0]["id"]
                stats["trade_levels"] += 1

            # 2. Handle Units
            for unit in units:
                unit_code = unit.get("code")
                unit_title = unit.get("title")
                
                unit_res = (
                    client.table("units")
                    .select("id")
                    .eq("code", unit_code)
                    .eq("trade_level_id", trade_level_id)
                    .execute()
                )
                if unit_res.data:
                    unit_id = unit_res.data[0]['id']
                else:
                    print(f"  + Unit: {unit_code}")
                    ins_unit = client.table("units").insert({
                        "trade_id": trade_id,
                        "trade_level_id": trade_level_id,
                        "code": unit_code,
                        "title": unit_title
                    }).execute()
                    unit_id = ins_unit.data[0]['id']
                    stats["units"] += 1

                # 3. Handle Learning Outcomes
                for lo in unit.get("learning_outcomes", []):
                    lo_num = lo.get("lo_num")
                    lo_desc = lo.get("description")
                    
                    lo_res = client.table("learning_outcomes").select("id").eq("unit_id", unit_id).eq("lo_num", lo_num).execute()
                    if lo_res.data:
                        lo_id = lo_res.data[0]['id']
                    else:
                        ins_lo = client.table("learning_outcomes").insert({
                            "unit_id": unit_id,
                            "lo_num": lo_num,
                            "description": lo_desc
                        }).execute()
                        lo_id = ins_lo.data[0]['id']
                        stats["learning_outcomes"] += 1

                    # 4. Handle Performance Criteria
                    for pc in lo.get("performance_criteria", []):
                        pc_code = pc.get("pc_code")
                        pc_desc = pc.get("description")
                        
                        pc_check = client.table("performance_criteria").select("id").eq("lo_id", lo_id).eq("pc_code", pc_code).execute()
                        if not pc_check.data:
                            client.table("performance_criteria").insert({"lo_id": lo_id, "pc_code": pc_code, "description": pc_desc}).execute()
                            stats["performance_criteria"] += 1
        
        except Exception as e:
            print(f"❌ Error processing {trade_name}: {e}")
            if "23505" in str(e):
                print("💡 Hint: This usually means your database sequences are out of sync. Run the SQL fix in the Supabase Dashboard.")
            continue
        
        print(f"🏁 Finished processing {trade_name}\n")

    if (args.file_path or args.trade_name or args.level is not None) and matched_files == 0:
        print("⚠️ No NOS files matched the requested filter(s).")

    print(
        "✅ Seed summary: "
        f"{stats['trades']} trades, "
        f"{stats['trade_levels']} trade levels, "
        f"{stats['units']} units, "
        f"{stats['learning_outcomes']} learning outcomes, "
        f"{stats['performance_criteria']} performance criteria inserted."
    )

if __name__ == "__main__":
    print("🚀 Starting NOS Database Seeding...")
    seed_nos_data()

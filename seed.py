import os
import json
import glob
from auth_utils import get_admin_supabase

def seed_nos_data():
    """
    Reads JSON files from the data/nos directory and populates the Supabase database.
    """
    client = get_admin_supabase()
    
    if not os.path.exists("data/nos"):
        os.makedirs("data/nos")
        print("📂 Created 'data/nos' directory. Please place your JSON files there.")

    # Path to your extracted JSON files
    json_files = glob.glob("data/nos/*.json")
    
    if not json_files:
        print("⚠️ No JSON files found in data/nos/. Please add your extracted NOS files there.")
        return

    for file_path in json_files:
        print(f"🔍 Processing {file_path}...")
        
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        trade_name = data.get("trade_name")
        units = data.get("units", [])
        
        if not trade_name:
            print(f"Skipping {file_path}: Missing trade_name")
            continue

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

            # 2. Handle Units
            for unit in units:
                unit_code = unit.get("code")
                unit_title = unit.get("title")
                
                unit_res = client.table("units").select("id").eq("code", unit_code).eq("trade_id", trade_id).execute()
                if unit_res.data:
                    unit_id = unit_res.data[0]['id']
                else:
                    print(f"  + Unit: {unit_code}")
                    ins_unit = client.table("units").insert({
                        "trade_id": trade_id,
                        "code": unit_code,
                        "title": unit_title
                    }).execute()
                    unit_id = ins_unit.data[0]['id']

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

                    # 4. Handle Performance Criteria
                    for pc in lo.get("performance_criteria", []):
                        pc_code = pc.get("pc_code")
                        pc_desc = pc.get("description")
                        
                        pc_check = client.table("performance_criteria").select("id").eq("lo_id", lo_id).eq("pc_code", pc_code).execute()
                        if not pc_check.data:
                            client.table("performance_criteria").insert({"lo_id": lo_id, "pc_code": pc_code, "description": pc_desc}).execute()
        
        except Exception as e:
            print(f"❌ Error processing {trade_name}: {e}")
            if "23505" in str(e):
                print("💡 Hint: This usually means your database sequences are out of sync. Run the SQL fix in the Supabase Dashboard.")
            continue
        
        print(f"🏁 Finished processing {trade_name}\n")

if __name__ == "__main__":
    print("🚀 Starting NOS Database Seeding...")
    seed_nos_data()
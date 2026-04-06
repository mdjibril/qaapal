import sqlite3

def populate_nsq_data():
    conn = sqlite3.connect('nsq_audit.db')
    cursor = conn.cursor()

    # --- 1. RESET SCHEMA (Drop old versions to fix column errors) ---
    cursor.execute("DROP TABLE IF EXISTS performance_criteria")
    cursor.execute("DROP TABLE IF EXISTS learning_outcomes")
    cursor.execute("DROP TABLE IF EXISTS units")
    cursor.execute("DROP TABLE IF EXISTS trades")

    # --- 2. CREATE FRESH TABLES WITH CORRECT COLUMNS ---
    cursor.execute("CREATE TABLE trades (id INTEGER PRIMARY KEY, name TEXT)")
    
    # Notice 'code' is now explicitly included here:
    cursor.execute("""
        CREATE TABLE units (
            id INTEGER PRIMARY KEY, 
            trade_id INTEGER, 
            code TEXT, 
            title TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE learning_outcomes (
            id INTEGER PRIMARY KEY, 
            unit_id INTEGER, 
            lo_num TEXT, 
            desc TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE performance_criteria (
            id INTEGER PRIMARY KEY, 
            lo_id INTEGER, 
            pc_code TEXT, 
            desc TEXT
        )
    """)

    # --- 3. INSERT TRADE ---
    cursor.execute("INSERT INTO trades (id, name) VALUES (1, 'ICT Computer Hardware Repairs L3')")
    trade_id = 1
    
    # ... keep the rest of your loop (for u_code, u_title, lo_list in full_nos: ...)
    # --- 3. DATA STRUCTURE ---
    # Format: [Unit Code, Unit Title, [ (LO_Num, LO_Desc, [ (PC_Code, PC_Desc) ]) ]]
    full_nos = [
        ["ICT/CMR/001/L3", "Health and Safety in Hardware Maintenance", [
            ("LO 1", "Apply health and safety regulations", [
                ("PC 1.1", "Explain key health and safety regulations."),
                ("PC 1.2", "Demonstrate use of PPE during installation/repair.")
            ]),
            ("LO 2", "Mitigate ESD and electrical hazards", [
                ("PC 1.3", "Demonstrate safe handling/discharge of static."),
                ("PC 1.4", "Ensure proper grounding techniques."),
                ("PC 2.1", "Identify hazardous materials needing special disposal."),
                ("PC 2.2", "Follow local regulations for e-waste disposal."),
                ("PC 2.3", "Demonstrate safe dismantling/segregating for disposal."),
                ("PC 2.4", "Maintain accurate waste disposal documentation.")
            ]),
            ("LO 3", "Follow safe e-waste disposal procedures", [
                ("PC 3.1", "Identify types of e-waste and environmental impact."),
                ("PC 3.2", "Demonstrate procedures for segregation and recycling."),
                ("PC 3.3", "Ensure compliance with hazardous material guidelines.")
            ])
        ]],
        ["ICT/GSS/002/L3", "Teamwork", [
            ("LO 1", "Importance of Teamwork", [
                ("PC 1.1", "Explain role of teamwork in productivity."),
                ("PC 1.2", "Describe characteristics of effective teams."),
                ("PC 1.3", "Identify benefits of collaboration.")
            ]),
            ("LO 2", "Contribute to Team Goals", [
                ("PC 2.1", "Identify team goals and individual responsibilities."),
                ("PC 2.2", "Willingness to take on tasks/share knowledge."),
                ("PC 2.3", "Prioritize team success over individual achievement.")
            ]),
            ("LO 3", "Collaborate in Problem-Solving", [
                ("PC 3.1", "Participate in brainstorming sessions."),
                ("PC 3.2", "Engage in group decision-making."),
                ("PC 3.3", "Value diverse perspectives of team members.")
            ])
        ]],
        ["ICT/GSS/003/L3", "Communication", [
            ("LO 1", "Professional Communication", [
                ("PC 1.1", "Use clear/concise language in verbal/written forms."),
                ("PC 1.2", "Apply professional tone in emails and reports."),
                ("PC 1.3", "Adjust communication style based on audience.")
            ]),
            ("LO 2", "Technology in Communication", [
                ("PC 2.1", "Proficiency in digital communication tools."),
                ("PC 2.2", "Participate in virtual meetings with etiquette."),
                ("PC 2.3", "Utilize collaborative tools for info sharing.")
            ]),
            ("LO 3", "Resolve Communication Barriers", [
                ("PC 3.1", "Identify/address cultural or language barriers."),
                ("PC 3.2", "Encourage open dialogue and active listening."),
                ("PC 3.3", "Apply conflict resolution strategies.")
            ])
        ]],
        ["ICT/CMR/004/L3", "Computer Hardware (Audit & Flow)", [
            ("LO 1", "Review Hardware Components", [
                ("PC 1.1", "Enumerate primary internal components."),
                ("PC 1.2", "Describe functional roles (processing/power)."),
                ("PC 1.3", "Differentiate peripheral device types."),
                ("PC 1.4", "Describe physical attributes of key hardware.")
            ]),
            ("LO 2", "System Architecture & Data Flow", [
                ("PC 2.1", "Explain basic system architecture."),
                ("PC 2.2", "Describe data flow (internal vs external)."),
                ("PC 2.3", "Describe pathways in hardware/software."),
                ("PC 2.4", "Interpret system architecture diagrams.")
            ]),
            ("LO 3", "Compatibility & Specifications", [
                ("PC 3.1", "Discuss clock speed and connectivity standards."),
                ("PC 3.2", "Evaluate compatibility during assembly/upgrades."),
                ("PC 3.3", "Compare options for specific operational needs."),
                ("PC 3.4", "Adhere to manufacturer guidelines.")
            ]),
            ("LO 4", "Assembly & Disassembly Skills", [
                ("PC 4.1", "Demonstrate proper techniques for disassembly."),
                ("PC 4.2", "Identify essential tools for maintenance."),
                ("PC 4.3", "Execute step-by-step assembly of functional PC."),
                ("PC 4.4", "Conduct practical mock assembly exercise.")
            ])
        ]],
        ["ICT/CMR/005/L3", "Installation of Hardware Components", [
            ("LO 1", "Install Internal Components", [
                ("PC 1.1", "Identify required tools for installation."),
                ("PC 1.2", "Safely remove and replace hardware."),
                ("PC 1.3", "Follow manufacturer best practices."),
                ("PC 1.4", "Verify via system boot and BIOS checks.")
            ]),
            ("LO 2", "Configure Peripheral Devices", [
                ("PC 2.1", "Identify input devices."),
                ("PC 2.2", "Identify output and external storage devices."),
                ("PC 2.3", "Demonstrate physical connection of peripherals."),
                ("PC 2.4", "Install necessary drivers and software."),
                ("PC 2.5", "Conduct testing for successful operation.")
            ]),
            ("LO 3", "Cable Management Practices", [
                ("PC 3.1", "Identify cable types (power/data)."),
                ("PC 3.2", "Demonstrate proper routing for airflow."),
                ("PC 3.3", "Secure cables within the case for safety."),
                ("PC 3.4", "Explain impact on system performance.")
            ]),
            ("LO 4", "Optimization Post Installation", [
                ("PC 4.1", "Configure BIOS/UEFI to recognize components."),
                ("PC 4.2", "Adjust boot priorities/enable features."),
                ("PC 4.3", "Perform operating system installations."),
                ("PC 4.4", "Ensure compatibility with hardware."),
                ("PC 4.5", "Verify performance benchmarks.")
            ])
        ]],
        ["ICT/CMR/006/L3", "Troubleshooting Hardware Issues", [
            ("LO 1", "Identify Common Problems", [
                ("PC 1.1", "Recognize symptoms (boot failure, beep codes)."),
                ("PC 1.2", "Differentiate hardware vs software issues."),
                ("PC 1.3", "Observe symptoms for effective analysis."),
                ("PC 1.4", "Utilize checklists for systematic evaluation.")
            ]),
            ("LO 2", "Apply Diagnostic Tools", [
                ("PC 2.1", "Use diagnostic software (POST codes)."),
                ("PC 2.2", "Conduct visual inspection for physical damage."),
                ("PC 2.3", "Use multimeters to measure voltage/resistance."),
                ("PC 2.4", "Interpret results for troubleshooting strategy.")
            ]),
            ("LO 3", "Troubleshooting Methodologies", [
                ("PC 3.1", "Problem identification and hypothesis testing."),
                ("PC 3.2", "Prioritize steps based on severity."),
                ("PC 3.3", "Document steps for future reference."),
                ("PC 3.4", "Communicate solutions to clients/team.")
            ]),
            ("LO 4", "Software Hardware Interaction", [
                ("PC 4.1", "Troubleshoot software-related issues."),
                ("PC 4.2", "Perform maintenance (updates, virus scans)."),
                ("PC 4.3", "Resolve hardware recognition issues."),
                ("PC 4.4", "Demonstrate solutions for knowledge sharing.")
            ]),
            ("LO 5", "Basic Networking Issues", [
                ("PC 5.1", "Diagnose connectivity and slow performance."),
                ("PC 5.2", "Utilize tools (ping, ipconfig, netstat)."),
                ("PC 5.3", "Document solutions for future learning.")
            ])
        ]],
        ["ICT/CMR/007/L3", "Repair and Maintenance", [
            ("LO 1", "Diagnose System Issues", [
                ("PC 1.1", "Conduct systematic diagnostic techniques."),
                ("PC 1.2", "Interpret error messages and codes."),
                ("PC 1.3", "Assess system performance."),
                ("PC 1.4", "Document diagnostic findings.")
            ]),
            ("LO 2", "Hardware Repair/Replacement", [
                ("PC 2.1", "Safe disassembly for component access."),
                ("PC 2.2", "Repair/replace parts adhering to safety."),
                ("PC 2.3", "Verify specifications of replacement parts."),
                ("PC 2.4", "Conduct functionality tests post-repair.")
            ]),
            ("LO 3", "Software Maintenance", [
                ("PC 3.1", "Install/Configure OS and apps."),
                ("PC 3.2", "Perform patches and virus scans."),
                ("PC 3.3", "Troubleshoot software-related issues."),
                ("PC 3.4", "Document software updates.")
            ]),
            ("LO 4", "Preventive Maintenance", [
                ("PC 4.1", "Execute plan including component cleaning."),
                ("PC 4.2", "Analyze effectiveness of maintenance."),
                ("PC 4.3", "Maintain records for continuous monitoring.")
            ]),
            ("LO 5", "Security and Data Protection", [
                ("PC 5.1", "Use firewalls and antivirus."),
                ("PC 5.2", "Conduct data backups/recovery plans."),
                ("PC 5.3", "Explain safe computing practices."),
                ("PC 5.4", "Update protocols based on emerging threats.")
            ])
        ]],
        ["ICT/CMR/008/L3", "Power Supply and Cooling", [
            ("LO 1", "PSU Functionality", [
                ("PC 1.1", "Describe role of PSU in system."),
                ("PC 1.2", "Identify types and connector types."),
                ("PC 1.3", "Determine system power requirements."),
                ("PC 1.4", "Select appropriate unit for configurations.")
            ]),
            ("LO 2", "Configure PSU", [
                ("PC 2.1", "Safe removal and installation of PSU."),
                ("PC 2.2", "Connect PSU to motherboard and peripherals."),
                ("PC 2.3", "Verify functionality via voltage testing."),
                ("PC 2.4", "Troubleshoot power-related issues.")
            ]),
            ("LO 3", "Cooling System Types", [
                ("PC 3.1", "Identify air, liquid, and passive cooling."),
                ("PC 3.2", "Principles of thermal management."),
                ("PC 3.3", "Assess cooling requirements per workload."),
                ("PC 3.4", "Advantages/Disadvantages of cooling methods.")
            ]),
            ("LO 4", "Maintain Cooling Systems", [
                ("PC 4.1", "Install heatsinks and fans correctly."),
                ("PC 4.2", "Configure fan speeds for optimization."),
                ("PC 4.3", "Clean dust using blowers."),
                ("PC 4.4", "Diagnose cooling-related issues."),
                ("PC 4.5", "Resolve identified issues.")
            ]),
            ("LO 5", "Manage Efficiency", [
                ("PC 5.1", "Monitor performance of power and cooling."),
                ("PC 5.2", "Analyze power consumption and temperature."),
                ("PC 5.3", "Implement energy-saving practices."),
                ("PC 5.4", "Develop upgrade strategies.")
            ])
        ]],
        ["ICT/CMR/009/L3", "Data Storage and Backup", [
            ("LO 1", "Storage Device Types", [
                ("PC 1.1", "Identify HDDs, SSDs, Flash, Optical."),
                ("PC 1.2", "Explain pros/cons (speed, cost, durability)."),
                ("PC 1.3", "Analyze role and impact on performance."),
                ("PC 1.4", "Evaluate compatibility with OS.")
            ]),
            ("LO 2", "Configure Storage", [
                ("PC 2.1", "Safe installation and configuration."),
                ("PC 2.2", "Format and partition according to needs."),
                ("PC 2.3", "Configure drive letters and file systems."),
                ("PC 2.4", "Verify through system recognition.")
            ]),
            ("LO 3", "Backup Solutions", [
                ("PC 3.1", "Identify importance and risks of loss."),
                ("PC 3.2", "Evaluate backup methods (Full, Incremental)."),
                ("PC 3.3", "Develop comprehensive backup strategy."),
                ("PC 3.4", "Demonstrate implementation with software.")
            ]),
            ("LO 4", "Data Recovery", [
                ("PC 4.1", "Discuss causes of data loss."),
                ("PC 4.2", "Use software to recover corrupt files."),
                ("PC 4.3", "Use manual recovery for damaged drives."),
                ("PC 4.4", "Document and analyze recovery success.")
            ]),
            ("LO 5", "Security and Integrity", [
                ("PC 5.1", "Explain principles of encryption."),
                ("PC 5.2", "Implement physical security/access control."),
                ("PC 5.3", "Conduct audits for policy compliance."),
                ("PC 5.4", "Dispose of outdated data securely.")
            ])
        ]],
        ["ICT/CMR/010/L3", "Software Interaction with Hardware", [
            ("LO 1", "Role of Device Drivers", [
                ("PC 1.1", "Explain OS-Hardware communication via drivers."),
                ("PC 1.2", "Identify different types of drivers."),
                ("PC 1.3", "Importance of updates for stability."),
                ("PC 1.4", "Evaluate impact of missing drivers.")
            ]),
            ("LO 2", "Install/Update Drivers", [
                ("PC 2.1", "Identify/Download from manufacturer sites."),
                ("PC 2.2", "Use Device Manager to manage drivers."),
                ("PC 2.3", "Troubleshoot installation/compatibility."),
                ("PC 2.4", "Conduct successful installation tests.")
            ]),
            ("LO 3", "BIOS/UEFI Configuration", [
                ("PC 3.1", "Explain role in boot process."),
                ("PC 3.2", "Navigate interface to modify settings."),
                ("PC 3.3", "Optimize boot order and power settings."),
                ("PC 3.4", "Discuss risks of BIOS updates.")
            ]),
            ("LO 4", "Troubleshoot Interactions", [
                ("PC 4.1", "Identify system crashes and malfunctions."),
                ("PC 4.2", "Use tools to find root cause of conflicts."),
                ("PC 4.3", "Implement driver rollbacks/restores."),
                ("PC 4.4", "Document steps for future sharing.")
            ]),
            ("LO 5", "Manage Hardware Resources", [
                ("PC 5.1", "Monitor CPU, RAM, and disk space usage."),
                ("PC 5.2", "Configure resource settings for stability."),
                ("PC 5.3", "Resolve IRQ and I/O address conflicts."),
                ("PC 5.4", "Manage resources in multi-tasking environments.")
            ])
        ]],
        ["ICT/CMR/011/L3", "Computer Networking Basics", [
            ("LO 1", "Fundamental Concepts", [
                ("PC 1.1", "Explain LAN/WAN, protocols, bandwidth."),
                ("PC 1.2", "Differentiate between LAN, WAN, MAN, PAN."),
                ("PC 1.3", "Function of routers, switches, access points."),
                ("PC 1.4", "Identify topologies (Star, Bus, Mesh).")
            ]),
            ("LO 2", "Protocols and Standards", [
                ("PC 2.1", "Role of protocols in communication."),
                ("PC 2.2", "Describe TCP/IP, HTTP, FTP, DHCP."),
                ("PC 2.3", "Discuss OSI model and 7 layers."),
                ("PC 2.4", "Explain how protocols work together.")
            ]),
            ("LO 3", "IP Addressing and Subnetting", [
                ("PC 3.1", "Significance of IP addressing."),
                ("PC 3.2", "Differentiate IPv4 and IPv6."),
                ("PC 3.3", "Calculate subnet masks."),
                ("PC 3.4", "Identify common IP address classes.")
            ]),
            ("LO 4", "Configure Network Connections", [
                ("PC 4.1", "Physical setup using Ethernet cables."),
                ("PC 4.2", "Configure IP, masks, and gateways."),
                ("PC 4.3", "Share resources (files, printers) across LAN."),
                ("PC 4.4", "Test connectivity with ping/traceroute.")
            ]),
            ("LO 5", "Network Security Fundamentals", [
                ("PC 5.1", "Discuss malware, phishing, and access."),
                ("PC 5.2", "Importance of firewalls and encryption."),
                ("PC 5.3", "Securing a network via password changes.")
            ])
        ]]
    ]

    # --- 4. EXECUTION LOOP ---
    for u_code, u_title, lo_list in full_nos:
        cursor.execute("INSERT INTO units (trade_id, code, title) VALUES (?, ?, ?)", (trade_id, u_code, u_title))
        unit_id = cursor.lastrowid
        
        for lo_num, lo_desc, pc_list in lo_list:
            cursor.execute("INSERT INTO learning_outcomes (unit_id, lo_num, desc) VALUES (?, ?, ?)", (unit_id, lo_num, lo_desc))
            lo_id = cursor.lastrowid
            
            for pc_code, pc_desc in pc_list:
                cursor.execute("INSERT INTO performance_criteria (lo_id, pc_code, desc) VALUES (?, ?, ?)", (lo_id, pc_code, pc_desc))

    conn.commit()
    conn.close()
    print("Successfully populated all 11 Units for ICT Level 3!")

if __name__ == "__main__":
    populate_nsq_data()
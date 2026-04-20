import os
from sqlalchemy import create_engine, text

# --- CONFIGURATION ---
DB_USER = os.getenv("DB_USER", "postgres")
DB_PASS = os.getenv("DB_PASS", "[REDACTED]") # Set this in your environment
DB_HOST = os.getenv("DB_HOST", "db.omsvxmtssqqrznvesdfe.supabase.co")
DB_NAME = os.getenv("DB_NAME", "postgres")
DB_PORT = os.getenv("DB_PORT", "5432")

DATABASE_URL = f"postgresql://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

engine = create_engine(DATABASE_URL)

def seed_nsq_level_2():
    # --- DATA STRUCTURE ---
    full_nos = [
        ["ICT/CMR/001/L2", "Occupational Health and Safety in Workplace Environment", [
            ("LO 1", "Understand Occupational Health and Safety Issues in Computer Operations and Maintenance", [
                ("PC 1.1", "Explain the importance of wearing clean and appropriate PPE."),
                ("PC 1.2", "Know workplace safety compliance with regulations, including the Nigerian Factory Health and Safety Act of 2015."),
                ("PC 1.3", "Demonstrate treatment of cuts, grazes, and wounds."),
                ("PC 1.4", "Explain the process of reporting accidents, illnesses, and infections."),
                ("PC 1.5", "Explain the importance of maintaining good personal hygiene."),
                ("PC 1.6", "Explain the Nigerian Factory Health and Safety Act of 2015 specifically regarding computer operations."),
                ("PC 1.7", "Explain how to follow general hygiene rules."),
                ("PC 1.8", "Identify appropriate PPE for various body parts and regulatory protection.")
            ]),
            ("LO 2", "Observe Safety and Security in the Workplace", [
                ("PC 2.1", "Explain the importance of healthy, safe, and secure workplaces."),
                ("PC 2.2", "Explain how to report accidents or near misses to appropriate personnel."),
                ("PC 2.3", "Carry out pollution control and waste disposal of organic and inorganic wastes.")
            ]),
            ("LO 3", "Understand Hazards Identification and Mitigation Methods in a Workplace Environment", [
                ("PC 3.1", "Identify hazards or potential hazards."),
                ("PC 3.2", "State where to find information about health and workplace hazards."),
                ("PC 3.3", "Describe types of workplace hazards and how to deal with them."),
                ("PC 3.4", "Identify hazards that can be addressed personally."),
                ("PC 3.5", "Identify hazards that should be reported to appropriate personnel."),
                ("PC 3.6", "Identify hazards that should be reported."),
                ("PC 3.7", "Identify risk elements in your own workplace environment."),
                ("PC 3.8", "Describe organizational security procedures and their importance."),
                ("PC 3.9", "Follow procedures for raising awareness of hazards.")
            ]),
            ("LO 4", "Demonstrate Emergency Procedures in a Workplace", [
                ("PC 4.1", "Describe types of emergencies in the workplace."),
                ("PC 4.2", "Explain how to locate first-aid equipment and the registered first-aider."),
                ("PC 4.3", "Describe organizational emergency procedures, particularly for fire."),
                ("PC 4.4", "State possible causes for fire in the workplace."),
                ("PC 4.5", "Describe how to minimize the possibility of fire."),
                ("PC 4.6", "Explain where to find alarms and how to set them off.")
            ])
        ]],
        ["ICT/CMR/002/L2", "Communication", [
            ("LO 1", "Demonstrate how to Communicate Clearly and Concisely", [
                ("PC 1.1", "Describe the principles of effective communications in a technical manner."),
                ("PC 1.2", "Explain how to effectively communicate with clients to understand their needs and provide technical support."),
                ("PC 1.3", "Explain how to clearly and concisely communicate technical information to colleagues, clients, and stakeholders.")
            ]),
            ("LO 2", "Understand the Concept of Effective Listening", [
                ("PC 2.1", "Describe the key elements of effective listening (Attention, Concentration, Comprehension, Retention, and Response)."),
                ("PC 2.2", "Explain the barriers to effective listening (Distractions, Biases, Language, and Emotional barriers)."),
                ("PC 2.3", "Describe the benefits of effective listening, such as improved communication and increased customer satisfaction.")
            ]),
            ("LO 3", "Understand Effective Technical Documentation", [
                ("PC 3.1", "Identify how to document technical papers accurately and clearly."),
                ("PC 3.2", "Inform on the creation of clear and concise user manuals."),
                ("PC 3.3", "Describe how to maintain up-to-date records of system configurations and maintenance activities."),
                ("PC 3.4", "Explain how to create visual aids like diagrams and flowcharts to support documentation."),
                ("PC 3.5", "Describe how to revise and update technical documentation regularly."),
                ("PC 3.6", "Describe how to ensure documentation complies with relevant industry standards."),
                ("PC 3.7", "Describe how to ensure documentation is accessible to all audiences, including individuals with disabilities.")
            ]),
            ("LO 4", "Understand Emergency Procedures in Workplace", [
                ("PC 4.1", "Describe how to communicate effectively with colleagues and customers face-to-face."),
                ("PC 4.2", "Demonstrate effective communication over the phone and via video conferencing."),
                ("PC 4.3", "Explain how to communicate effectively via email and messaging platforms."),
                ("PC 4.4", "Explain how to effectively communicate technical information through presentations and reports."),
                ("PC 4.5", "Describe how to communicate feedback and escalate issues effectively.")
            ]),
            ("LO 5", "Understand the Assessment Criteria for Effective Communication", [
                ("PC 5.1", "Explain how to communicate the accuracy and clarity of technical information."),
                ("PC 5.2", "Describe how to adapt a communication style to suit different audiences and contexts."),
                ("PC 5.3", "Explain the importance of timeliness in responding to messages.")
            ]),
            ("LO 6", "Knowledge and Understanding", [
                ("PC 6.1", "Describe the principles of effective communication."),
                ("PC 6.2", "Explain technical terminology and concepts (e.g., CPU, RAM, Boot Process, Troubleshooting)."),
                ("PC 6.4", "Describe communication protocols and etiquette, such as active listening, respectful tone, and proper formatting."),
                ("PC 6.5", "Explain the importance of effective communication in technical environments.")
            ])
        ]],
        ["ICT/CMR/003/L2", "Teamwork", [
            ("LO 1", "Understand how to work collaboratively with others", [
                ("PC 1.1", "Demonstrate a positive and professional attitude by being respectful, punctual, and reliable."),
                ("PC 1.2", "Explain how to use active listening skills, including maintaining eye contact and asking clarifying questions."),
                ("PC 1.3", "Explain how to provide and receive feedback, including constructive criticism and positive reinforcement."),
                ("PC 1.4", "Explain how to work effectively in a team to achieve common goals."),
                ("PC 1.5", "Describe how to manage conflicts by resolving issues constructively and respectfully.")
            ]),
            ("LO 2", "Understand how to Communicate Effectively with Team members", [
                ("PC 2.1", "Explain key communication skills, including information sharing and providing feedback within a team."),
                ("PC 2.2", "Demonstrate professionalism through a positive attitude, respect, punctuality, and reliability.")
            ]),
            ("LO 3", "Know how to Support Team members", [
                ("PC 3.1", "Describe problem-solving skills, including key inputs and ideas essential for team members."),
                ("PC 3.2", "Explain how to adapt to changing circumstances, such as shifting priorities, deadlines, and team dynamics."),
                ("PC 3.3", "Demonstrate effective teamwork skills, including communication, collaboration, and conflict resolution.")
            ]),
            ("LO 4", "Know how to respond to workplace emergence", [
                ("PC 4.1", "Describe types of emergencies in the workplace."),
                ("PC 4.2", "Explain how to find first-aid equipment and identify the registered first-aider in the workplace."),
                ("PC 4.3", "Describe organizational emergency procedures, especially for fire incidents, and how to follow them correctly."),
                ("PC 4.4", "State possible causes for fire in the workplace."),
                ("PC 4.5", "Describe how to minimize the possibility of fire in the workplace."),
                ("PC 4.6", "Explain where to find alarms and how to set them off.")
            ]),
            ("LO 5", "Know how to Respect and Value Diversity, Equity, and Inclusivity in a Team", [
                ("PC 5.1", "Demonstrate an understanding of diverse cultures, customs, and values, and their applications in the workplace."),
                ("PC 5.2", "Describe how to build and maintain relationships with diverse stakeholders, including colleagues, clients, and community partners."),
                ("PC 5.3", "Explain how to navigate conflicts and difficult conversations in a respectful, empathetic, and inclusive manner."),
                ("PC 5.4", "Describe how to foster a culture of feedback and continuous learning where everyone feels valued, heard, and supported."),
                ("PC 5.5", "Explain how to advocate for diversity, equity, and inclusion in the workplace and the broader community.")
            ]),
            ("LO 6", "Demonstrate how to coordinate team members effectively", [
                ("PC 6.1", "Explain team structures and the roles of each member."),
                ("PC 6.2", "Describe the effective use of communication methods, including verbal, written, and electronic communication."),
                ("PC 6.3", "Explain how conflict resolution and negotiation techniques are applied in a team setting.")
            ]),
            ("LO 7", "Describe the Knowledge and Understanding of Teamwork", [
                ("PC 7.1", "Explain the principles of effective teamwork in a project or organization."),
                ("PC 7.2", "Describe the importance of communication, collaboration, and adaptability in team environments."),
                ("PC 7.3", "Explain strategies for managing conflict and building trust within teams."),
                ("PC 7.4", "Describe the benefits of diversity and inclusivity in team settings.")
            ]),
            ("LO 8", "Describe the Evidence Requirements for Teamwork Engagements", [
                ("PC 8.1", "Describe teamwork in a simulated or real-work environment."),
                ("PC 8.2", "Explain how to obtain written or verbal feedback from team members or supervisors."),
                ("PC 8.3", "Describe how to document team meetings, decisions, and actions."),
                ("PC 8.4", "Explain how to reflect on personal teamwork skills and identify areas for improvement.")
            ])
        ]],
        ["ICT/CMR/004/L2", "Disassemble and Assemble Computers", [
            ("LO 1", "Disassemble and Assemble Personal Computers", [
                ("PC 1.1", "Demonstrate how to boot the computer systems (cold booting)."),
                ("PC 1.2", "Demonstrate how to disconnect external cables, including data and power cables."),
                ("PC 1.3", "Demonstrate how to discharge static electricity using anti-static straps or alternative methods."),
                ("PC 1.4", "Show how to remove the computer cover."),
                ("PC 1.5", "Remove key components including front panel, HDD, SSD, power pack, motherboard, CPU, cooling fan, and RAM."),
                ("PC 1.6", "Connect computer components and replace the computer cover.")
            ]),
            ("LO 2", "Replace Motherboards and Processors", [
                ("PC 2.1", "Remove the old motherboard."),
                ("PC 2.2", "Identify matching characteristics of the new and old motherboards."),
                ("PC 2.3", "Replace the old motherboard with the new one."),
                ("PC 2.4", "Assess the performance of the old processor."),
                ("PC 2.5", "Replace the old processor with the new one.")
            ]),
            ("LO 3", "Replacement of Mass Storage Devices and Random Access Memory", [
                ("PC 3.1", "Identify factors when replacing mass storage and RAM."),
                ("PC 3.2", "Remove mass storage devices from the case."),
                ("PC 3.3", "Replace the integrated drive electronic (IDE) cable."),
                ("PC 3.4", "Install an internal storage device (HDD/SSD)."),
                ("PC 3.5", "Replace the IDE cable (duplicate)."),
                ("PC 3.6", "Install an internal storage device (duplicate).")
            ])
        ]],
        ["ICT/CMR/005/L2", "Faults Trace, Measurement, and Troubleshooting in Computers", [
            ("LO 1", "Demonstrate Knowledge of Measuring Instruments in Computer Hardware Maintenance and Repairs", [
                ("PC 1.1", "Explain technical terms including Voltage, Current, Resistance, Capacitance, Inductance, etc."),
                ("PC 1.2", "Describe measuring instruments such as Analog and Digital Multimeters, Logic probe Testers, etc."),
                ("PC 1.3", "Apply these measuring instruments to trace faults.")
            ]),
            ("LO 2", "Apply Basic Troubleshooting Techniques", [
                ("PC 2.1", "Measure the AC, DC, and Power units of computer hardware."),
                ("PC 2.2", "Test the functionality of all internal and external components and cables."),
                ("PC 2.3", "Identify basic error messages and their meanings."),
                ("PC 2.4", "Identify faulty computer sounds (beep codes) and their meanings."),
                ("PC 2.5", "Search the World Wide Web for problem-solving tips and tutorials.")
            ]),
            ("LO 3", "Perform Testing on Measuring Instruments In Computer Hardware Maintenance and Repairs", [
                ("PC 3.1", "Perform continuity tests on fuses and cables."),
                ("PC 3.2", "Measure voltage across the 20-pin ATX Power Connector and other internal drive connectors."),
                ("PC 3.3", "Follow the specific procedures for testing components as outlined in installation manuals.")
            ])
        ]],
        ["ICT/CMR/006/L2", "General Maintenance and Repairs of Faulty Computers", [
            ("LO 1", "Trace Faults During Computer Hardware Maintenance and Repairs", [
                ("PC 1.1", "Perform the Basic Troubleshooting Procedures."),
                ("PC 1.2", "Use Measuring Instruments to Trace Faults."),
                ("PC 1.3", "Locate Faulty Components by Visual Inspection, Open, or Short Circuit Test."),
                ("PC 1.4", "Use Multimeters to check the Current flow and Voltage on the Motherboard."),
                ("PC 1.5", "Replace Module or Components with other Spares to eliminate Faults.")
            ]),
            ("LO 2", "Clean Computer Systems During Hardware Maintenance and Repairs", [
                ("PC 2.1", "Identify cleaning methods: Blowing, Dusting/Brushing, and Applying solutions."),
                ("PC 2.2", "Disassemble the Computer Systems for Cleaning or washing."),
                ("PC 2.3", "Identify the Basic Tools Required: Non-lint Cloth, Isopropyl alcohol, Portable Vacuum, etc."),
                ("PC 2.4", "Use Isopropyl Alcohol and Brushes to wash Motherboards."),
                ("PC 2.5", "Heat the Motherboard with workplace stations after washing."),
                ("PC 2.6", "Use an air blower to remove Dust and Dirt inside the computers.")
            ]),
            ("LO 3", "Know how to Unplug and Plug Computer Components During Troubleshooting", [
                ("PC 3.1", "Apply “halt on” setting in the CMOS setup Utility."),
                ("PC 3.2", "Perform plugging and unplugging of internal components for error detection (L2 cache, RAM, etc.)."),
                ("PC 3.3", "Carry out a “power-on-self” (POST)” check to locate common faults.")
            ])
        ]],
        ["ICT/CMR/007/L2", "Management of Computer Hardware Maintenance and Repairs", [
            ("LO 1", "Understand the Procedure to Set up a Computer Hardware Maintenance and Repairs Workshop", [
                ("PC 1.1", "Describe appropriate equipment and facilities for setting up a workshop."),
                ("PC 1.2", "Identify appropriate locations for the workshop."),
                ("PC 1.3", "Describe the appropriate size and layout for the workshop."),
                ("PC 1.4", "Maintain a clean, safe, and secure workplace environment.")
            ]),
            ("LO 2", "Apply Managerial and Customer Service Principles to Workshop", [
                ("PC 2.1", "Describe how to attend to customers with faulty computers."),
                ("PC 2.2", "Explain the normal documentation process for collecting/returning computers."),
                ("PC 2.3", "Demonstrate good communication and interpersonal skills."),
                ("PC 2.4", "Keep good records of incomes, expenses, assets, and liabilities."),
                ("PC 2.5", "Estimate the cost of repairs for faulty computers.")
            ]),
            ("LO 3", "Raise Funds or Capital for Workshop", [
                ("PC 3.1", "Propose start-up capital required for the workshop."),
                ("PC 3.2", "Identify various sources of capital to set up the workshop."),
                ("PC 3.3", "Explain the Returns on Investment (RoI) for the workshop."),
                ("PC 3.4", "Maintain good stock control and inventory of spare parts and modules.")
            ])
        ]],
        ["ICT/CMR/008/L2", "Fundamentals of Basic Electronics to Computer Hardware Maintenance and Repairs", [
            ("LO 1", "Understand Applications of Resistors", [
                ("PC 1.1", "Explain the Color Codes of Small Resistors."),
                ("PC 1.2", "Identify resistance using four-band and five-band color code systems."),
                ("PC 1.3", "Connect resistors in Parallel and Series."),
                ("PC 1.4", "Draw Resistors in Serial and Parallel Configurations."),
                ("PC 1.5", "Use an Ohmmeter to determine total Resistance."),
                ("PC 1.6", "Compare Ohmmeter Readings with Calculated Values.")
            ]),
            ("LO 2", "Apply Capacitors in Computers and Electronic Circuits", [
                ("PC 2.1", "Explain the meaning of a Capacitor."),
                ("PC 2.2", "Discuss applications of different types of Capacitors."),
                ("PC 2.3", "Draw the Symbols of Capacitors."),
                ("PC 2.4", "Define Capacitance and its SI Unit."),
                ("PC 2.5", "Connect capacitors in Series and Parallel."),
                ("PC 2.6", "Draw Capacitors in Serial and Parallel Configurations."),
                ("PC 2.7", "Use a multimeter to measure current and voltage across capacitor configurations.")
            ]),
            ("LO 3", "Understand Inductors in Computers and Electronic Circuits", [
                ("PC 3.1", "Describe an inductor and how it works."),
                ("PC 3.2", "Define inductance and its SI Unit."),
                ("PC 3.3", "Discuss applications of inductors in computers."),
                ("PC 3.4", "Connect inductors in Series and Parallel."),
                ("PC 3.5", "Draw inductors in serial and parallel configurations."),
                ("PC 3.6", "Use a Multimeter to measure current and voltage.")
            ]),
            ("LO 4", "Understand the Concept and Applications of Filters", [
                ("PC 4.1", "Explain the meaning of a Filter and its Application."),
                ("PC 4.2", "Use a simple RC circuit to explain a low-pass Filter."),
                ("PC 4.3", "Draw a simple RC Circuit to illustrate a high-pass Filter."),
                ("PC 4.4", "Draw a Band Pass Filter Circuit."),
                ("PC 4.5", "Discuss the Band Stop Filter Circuit and its Applications."),
                ("PC 4.6", "Construct Low Pass, High Pass, Band Pass, and Band Stop filters.")
            ]),
            ("LO 5", "Understand Semiconductors in Computers and Electronic Circuits", [
                ("PC 5.1", "Discuss Semiconductor materials and the effect of Doping."),
                ("PC 5.2", "Explain PN Junction Diode and its Composition."),
                ("PC 5.3", "State the difference between forward biased and reverse biased diodes."),
                ("PC 5.4", "Apply Diodes in Half Wave, Full Wave, and Bridge Rectification."),
                ("PC 5.5", "Identify the uses of Zener Diodes.")
            ]),
            ("LO 6", "Identify Uses of BJTs and FETs", [
                ("PC 6.1", "Explain the Physical Configuration and Types of BJTs."),
                ("PC 6.2", "State basic functions: Switching and Amplification."),
                ("PC 6.3", "Test the functionality of Transistors."),
                ("PC 6.4", "State applications of JFET and MOSFET in computers.")
            ]),
            ("LO 7", "Understand types and Applications of Optoelectronics", [
                ("PC 7.1", "Discuss Light Emitting and Light Detecting categories."),
                ("PC 7.2", "Identify Visible-Light, Blinking, Tricolor, and 7-Segment LEDs."),
                ("PC 7.3", "Identify Light Detecting Devices (Photoresistors, Solar cells, etc.).")
            ]),
            ("LO 8", "Identify Types and uses of Integrated Circuits (ICs)", [
                ("PC 8.1", "Identify Integrated Circuits on Circuit Boards."),
                ("PC 8.2", "State Advantages and Disadvantages of Integrated Circuits."),
                ("PC 8.3", "Identify basic IC Packages: TO-5, Flat Package, and DIL."),
                ("PC 8.4", "Draw the IC Symbols."),
                ("PC 8.5", "State uses of Voltage Regulators, 555 Timers, and Op-Amps."),
                ("PC 8.6", "Construct simple electronic circuits using ICs.")
            ])
        ]],
        ["ICT/CMR/009/L2", "Fundamental Principles of Using Printers, Photocopy Machines, and Scanners", [
            ("LO 1", "Understand the Basic Operation and Maintenance of Printers", [
                ("PC 1.1", "Explain various types of printers (Impact; Non-impact)."),
                ("PC 1.2", "Identify printer components and consumables."),
                ("PC 1.3", "Describe control panel functions."),
                ("PC 1.4", "Identify printer interfaces (Parallel, USB, Serial, Wireless, SCSI)."),
                ("PC 1.5", "Perform Installation and Configuration of Printers."),
                ("PC 1.6", "Perform Print and Cancel operations."),
                ("PC 1.7", "Change Printer Settings to Optimize Performance."),
                ("PC 1.8", "Perform Replacement and Refilling of Cartridge/Toner."),
                ("PC 1.9", "Connect Printers to a Wired or Wireless Network.")
            ]),
            ("LO 2", "Apply Basic Maintenance Procedures to Printers", [
                ("PC 2.1", "Explain Error Codes and messages of Printers."),
                ("PC 2.2", "Use Diagnostic Tools to Eliminate Faults."),
                ("PC 2.3", "Review Service and Installation Manuals."),
                ("PC 2.4", "Isolate the Problems of the Printers."),
                ("PC 2.5", "Replace Parts and Consumables as needed."),
                ("PC 2.6", "Test run the Repaired Printer."),
                ("PC 2.7", "Install missing Printer Drivers."),
                ("PC 2.8", "Fix Printer IP-Address problem.")
            ]),
            ("LO 3", "Understand Basic Operation and Maintenance of Photocopy Machines", [
                ("PC 3.1", "Identify parts of a Photocopy Machine."),
                ("PC 3.2", "Operate Photocopy Machine."),
                ("PC 3.3", "Replace Toner and Other Consumables."),
                ("PC 3.4", "Clear Paper Jam and Other Error Messages.")
            ]),
            ("LO 4", "Understand Basic Operation and Maintenance of Scanners", [
                ("PC 4.1", "Identify parts of a Scanner."),
                ("PC 4.2", "Outline the operation of a Scanner."),
                ("PC 4.3", "Explain Types of Scanners (Handheld, Flatbed, Specialized)."),
                ("PC 4.4", "Connect a Scanner to a Computer."),
                ("PC 4.5", "Perform Installation and Uninstallation of Scanner."),
                ("PC 4.6", "Use Scanner correctly.")
            ])
        ]]
    ]

    with engine.begin() as conn:
        print("--- CLEANING DATABASE ---")
        # Cleans existing data to ensure Level 2 is fresh
        conn.execute(text("TRUNCATE TABLE public.performance_criteria, public.learning_outcomes, public.units, public.trades RESTART IDENTITY CASCADE"))
        
        print("--- INSERTING LEVEL 2 TRADE ---")
        # Note: trade_id will be 1 due to RESTART IDENTITY CASCADE
        conn.execute(text("INSERT INTO public.trades (name) VALUES (:name)"), 
                     {"name": "NSQ Level 2 Computer Hardware Repairs & Maintenance"})
        trade_id = 1
        
        for u_code, u_title, lo_list in full_nos:
            print(f"Loading Unit: {u_code}")
            res = conn.execute(
                text("INSERT INTO public.units (trade_id, code, title) VALUES (:tid, :code, :title) RETURNING id"),
                {"tid": trade_id, "code": u_code, "title": u_title}
            )
            unit_id = res.scalar()
            
            for lo_num, lo_desc, pc_list in lo_list:
                # Using 'description' column as per Supabase standards
                res = conn.execute(
                    text("INSERT INTO public.learning_outcomes (unit_id, lo_num, description) VALUES (:uid, :num, :desc) RETURNING id"),
                    {"uid": unit_id, "num": lo_num, "desc": lo_desc}
                )
                lo_id = res.scalar()
                
                for pc_code, pc_desc in pc_list:
                    conn.execute(
                        text("INSERT INTO public.performance_criteria (lo_id, pc_code, description) VALUES (:lid, :code, :desc)"),
                        {"lid": lo_id, "code": pc_code, "desc": pc_desc}
                    )
        
        print("\nSUCCESS: All 9 Units for NSQ Level 2 have been loaded to Supabase!")

if __name__ == "__main__":
    seed_nsq_level_2()
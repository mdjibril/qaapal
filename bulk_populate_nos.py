import sqlite3

def populate_nsq_networking_data():
    conn = sqlite3.connect('nsq_audit.db')
    cursor = conn.cursor()

    # --- INSERT TRADE ---
    cursor.execute("INSERT INTO trades (id, name) VALUES (4, 'NSQ Level 2 Computer Networking')")
    trade_id = 4
    
    # --- DATA STRUCTURE ---
    full_nos = [
        ["ICT/CNT/001/L2", "Occupational Health and Safety in Networking", [
            ("LO 1", "Identify Workplace Hazards and Apply Safety Measures", [
                ("PC 1.1", "Identify common hazards such as electrical risks, tripping hazards, and ergonomic issues in networking environments."),
                ("PC 1.2", "Explain the importance of risk assessment and how to conduct one before performing networking tasks."),
                ("PC 1.3", "Apply appropriate safety measures, including the use of Personal Protective Equipment (PPE), fire safety procedures, and proper handling of cables and tools.")
            ]),
            ("LO 2", "Follow Safe Handling Procedures for Networking Equipment", [
                ("PC 2.1", "Demonstrate proper techniques for handling and installing networking hardware, including routers, switches, and servers."),
                ("PC 2.2", "Follow manufacturer guidelines and safety protocols when performing maintenance on network devices."),
                ("PC 2.3", "Dispose of electronic waste and damaged networking components following environmental and workplace safety regulations.")
            ]),
            ("LO 3", "Respond to Workplace Emergencies and Incidents", [
                ("PC 3.1", "Identify different types of emergencies, such as electrical fires, equipment malfunctions, and other site hazards."),
                ("PC 3.2", "Follow established workplace emergency response procedures, including fire evacuation plans and first-aid protocols."),
                ("PC 3.3", "Report and document workplace safety incidents accurately and communicate them to the relevant personnel.")
            ])
        ]],
        ["ICT/CNT/002/L2", "Communication for Networking Professionals", [
            ("LO 1", "Demonstrate Effective Communication in Networking Environments", [
                ("PC 1.1", "Use clear and professional language when explaining technical networking concepts to different audiences."),
                ("PC 1.2", "Apply active listening and questioning techniques to understand networking issues and provide appropriate responses."),
                ("PC 1.3", "Communicate technical support and troubleshooting steps effectively to users and colleagues.")
            ]),
            ("LO 2", "Develop and Interpret Technical Documentation", [
                ("PC 2.1", "Read and interpret network diagrams, system logs, and configuration documents accurately."),
                ("PC 2.2", "Create and maintain clear documentation of network configurations, troubleshooting procedures, and incident reports."),
                ("PC 2.3", "Follow industry standards for documenting networking tasks to ensure consistency and clarity.")
            ]),
            ("LO 3", "Utilize Digital Communication Tools for Networking Support", [
                ("PC 3.1", "Use email, chat, and helpdesk ticketing systems to document and track networking issues."),
                ("PC 3.2", "Conduct virtual meetings and remote troubleshooting sessions using appropriate online tools."),
                ("PC 3.3", "Maintain professionalism and clarity when communicating network-related concerns via digital platforms.")
            ])
        ]],
        ["ICT/CNT/003/L2", "Teamwork in Networking", [
            ("LO 1", "Understand the Role of Teamwork in Networking Environments", [
                ("PC 1.1", "Describe the benefits of teamwork in networking projects, including efficiency, problem-solving, and knowledge sharing."),
                ("PC 1.2", "Identify different roles in a networking team (e.g., network administrator, technician, support specialist) and explain their responsibilities."),
                ("PC 1.3", "Demonstrate an understanding of how collaboration improves network maintenance, security, and troubleshooting.")
            ]),
            ("LO 2", "Apply Effective Communication and Collaboration Techniques in Team Settings", [
                ("PC 2.1", "Use clear and concise communication when working with team members to complete networking tasks."),
                ("PC 2.2", "Participate in team discussions and contribute constructive ideas for network-related problem-solving."),
                ("PC 2.3", "Provide and receive feedback professionally to improve collaboration and efficiency in network operations.")
            ]),
            ("LO 3", "Resolve Conflicts and Contribute to Team Success", [
                ("PC 3.1", "Identify common sources of conflict in IT and networking teams and suggest strategies for resolution."),
                ("PC 3.2", "Demonstrate professionalism and respect when addressing disagreements with team members."),
                ("PC 3.3", "Work towards common goals by supporting teammates, sharing responsibilities, and maintaining a positive work environment.")
            ])
        ]],
        ["ICT/CNT/004/L2", "Network Hardware Installation and Configuration", [
            ("LO 1", "Know Network Hardware for Installation", [
                ("PC 1.1", "Identify key networking components."),
                ("PC 1.2", "Verify hardware compatibility with network specifications."),
                ("PC 1.3", "Inspect network hardware for physical damage."),
                ("PC 1.4", "Follow safety precautions before handling network devices.")
            ]),
            ("LO 2", "Install Network Devices and Components", [
                ("PC 2.1", "Mount networking hardware, ensuring proper placement and ventilation."),
                ("PC 2.2", "Establish physical connections using appropriate cables, connectors, and ports."),
                ("PC 2.3", "Label network cables for easy identification."),
                ("PC 2.4", "Test hardware connections.")
            ]),
            ("LO 3", "Configure Network Hardware for Initial Operation", [
                ("PC 3.1", "Navigate the configuration interfaces of routers, switches, and other network devices."),
                ("PC 3.2", "Configure basic settings such as IP addressing, subnet masks, and default gateways."),
                ("PC 3.3", "Set up VLANs, DHCP, and basic security settings where applicable."),
                ("PC 3.4", "Save and back up initial configuration settings for future reference.")
            ]),
            ("LO 4", "Troubleshoot Network Hardware", [
                ("PC 4.1", "Diagnose common hardware failures, including connectivity issues, power failures, and overheating."),
                ("PC 4.2", "Apply basic troubleshooting techniques, such as checking cable integrity, resetting devices, and updating firmware."),
                ("PC 4.3", "Maintain network hardware by cleaning, inspecting, and replacing faulty components as needed."),
                ("PC 4.4", "Document troubleshooting steps and maintenance activities for future reference.")
            ])
        ]],
        ["ICT/CNT/005/L2", "Structured Cabling and Cable Management", [
            ("LO 1", "Select Appropriate Network Cables and Connectors", [
                ("PC 1.1", "Identify various types of network cables, including twisted-pair (Cat5e, Cat6, Cat6a), fiber optic, and coaxial cables."),
                ("PC 1.2", "Explain the characteristics of each cable type in different networking environments."),
                ("PC 1.3", "Select the appropriate cables and connectors based on network requirements."),
                ("PC 1.4", "Identify the correct crimping tools, cable testers, and termination accessories.")
            ]),
            ("LO 2", "Terminate Network Cables", [
                ("PC 2.1", "Prepare cables for termination using proper stripping and crimping techniques."),
                ("PC 2.2", "Terminate copper cables using RJ-45 connectors."),
                ("PC 2.3", "Install fiber optic cables using appropriate splicing and termination techniques."),
                ("PC 2.4", "Test terminated cables for continuity, signal strength, and proper connectivity.")
            ]),
            ("LO 3", "Implement Proper Cable Routing and Labeling Techniques", [
                ("PC 3.1", "Implement structured cable routing to minimize interference."),
                ("PC 3.2", "Secure cables using cable trays, conduits, and ties while following safety and industry guidelines."),
                ("PC 3.3", "Label network cables according to a standardized naming convention."),
                ("PC 3.4", "Maintain documentation of cable layouts, patch panel mappings, and connection points.")
            ])
        ]],
        ["ICT/CNT/006/L2", "Wired and Wireless Network Configuration", [
            ("LO 1", "Configure Wired Network Connections", [
                ("PC 1.1", "Configure network devices such as routers, switches, and hubs for wired networks."),
                ("PC 1.2", "Assign IP addresses (static and dynamic) for wired network devices."),
                ("PC 1.3", "Implement basic VLAN configurations to segment network traffic."),
                ("PC 1.4", "Verify wired network connections using diagnostic tools (e.g., ping, tracer, and cable testers).")
            ]),
            ("LO 2", "Configure Wireless Networks", [
                ("PC 2.1", "Configure wireless routers and access points with appropriate SSID and encryption settings."),
                ("PC 2.2", "Configure wireless security protocols such as WPA2, WPA3, and MAC filtering to enhance security."),
                ("PC 2.3", "Optimize wireless network coverage by adjusting settings."),
                ("PC 2.4", "Monitor wireless network performance using diagnostic tools.")
            ]),
            ("LO 3", "Implement Network Security Measures for Wired and Wireless Networks", [
                ("PC 3.1", "Configure network firewalls."),
                ("PC 3.2", "Enable encryption protocols (e.g., WPA3, TLS) to secure wireless communications."),
                ("PC 3.3", "Implement authentication mechanisms such as RADIUS and 802.1X for secure network access."),
                ("PC 3.4", "Identify common network security threats, including unauthorized access and rogue access points.")
            ]),
            ("LO 4", "Maintain Wired and Wireless Network Performance", [
                ("PC 4.1", "Utilize network monitoring tools (e.g., Wireshark, NetFlow) to analyze traffic and detect anomalies."),
                ("PC 4.2", "Diagnose common wired and wireless network connectivity issues."),
                ("PC 4.3", "Apply firmware and software updates to network devices."),
                ("PC 4.4", "Document network configurations, performance metrics, and troubleshooting steps for future reference.")
            ])
        ]],
        ["ICT/CNT/007/L2", "Network Performance Monitoring and Maintenance", [
            ("LO 1", "Monitor Network Performance Using Diagnostic Tools", [
                ("PC 1.1", "Identify key network performance indicators such as bandwidth utilization, latency, and packet loss."),
                ("PC 1.2", "Utilize network monitoring tools (e.g., Wireshark, PRTG, SolarWinds) to capture and analyze traffic data."),
                ("PC 1.3", "Interpret network performance reports."),
                ("PC 1.4", "Set up notifications for critical network performance thresholds.")
            ]),
            ("LO 2", "Troubleshoot Network Performance Issues", [
                ("PC 2.1", "Identify symptoms of network congestion, bottlenecks, and connectivity issues."),
                ("PC 2.2", "Apply troubleshooting commands (e.g., ping, traceroute, netstat) to diagnose network issues."),
                ("PC 2.3", "Isolate issues related to faulty hardware, misconfigurations, or security breaches.")
            ]),
            ("LO 3", "Implement Preventive Maintenance Strategies for Network Reliability", [
                ("PC 3.1", "Perform regular hardware inspections."),
                ("PC 3.2", "Perform regular firmware updates."),
                ("PC 3.3", "Implement automated backup and recovery solutions for network configurations."),
                ("PC 3.4", "Conduct scheduled system updates and patches.")
            ]),
            ("LO 4", "Optimize Network Performance Through Configuration Adjustments", [
                ("PC 4.1", "Adjust Quality of Service (QoS) settings to prioritize critical network traffic."),
                ("PC 4.2", "Optimize network bandwidth by managing load balancing and traffic shaping techniques."),
                ("PC 4.3", "Configure network devices to minimize latency and improve data transmission speed."),
                ("PC 4.4", "Monitor and adjust network security settings to balance performance and protection.")
            ])
        ]],
        ["ICT/CNT/008/L2", "Basic Network Security Implementation", [
            ("LO 1", "Understand Basic Network Security Concepts", [
                ("PC 1.1", "Define key network security concepts."),
                ("PC 1.2", "Identify common types of network security threats."),
                ("PC 1.3", "Explain the role of encryption, firewalls, and access control."),
                ("PC 1.4", "Recognize common security vulnerabilities in networking protocols (e.g., TCP/IP, HTTP, DNS).")
            ]),
            ("LO 2", "Implement Network Perimeter Security", [
                ("PC 2.1", "Configure firewalls to filter incoming and outgoing network traffic."),
                ("PC 2.2", "Implement intrusion detection and prevention systems (IDPS)."),
                ("PC 2.3", "Configure Virtual Private Networks (VPNs) for secure remote access."),
                ("PC 2.4", "Apply network address translation (NAT) to enhance security.")
            ]),
            ("LO 3", "Configure Network Access Control", [
                ("PC 3.1", "Set up user authentication methods such as usernames/passwords, two-factor authentication, and biometrics."),
                ("PC 3.2", "Apply Role-Based Access Control (RBAC)."),
                ("PC 3.3", "Implement Access Control Lists (ACLs) to restrict network traffic based on IP addresses, subnets, and ports.")
            ]),
            ("LO 4", "Secure Network Communication and Data Transmission", [
                ("PC 4.1", "Implement encryption methods, such as SSL/TLS, to protect sensitive data during transmission."),
                ("PC 4.2", "Configure secure communication protocols such as HTTPS, SSH, and SFTP for secure remote access and file transfer."),
                ("PC 4.3", "Ensure that wireless networks are secured using WPA2/WPA3 encryption standards."),
                ("PC 4.4", "Use Virtual LANs (VLANs) and VPNs to segment network traffic and enhance security.")
            ]),
            ("LO 5", "Monitor and Respond to Security Incidents", [
                ("PC 5.1", "Configure security monitoring tools such as Intrusion Detection Systems (IDS) and event log analyzers."),
                ("PC 5.2", "Recognize security alerts and events, such as unauthorized login attempts or malware activity."),
                ("PC 5.3", "Develop incident response protocols to quickly mitigate security breaches."),
                ("PC 5.4", "Document security incidents and responses for future analysis and improvement.")
            ])
        ]]
    ]

    # --- EXECUTION LOOP ---
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
    print("Successfully populated all 8 Units for NSQ Level 2 Computer Networking!")

if __name__ == "__main__":
    populate_nsq_networking_data()
import sqlite3

def populate_nsq_social_media_data():
    conn = sqlite3.connect('nsq_audit.db')
    cursor = conn.cursor()

    # --- INSERT TRADE ---
    cursor.execute("INSERT INTO trades (id, name) VALUES (3, 'NSQ Level 2 Social Media Contents Creation and Management')")
    trade_id = 3
    
    # --- DATA STRUCTURE ---
    full_nos = [
        ["ICT/SMC/001/L2", "Occupational Health and Safety", [
            ("LO 1", "Know Health and Safety Regulations and Requirements", [
                ("PC 1.1", "Explain what health and safety regulations are and why they are important in the workplace."),
                ("PC 1.2", "Identify the basic health and safety rules that must be followed in different work environments."),
                ("PC 1.3", "Follow health and safety guidelines to prevent accidents, and ensure a safe working environment.")
            ]),
            ("LO 2", "Identify and Mitigate Workplace Hazards", [
                ("PC 2.1", "Recognize common hazards in the workplace, including physical, chemical, and ergonomic risks."),
                ("PC 2.2", "Explain the importance of hazard prevention and safety measures."),
                ("PC 2.3", "Identify how to take appropriate actions to reduce risks and maintain a safe working environment.")
            ]),
            ("LO 3", "Know how to Implement Safe Working Practices and Emergency Procedures", [
                ("PC 3.1", "Describe the importance of following safety guidelines to prevent accidents and injuries."),
                ("PC 3.2", "Describe the correct steps to take in case of emergencies such as fire, medical incidents, or equipment failures."),
                ("PC 3.3", "Demonstrate how to follow workplace safety rules and respond effectively to emergency situations.")
            ])
        ]],
        ["ICT/SMC/002/L2", "Teamwork", [
            ("LO 1", "Know the Principles of Effective Teamwork", [
                ("PC 1.1", "Identify the characteristics of a successful team and the roles each member plays in social media management."),
                ("PC 1.2", "Explain the importance of clear communication, active listening, and mutual respect in a team setting."),
                ("PC 2.3", "Identify how to take appropriate actions to reduce risks and maintain a safe working environment."),
                ("PC 1.3", "Describe different team dynamics, including collaboration, decision-making and accountability in social media management.")
            ]),
            ("LO 2", "Demonstrate Problem-Solving and Conflict Resolution Skills in Team Settings", [
                ("PC 2.1", "Participate in team discussions on how to analyze social media management."),
                ("PC 2.2", "Address conflicts that may arise within the team in a professional manner, using mediation and negotiation techniques to reach a resolution."),
                ("PC 2.3", "Evaluate the effectiveness of team problem-solving strategies and suggest improvements to enhance team performance in future projects.")
            ]),
            ("LO 3", "Exhibit Leadership and Support Team Development", [
                ("PC 3.1", "Organize team tasks and delegate responsibilities according to team members' strengths and skills."),
                ("PC 3.2", "Provide constructive feedback and support to team members, encouraging continuous improvement and skill development."),
                ("PC 3.3", "Foster a positive team environment by promoting inclusivity, recognizing individual contributions and motivating the team to achieve set goals.")
            ])
        ]],
        ["ICT/SMC/003/L2", "Communication", [
            ("LO 1", "Know the Importance of Effective Communication in Workplace", [
                ("PC 1.1", "Explain the impact of clear and concise communication on team performance, project success and client satisfaction."),
                ("PC 1.2", "Identify barriers to effective communication in a technical workplace and strategies to overcome them."),
                ("PC 1.3", "Describe how cultural differences, language and technical jargon can influence communication in a diverse workplace.")
            ]),
            ("LO 2", "Know Effective Verbal and Non-Verbal Communication Skills", [
                ("PC 2.1", "Demonstrate verbally with appropriate tone, clarity and technical language when communicating with different stakeholders."),
                ("PC 2.2", "Demonstrate active listening by accurately interpreting and responding to verbal and non-verbal cues during discussions and meetings."),
                ("PC 2.3", "Apply non-verbal communication techniques, such as body language and eye contact, to enhance message delivery and understanding.")
            ]),
            ("LO 3", "Recognize Digital Tools for Professional Communication", [
                ("PC 3.1", "Use appropriate digital communication tools to exchange information effectively within a network support team."),
                ("PC 3.2", "Compose clear and professional emails, reports and other written correspondences to ensure effective communication with stakeholders."),
                ("PC 3.3", "Ensure confidentiality and security of sensitive information when communicating through digital platforms.")
            ])
        ]],
        ["ICT/SMC/006/L2", "Content Strategy Development", [
            ("LO 1", "Know the importance of a content calendar", [
                ("PC 1.1", "Explain a content calendar."),
                ("PC 1.2", "Identify simple steps to create a content calendar."),
                ("PC 1.3", "Assemble a weekly content calendar using any content type.")
            ]),
            ("LO 2", "Know different types of content", [
                ("PC 2.1", "Explain types of content."),
                ("PC 2.2", "Identify types of content (Education, Entertainment, Promotion, Broadcast)."),
                ("PC 2.3", "Explain the importance of using different types of content.")
            ]),
            ("LO 3", "Know how to create trending and viral content", [
                ("PC 3.1", "Explain what a viral/trending content is."),
                ("PC 3.2", "Demonstrate ways to create trending topics online."),
                ("PC 3.3", "Identify online tools to create trending topics in any niche.")
            ]),
            ("LO 4", "Know how to plan long-term content strategies", [
                ("PC 4.1", "Explain long-term content strategies in social media."),
                ("PC 4.2", "Demonstrate how to plan long-term content strategies."),
                ("PC 4.3", "Discuss the tools used in planning long term content strategies.")
            ])
        ]],
        ["ICT/SMC/006/L1", "Brand Identity and Messaging", [
            ("LO 1", "Know how to create a brand voice and personality", [
                ("PC 1.1", "Explain a brand’s personality."),
                ("PC 1.2", "Develop three short social media captions that reflect a unique brand voice."),
                ("PC 1.3", "Select words for a brand’s voice.")
            ]),
            ("LO 2", "Know the types of visual identity elements", [
                ("PC 2.1", "Explain visual identity elements."),
                ("PC 2.2", "Identify how to use visual identity elements tools (Styles, Fonts, Logos)."),
                ("PC 2.3", "Demonstrate with any visual identity element how to create a post.")
            ]),
            ("LO 3", "Know how to write an engaging post and caption for different platforms", [
                ("PC 3.1", "Identify the elements that makes a post engaging."),
                ("PC 3.2", "Differentiate between a formal and a casual post."),
                ("PC 3.3", "Develop a short post for different social media platforms.")
            ]),
            ("LO 4", "Know how to adapt your writing style to match each platform’s audience", [
                ("PC 4.1", "Identify different writing styles for different platforms."),
                ("PC 4.2", "Demonstrate ways to modify a post from a platform to fit another platform."),
                ("PC 4.3", "Identify ways to keep a brand’s style consistent across platforms.")
            ])
        ]],
        ["ICT/SMC/006/L2", "Analytics and Performance Tracking", [
            ("LO 1", "Know social media analytics", [
                ("PC 1.1", "Explain social media analytic tools."),
                ("PC 1.2", "Identify key features in any of the major social media that help improve post performance."),
                ("PC 1.3", "Demonstrate with a social media analytic tool to check post performance.")
            ]),
            ("LO 2", "Understanding key metrics in social media platforms", [
                ("PC 2.1", "Explain what these key metrics mean (Reach, Impressions, Engagement rate, Click through rate)."),
                ("PC 2.2", "Measure the reach of a social media post."),
                ("PC 2.3", "Compare two posts based on their Click-Through Rates.")
            ]),
            ("LO 3", "Know how to analyze post performance and adjust strategies", [
                ("PC 3.1", "Demonstrate ways to check low performing post."),
                ("PC 3.2", "Identify changes needed to improve a low-performing post."),
                ("PC 3.3", "Identify performance adjustment strategies.")
            ]),
            ("LO 4", "Understand A/B testing for social media content", [
                ("PC 4.1", "Explain A/B testing in social media content."),
                ("PC 4.2", "Measure the performance of two different post formats using A/B testing."),
                ("PC 4.3", "Compare the results of two different post versions to determine which works better.")
            ])
        ]],
        ["ICT/SMC/007/L2", "Social Media Advertising Basics", [
            ("LO 1", "Know different type of social media adverts", [
                ("PC 1.1", "Explain the different types of social media adverts."),
                ("PC 1.2", "Compare image ads and video ads in terms of engagement."),
                ("PC 1.3", "Identify which type of social media adverts is best for increasing online traffic.")
            ]),
            ("LO 2", "Understand the basics of audience targeting", [
                ("PC 2.1", "Demonstrate the process a business uses to select the right audience for adverts."),
                ("PC 2.2", "Compare different audience targeting methods in social media."),
                ("PC 2.3", "Differentiate between broad and specific audience targeting strategies.")
            ]),
            ("LO 3", "Know how to set simple adverts budgets and schedules", [
                ("PC 3.1", "Determine the best way to set a budget for social media advertising."),
                ("PC 3.2", "Explain the effect of scheduling adverts at the right time for performance."),
                ("PC 3.3", "Measure the impact of different budget sizes on advertising success.")
            ]),
            ("LO 4", "Know how to measure adverts performance and make changes", [
                ("PC 4.1", "Evaluate the success of a campaign using advertising metrics."),
                ("PC 4.2", "Differentiate between high-performing and low-performing adverts."),
                ("PC 4.3", "Implement changes to improve adverts performance based on analytics.")
            ])
        ]],
        ["ICT/SMC/006/L2", "Managing Brand Reputation", [
            ("LO 1", "Understand ways to handle negative comments", [
                ("PC 1.1", "Identify negative comments."),
                ("PC 1.2", "Identify effective ways to respond to negative comments."),
                ("PC 1.3", "Explain why staying professional is important when handling negative comments."),
                ("PC 1.4", "Determine the best approaches to manage repeated negative feedback.")
            ]),
            ("LO 2", "Know the strategies used to manage misinformation", [
                ("PC 2.1", "Describe the impact of misinformation on a brand's reputation."),
                ("PC 2.2", "Identify effective ways to stop misinformation from spreading."),
                ("PC 2.3", "Develop a response plan for correcting false information about a brand.")
            ]),
            ("LO 3", "Understand steps to recover from a brand crisis", [
                ("PC 3.1", "Explain brand crisis."),
                ("PC 3.2", "Identify key actions a brand should take during a crisis."),
                ("PC 3.3", "Explain the role of communication in crisis management."),
                ("PC 3.4", "Determine ways to rebuild trust with an audience.")
            ]),
            ("LO 4", "Know different methods on how to create a crisis response plan", [
                ("PC 4.1", "Explain the need for a crisis response plan."),
                ("PC 4.2", "Describe key elements in a crisis response plan."),
                ("PC 4.3", "Identify who should be involved in managing a crisis.")
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
    print("Successfully populated all 8 Units for NSQ Level 2 Social Media Contents Creation and Management!")

if __name__ == "__main__":
    populate_nsq_social_media_data()
What it is: A complete management platform for Internet Service Providers (ISPs), made by Ubiquiti.
                                                                                                                                                                                    
  ---
  Two Main Parts                                                                                                                                                                    
                                                                  
  ┌────────────────────────┬────────────────────────┐
  │    NETWORK MODULE      │      CRM MODULE        │
  ├────────────────────────┼────────────────────────┤
  │ • Routers & antennas   │ • Customer accounts    │
  │ • Tower/site locations │ • Billing & invoices   │
  │ • Device monitoring    │ • Service plans        │
  │ • Traffic stats        │ • Support tickets      │
  │ • Firmware updates     │ • Email notifications  │
  │ • Outage detection     │ • Payment collection   │
  └────────────────────────┴────────────────────────┘

  ---
  What Imperial Networks Uses It For
  ┌────────────────────┬────────────────────────────────────────────────────────┐
  │      Function      │                      What It Does                      │
  ├────────────────────┼────────────────────────────────────────────────────────┤
  │ Client Management  │ Track ~9,871 customers, their info, and service status │
  ├────────────────────┼────────────────────────────────────────────────────────┤
  │ Billing            │ Auto-generate invoices, collect payments               │
  ├────────────────────┼────────────────────────────────────────────────────────┤
  │ Network Monitoring │ See which devices are online, bandwidth usage          │
  ├────────────────────┼────────────────────────────────────────────────────────┤
  │ Support            │ Handle customer tickets                                │
  ├────────────────────┼────────────────────────────────────────────────────────┤
  │ Communication      │ Send emails to clients (3,794 tracked)                 │
  ├────────────────────┼────────────────────────────────────────────────────────┤
  │ Traffic Control    │ Throttle/suspend service for non-payment               │
  └────────────────────┴────────────────────────────────────────────────────────┘
  ---
  Tech Stack (Simple)

  - Runs on: Docker containers (easy to move/backup)
  - Database: PostgreSQL (stores all customer & network data)
  - Plugins: PHP-based add-ons for extra features
  - API: RESTful (can integrate with other systems)

  ---
  Why ISPs Use It

  1. All-in-one - Network + billing in one system
  2. Ubiquiti integration - Works seamlessly with Ubiquiti hardware
  3. Automation - Auto-suspend non-paying customers, auto-invoice
  4. Open plugins - Extend with custom features

  ---
  In short: It's the brain of an ISP - managing both the physical network equipment AND the business side (customers, money, support).
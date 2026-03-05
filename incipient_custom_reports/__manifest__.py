{
    'name': "Incipient Custom Reports",
    'summary': "Custom PDF reports for Order Backlog and Scheduled Shipments tracking.",
    'description': """
    This module provides custom PDF reports for sales and inventory tracking:

    1. Scheduled Shipment Report:
    - Hierarchical view of Sale Order lines and associated split delivery dates.
    - Tracks Ordered, Already Shipped, and Remaining quantities.
    - Prioritizes carrier information from delivery orders.

    2. Order Backlog Report:
    - Customer-wise backlog summary with monthly distribution (Backlog Thru).
    - Calculates backlog value based on pending delivery scheduled dates.
    - Displays Total Price, Total Backlog, and Monthly Backlog buckets.
    """,
    'author': "Incipient Corporation",
    'website': "https://www.incipientcorp.com",
    'category': 'Inventory/Delivery',
    'version': '19.0.1.0.0',
    'license': 'LGPL-3',  
    'depends': ['base', 'stock', 'delivery'],
    'data': [
        'security/ir.model.access.csv',
        'wizard/schedule_shipment_wizard_view.xml',
        'wizard/order_backlog_wizard_view.xml',
        'report/report_actions.xml',
        'report/schedule_shipment_report.xml',
        'report/order_backlog_report.xml',
    ],
    'installable': True,
    'auto_install': False,
    'application': False,
    

}


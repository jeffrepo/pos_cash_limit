# -*- coding: utf-8 -*-
{
    'name': "POS Cash Limit",

    'summary': """ Pos cash limit """,

    'description': """
        Pos cash limit
    """,

    'author': "JS",
    'website': "",

    'category': 'Uncategorized',
    'version': '1.0',

    'depends': ['point_of_sale'],

    'data': [
        'data/paperformat_ticket.xml',
        'views/pos_cash_limit_views.xml',
        'views/pos_session_view.xml',
        'views/pos_config_view.xml',

    ],
    'assets':{
        'point_of_sale.assets': [
            'pos_cash_limit/static/src/js/**/*',
        ],
    },
    'license': 'LGPL-3',
}

# -*- coding: utf-8 -*-
{
    'name': "Dashboard Table",

    'summary': """
        Configurable Dashboard Tables""",

    'description': """
        Configurable Dashboard Table , that's able to create menus, actions and security
    """,

    'author': "Sami Adam",
    'website': "https://www.linkedin.com/in/sami-mohamed-9ab3a598",
    'category': 'Technical Settings',
    'version': '0.1',

    # any module necessary for this one to work correctly
    'depends': ['base'],

    # always loaded
    'application': True,
    'data': [
        # 'security/ir.model.access.csv',
        'views/dashboard_table.xml',
        'views/templates.xml',
    ],
    # only loaded in demonstration mode
    'demo': [
        'demo/demo.xml',
    ],
}
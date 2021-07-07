# -*- coding: utf-8 -*-
from odoo import http

# class DashboardTable(http.Controller):
#     @http.route('/dashboard_table/dashboard_table/', auth='public')
#     def index(self, **kw):
#         return "Hello, world"

#     @http.route('/dashboard_table/dashboard_table/objects/', auth='public')
#     def list(self, **kw):
#         return http.request.render('dashboard_table.listing', {
#             'root': '/dashboard_table/dashboard_table',
#             'objects': http.request.env['dashboard_table.dashboard_table'].search([]),
#         })

#     @http.route('/dashboard_table/dashboard_table/objects/<model("dashboard_table.dashboard_table"):obj>/', auth='public')
#     def object(self, obj, **kw):
#         return http.request.render('dashboard_table.object', {
#             'object': obj
#         })
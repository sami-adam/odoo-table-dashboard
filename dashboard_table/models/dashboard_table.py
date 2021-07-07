# -*- coding: utf-8 -*-
import json
import ast
from odoo import models, fields, api, _
from odoo.exceptions import UserError, ValidationError


class ResDashboardTable(models.Model):
    _name = 'res.dashboard.table'
    _description = 'Dashboard Table'
    _order = 'sequence'

    name = fields.Char('Name')
    module_id = fields.Many2one('ir.module.module', 'Application')
    model_id = fields.Many2one('ir.model', 'Process')
    row_field_id = fields.Many2one('ir.model.fields', 'Row Field')
    row_field_values = fields.Char('Row Field Values')
    column_field_ids = fields.Many2many('ir.model.fields', string='Column Fields')
    domain = fields.Char('Domain', default='[]')
    parent_menu_id = fields.Many2one('ir.ui.menu', string='Parent Menu')
    group_ids = fields.Many2many('res.groups', string='Groups')
    user_ids = fields.Many2many('res.users', string='Users')
    table_data = fields.Char('Table Data', compute='get_table_data')
    sequence = fields.Integer('Sequence', default=10)
    color = fields.Integer('Color')
    menu_id = fields.Many2one('ir.ui.menu', string='Menu')

    def clean(self):
        in_use_menus = self.search([]).mapped('menu_id.id')
        not_used_menus = self.env['ir.ui.menu'].search([('name', '=', 'TDashboard')]).filtered(lambda r: r.action and r.action.res_model == 'res.dashboard.table' and r.id not in in_use_menus)
        not_used_menus.mapped('action') and not_used_menus.mapped('action').unlink()
        not_used_menus and not_used_menus.unlink()

    def validate_data(self):
        for rec in self:
            try:
                domain = rec.domain and ast.literal_eval(rec.domain) or []
                self.env[f'{rec.model_id.model}'].search(domain)
            except Exception as e:
                raise UserError(f'{e}')
        return True

    @api.onchange('model_id')
    def onchange_model_id(self):
        if self.model_id and not self.name:
            self.name = f'{self.model_id.name} Table'

    @api.multi
    def write(self, vals):
        if 'parent_menu_id' in vals:
            menu = self.env['ir.ui.menu'].search([('name', '=', 'TDashboard'), ('parent_id', '=', vals['parent_menu_id'])])
            if menu:
                vals['menu_id'] = menu.id
            else:
                window_action = self.env['ir.actions.act_window'].create({
                    'name': 'TDashboard',
                    'res_model': 'res.dashboard.table',
                    'view_mode': 'kanban',
                    'domain': f"[('parent_menu_id', '=', {vals['parent_menu_id']})]",
                })
                menu = self.env['ir.ui.menu'].create({
                    'name': 'TDashboard',
                    'action': f'ir.actions.act_window,{window_action.id}',
                    'parent_id': vals['parent_menu_id'],
                    'sequence': 0
                })
                vals['menu_id'] = menu.id
        res = super(ResDashboardTable, self).write(vals)
        if 'group_ids' in vals or 'user_ids' in vals:
            self.update_security()
        self.validate_data()
        self.clean()
        return res

    @api.model
    def create(self, vals):
        res = super(ResDashboardTable, self).create(vals)
        res.validate_data()
        if res.group_ids or res.user_ids:
            res.update_security()
        menu = self.env['ir.ui.menu'].search([('name', '=', 'TDashboard'), ('parent_id', '=', res.parent_menu_id.id)])
        if menu:
            res.menu_id = menu.id
        else:
            window_action = self.env['ir.actions.act_window'].create({
                'name': 'TDashboard',
                'res_model': 'res.dashboard.table',
                'view_mode': 'kanban',
                'domain': f"[('parent_menu_id', '=', {res.parent_menu_id.id})]",
            })
            menu = self.env['ir.ui.menu'].create({
                'name': 'TDashboard',
                'action': f'ir.actions.act_window,{window_action.id}',
                'parent_id': res.parent_menu_id.id,
                'sequence': 0
            })
            res.menu_id = menu.id
        res.clean()
        return res


    @api.multi
    def unlink(self):
        self.clean()
        return super(ResDashboardTable, self).unlink()

    def update_security(self):
        for rec in self:
            rule = self.env['ir.rule'].search([('name', '=', 'rule_' + rec.model_id.model.replace('.', '_') + '_tdashboard')])
            if rule:
                rule.write({'groups': [(6, 0,  [group for group in rec.group_ids.ids])]})
                if not rec.user_ids:
                    rule.domain_force = f"[('model_id','=',{rec.model_id.id})]"
                else:
                    rule.domain_force = f"[('user_ids','in',user.id),('model_id','=',{rec.model_id.id})]"
            else:
                self.env['ir.rule'].create({
                    'name': 'rule_' + rec.model_id.model.replace('.', '_') + '_tdashboard',
                    'model_id': self.env['ir.model'].search([('model', '=', rec._name)]).id,
                    'groups': rec.group_ids and [(4, group.id) for group in rec.group_ids],
                    'domain_force': rec.user_ids and f"[('user_ids','in',user.id),('model_id','=',{rec.model_id.id})]" or f"[('model_id','=',{rec.model_id.id})]",
                    'perm_read': True,
                    'perm_write': True
                })

    def get_display_name(self, name):

        return '_' in name.title() and name.title().replace('_', ' ') or name.title()

    def get_table_data(self):
        for rec in self:
            data = {}
            row_data = []
            domain = rec.domain or '[]'
            row_field_name = rec.row_field_id.name
            column_fields = rec.column_field_ids
            model_obj = self.env[f'{rec.model_id.model}']
            where_cond = 'where '
            for domain_item in ast.literal_eval(domain):
                where_cond += f"{domain_item[0]} {domain_item[1]} '{domain_item[2]}' and "
            row_field_input_values = rec.row_field_values and [value.strip() for value in rec.row_field_values.split(',')] or False
            if rec.row_field_id.ttype == 'selection':
                row_field_values = row_field_input_values or [selection[0] for selection in model_obj._fields[f'{row_field_name}'].selection]
            else:
                self.env.cr.execute(f"""select DISTINCT {row_field_name} from {rec.model_id.model.replace('.', '_')} {len(where_cond) > 6 and where_cond[:-5] or ''}""")
                row_field_values = row_field_input_values or [res.get(f'{rec.row_field_id.name}') for res in self.env.cr.dictfetchall()]
            #return 'Test'
            # Getting URL
            data_url = self.env['ir.config_parameter'].get_param('web.base.url')
            for row_value in row_field_values:
                if not row_value:
                    continue
                if rec.row_field_id.ttype == 'many2one':
                    row_value = int(row_value)
                    row_value_rec = self.env[f'{rec.row_field_id.relation}'].browse(row_value)
                    row_value_name = row_value_rec.name or str(row_value_rec.id)
                    row_value_name = row_value_name.replace(' ', '')
                    row_value_name2 = row_value_rec.name or str(row_value_rec.id)
                else:
                    row_value_name = f'{row_value}'
                    row_value_name2 = f'{row_value}'
                window_action = self.env['ir.actions.act_window'].search(
                    [('res_model', '=', rec.model_id.model), ('name', '=', f'{row_value_name}_dashboard_action'),
                     ('domain', '=', f"{[(f'{row_field_name}', '=', row_value)] + ast.literal_eval(domain)}")], limit=1)
                if not window_action:
                    action_domain = [(f'{row_field_name}', '=', row_value)] + ast.literal_eval(domain)
                    window_action = self.env['ir.actions.act_window'].create({'name': f'{row_value_name}_dashboard_action',
                                                                              'res_model': rec.model_id.model,
                                                                              'view_mode': 'tree,form',
                                                                              'domain': str(action_domain)})
                data_url += '/web?#view_type=list&model=%s&action=%s' % (rec.model_id.model, window_action and window_action.id)
                columns_domain = [(f'{row_field_name}', '=', row_value)] + ast.literal_eval(domain)
                columns_recs = self.env[rec.model_id.model].search(columns_domain)
                where_cond = 'where '
                for domain_item in ast.literal_eval(domain):
                    where_cond += f"{domain_item[0]} {domain_item[1]} '{domain_item[2]}' and "
                where_cond += f" {row_field_name} = '{row_value}'"
                data_dict = {
                    'field': self.get_display_name(row_value_name2),
                    'count': '{:,}'.format(self.env[rec.model_id.model].search_count([(f'{row_field_name}', '=', row_value)] + ast.literal_eval(domain))),
                    'data_url': data_url
                }
                columns = []
                for column_field in rec.column_field_ids:
                    if column_field.store:
                        if where_cond.endswith(' and '):
                            where_cond = where_cond[:-5]
                        self.env.cr.execute(f"""select sum({column_field.name}) from {rec.model_id.model.replace('.', '_')} {where_cond}""")
                        amount = self.env.cr.dictfetchall()[0].get('sum', 0)
                        columns.append({
                            'column_field': self.get_display_name(column_field.name),
                            'amount': '{:,}'.format(amount and round(amount, 2) or 0),
                        })
                    else:
                        columns.append({'column_field': self.get_display_name(column_field.name),
                                        'amount': '{:,}'.format(round(sum(columns_recs.mapped(column_field.name))), 2) or 0})
                data_dict.update({'columns': columns})
                row_data.append(data_dict)
            totals_list = [item for dic in [col.get('columns') for col in row_data] for item in dic]
            if rec.column_field_ids:
                totals = ['{:,}'.format(round(sum([float(row_dict.get('amount').replace(',', ''))
                                                   for row_dict in
                                                   filter(lambda r: r.get('column_field') == field_name, totals_list)]), 2))
                          for field_name in ['_' in f_name.title() and f_name.title().replace('_', ' ') or f_name.title() for f_name in rec.column_field_ids.mapped('name')]]
                data.update({'column_totals': totals})
            data.update({'rows': row_data, 'count_total': '{:,}'.format(
                sum([float(st_dict.get('count').replace(',', '')) for st_dict in row_data])), 'field_name': rec.row_field_id.field_description})
            rec.table_data = json.dumps(data)





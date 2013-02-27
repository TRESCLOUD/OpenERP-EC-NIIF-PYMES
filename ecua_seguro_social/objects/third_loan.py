#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011-2012 Christopher Ormaza - Ecuadorenlinea.net 
#    (<http://www.ecuadorenlinea.net>). All Rights Reserved
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

from time import strftime
import time

import netsvc
from osv import osv, fields
import decimal_precision as dp
from tools.translate import _

class account_hr_third_loan(osv.osv):
    
    _name = 'account.hr.third.loan' 
    
    _columns = {
                'name':fields.char('Number', size=64, required=False, readonly=True, states={'draft': [('readonly', False)]}),
                'description':fields.char('Description', size=255, required=True, help="It will be write in description of salary rule", readonly=True, states={'draft': [('readonly', False)]}),
                'start_share': fields.integer('Initial Share', help="It will be the first number of quota calculated, and get sequential of salary rules", readonly=True, states={'draft': [('readonly', False)]}),
                'employee_id':fields.many2one('hr.employee', 'Empleado', required=True, readonly=True, states={'draft': [('readonly', False)]}),
                'partner_id':fields.many2one('res.partner', 'Tercero Beneficiario', required=True, readonly=True, states={'draft': [('readonly', False)]}),
                'rule_ids':fields.one2many('hr.extra.input.output', 'loan_id', 'Egresos Programados', readonly=True, states={'draft': [('readonly', False)]}),
                'create_date': fields.datetime('Date', readonly=True),
                'state':fields.selection([
                    ('draft','Draft'),
                    ('done','Done'),
                     ],    'Estado', select=True, readonly=True),
                'line_ids':fields.one2many('account.hr.third.loan.line', 'loan_id', 'Lines', required=False, readonly=True, states={'draft': [('readonly', False)]}),
                'note': fields.text('Notas', readonly=True, states={'draft': [('readonly', False)]}),
                }
    
    
    _defaults = {  
        'state': 'draft',
        'name': lambda obj, cr, uid, context: obj.pool.get('ir.sequence').get(cr, uid, 'third.loan'),
        'description': _('Prestamo Quirografario'),
        'start_share':1,
        }
    
    def unlink(self, cr, uid, ids, context=None):
        if not context:
            context={}
        for loan in self.browse(cr, uid, ids, context):
            if loan.state == 'done':
                raise osv.except_osv(_('Error !'), _('Solo se puede borrar el registro en estado Borrador'))
        res = super(account_hr_third_loan, self).unlink(cr, uid, ids, context)
        return res 
    
    def action_aprove(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        rule_obj = self.pool.get('hr.extra.input.output')
        cat_id = self.pool.get('hr.salary.rule.category').search(cr, uid, [('code','=','EGRE')])[0] or None
        for loan in self.browse(cr, uid, ids, context):
            if not loan.line_ids:
                raise osv.except_osv(_('Error !'), _(u'Debe tener al menos una línea su prestamo'))
            counter = loan.start_share
            total_lines = len(loan.line_ids) - 1
            total_share = counter + total_lines
            for line in loan.line_ids:
                date_to_pay = None
                if line.date_policy == 'date':
                    date_to_pay = advance.date_to_pay
                    name = date_to_pay
                elif line.date_policy == 'period':
                    date_to_pay = line.period_id.date_stop
                vals_rule = {
                             'employee_id': loan.employee_id.id,
                             'loan_id': loan.id,
                             'date_to_pay': date_to_pay,
                             'name': _('%s - %s de %s') % (loan.description, counter, total_share),
                             'code': 'PRES',
                             'category_id': cat_id,
                             'condition_select': 'none',
                             'amount_select': 'fix',
                             'amount_fix': line.amount,
                             'account_debit':loan.employee_id.account_credit.id,
                             'account_credit':loan.partner_id.property_account_payable.id,
                             'pay_to_other': True,
                             'partner_id': loan.partner_id.id,
                             }
                rule_obj.create(cr, uid, vals_rule, context)
                counter += 1
            self.write(cr, uid, [loan.id], {'state':'done'}, context)
        return True

    def action_cancel(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        rule_obj = self.pool.get('hr.extra.input.output')
        for loan in self.browse(cr, uid, ids, context):
            rules = []
            for rule in loan.rule_ids:
                if rule.paid:
                    raise osv.except_osv(_('Error !'), _('No se puede cancelar, ya se encuentran pagadas las cuotas'))
                rules.append(rule.id)
            rule_obj.unlink(cr, uid, rules, context)
            self.write(cr, uid, [loan.id], {'state':'draft'}, context)
        return True
    
account_hr_third_loan()


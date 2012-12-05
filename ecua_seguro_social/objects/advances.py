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

class account_advances(osv.osv):

    _name = 'account.hr.advances'
    _description = 'Employee Advances'
    _order = "date desc, partner_id desc"

    STATE_VALUE = {'draft':[('readonly', False)]}

    def _get_type(self, cursor, uid, context=None):
        '''
        Metodo que devuelve el tipo de documento
        segun el contexto
        '''
        return context.get('type','out_advance')

    def _get_period(self, cr, uid, context=None):
        '''
        Metodo que devuelve el periodo activo
        del sistema financiero
        '''
        if context is None: context = {}
        if context.get('period_id', False):
            return context.get('period_id')
        periods = self.pool.get('account.period').find(cr, uid)
        return periods and periods[0] or False

    def _get_currency(self, cr, uid, context=None):
        '''
        Devuelve la moneda que usa la compañia en el diario
        a utilizar
        '''
        if context is None:
            context = {}
        journal_pool = self.pool.get('account.journal')
        journal_id = context.get('journal_id', False)
        if journal_id:
            journal = journal_pool.browse(cr, uid, journal_id, context=context)
#            currency_id = journal.company_id.currency_id.id
            if journal.currency:
                return journal.currency.id
        return False

    def unlink(self, cr, uid, ids, context=None):
        '''
        Metodo que implementa el borrado de registros
        '''
        for t in self.read(cr, uid, ids, ['state'], context=context):
            if t['state'] not in ('draft', 'cancel'):
                raise osv.except_osv(
                    _('Invalid action !'),
                    _('Cannot delete Advance(s) which are already opened or paid !'))
        return super(account_advances, self).unlink(cr, uid, ids, context)

    def onchange_employee(self, cr, uid, ids, employee_id, context=None):
        if not context:
            context = {}
        if employee_id:
            employee = self.pool.get('hr.employee').browse(cr, uid, employee_id, context)
            return {'value':{'partner_id': employee.partner_id.id or None}}
        else:
            return {}

    def onchange_payment_policy(self, cr, uid, ids, payment_policy, context=None):
        if not context:
            context = {}
        if payment_policy:
            if payment_policy == 'many_payments':
                return {'value':{'date_to_pay': time.strftime('%Y-%m-%d')}}
        else:
            return {'value':{}}

    def _compute_amount(self, cursor, user_id, ids, name, context, args):
        advances = self.browse(cursor, user_id, ids, context)
        res = {}
        for adv in advances:
            total_advance = 0.0
            if adv.payment_policy == 'one_payment':
                total_advance = adv.amount_to_pay
            else:
                for line in adv.line_ids:
                    total_advance += line.amount
            res[adv.id] = total_advance
        return res

    def dummy(self, cr, uid, ids, context):
        return True

    _columns = {
        'name': fields.char('Concepto',
                            size=255,
                            states=STATE_VALUE, readonly=True),
        'employee_id': fields.many2one('hr.employee', 'Employee',
                                      required=True,
                                      states=STATE_VALUE, readonly=True),
        'partner_id': fields.many2one('res.partner', 'Partner',
                                      required=True,
                                      states=STATE_VALUE, readonly=True),
        'date': fields.date('Fecha',
                            states=STATE_VALUE, readonly=True),
        'journal_id': fields.many2one('account.journal', 'Metodo de Pago',
                                      required=True, readonly=True,
                                      states=STATE_VALUE),
        'account_id': fields.related('journal_id',
                                     'default_debit_account_id',
                                     type='many2one',
                                     relation='account.account',
                                     string='Cuenta de Banco',
                                     readonly=True),
        'line_ids':fields.one2many('account.hr.advances.line',
                                   'advance_id',
                                   'Detalle de Anticipo',
                                   readonly=True, states=STATE_VALUE),
        'rule_ids':fields.one2many('hr.extra.input.output',
                                   'advance_id',
                                   'Detalle de Anticipo',
                                   readonly=True, states=STATE_VALUE),        
        'period_id': fields.many2one('account.period','Periodo',
                                     required=True, readonly=True),
        'move_id':fields.many2one('account.move', 'Asiento Contable'),
        'move_ids': fields.related('move_id','line_id', type='one2many',
                                   relation='account.move.line',
                                   string='Detalle de Asientos',
                                   readonly=True),
        'number': fields.char('Número',
                              size=64, readonly=True),
        'ref': fields.char('Ref', size=255 ,states=STATE_VALUE, readonly=True),
        'note': fields.text('Notas',states=STATE_VALUE, readonly=True),
        'amount': fields.function(_compute_amount, string='Total', method=True,
                               digits_compute=dp.get_precision('Account'),
                               store=True),
        'currency_id':fields.many2one('res.currency', 'Moneda',
                                      readonly=True,
                                      states=STATE_VALUE),
        'payment_policy':fields.selection([
            ('one_payment','One Payment'),
            ('many_payments','Many Payments'),
             ],    'Payment Policy', select=True, states=STATE_VALUE, readonly=True, help="One Payment: Only one discount on the payroll of the selected date, Many Payments: You can create many discount and distribute amount and dates to pay."),     
        'date_policy':fields.selection([
            ('date','By Date'),
            ('period','By Period'),
             ],    'Date Policy', select=False, states=STATE_VALUE, readonly=True),
        'period_to_pay_id': fields.many2one('account.period','Periodo',
                                     required=False, states=STATE_VALUE, readonly=True),
        'date_to_pay': fields.date('Date to Pay'),
        'amount_to_pay': fields.float('Amount to Advance', digits_compute=dp.get_precision('Account'), states=STATE_VALUE, readonly=True),
        'type':fields.selection([
        ('in_advance', 'Anticipo Clientes'),
        ('out_advance', 'Anticipo Proveedores'),
        ],'Tipo', readonly=True, states=STATE_VALUE),
        'state':fields.selection(
            [('draft','Draft'),
             ('posted','Posted'),
             ('cancel','Canceled')
            ], 'State', readonly=True, size=32),
        }

    _defaults = {
        'state': 'draft',
        'date': strftime('%Y-%m-%d'),
        'period_id': _get_period,
        'period_to_pay_id': _get_period,
        'type': _get_type,
        'payment_policy': 'one_payment',
        'date_policy': 'period',
        }

    def copy(self, cr, uid, id, default={}, context=None):
        '''
        Metodo que ejecuta la copia de un registro
        '''
        default.update({
            'state': 'draft',
            'number': False,
            'move_id': False,
            'rule_ids': False,
            'line_cr_ids': False,
            'line_dr_ids': False,
            'reference': False,
        })
        if 'date' not in default:
            default['date'] = time.strftime('%Y-%m-%d')
        return super(account_advances, self).copy(cr, uid, id, default, context)

    def proforma_advance(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        rule_obj = self.pool.get('hr.extra.input.output')
        adv_line_obj = self.pool.get('account.hr.advances.line')
        period_obj = self.pool.get('account.period')
        for advance in self.browse(cr, uid, ids, context):
            period_id = period_obj.search(cr, uid, [('date_start', '<=', advance.date), ('date_stop', '>=', advance.date)])
            if not period_id:
                raise osv.except_osv(_('Configuration Error!'), _("There's not period configured for date: %s.") % (advance.date))
            self.write(cr, uid, [advance.id], {'period_id': period_id[0]}, context)
            if advance.payment_policy == 'one_payment':
                date_to_pay = None
                name = None
                if advance.date_policy == 'date':
                    date_to_pay = advance.date_to_pay
                    name = date_to_pay
                elif advance.date_policy == 'period':
                    date_to_pay = advance.period_to_pay_id.date_stop
                    name = advance.period_to_pay_id.name
                vals_adv_line = {
                                 'name': _('Payment of Advance on %s.') % (name),
                                 'amount': advance.amount_to_pay,
                                 'date_to_pay':date_to_pay,
                                 'account_id':advance.employee_id.account_debit.id,
                                 'period_id':advance.period_id.id,
                                 'type': 'dr',
                                 'advance_id': advance.id,
                                 }
                adv_line_obj.create(cr, uid, vals_adv_line, context)
                cat_id = self.pool.get('hr.salary.rule.category').search(cr, uid, [('code','=','EGRE')])[0] or None
                if not cat_id:
                    raise osv.except_osv(_('Configuration Error!.'), _("There's not a category rule with code EGRE, please check System Configuration .") )
                vals_rule = {
                             'employee_id': advance.employee_id.id,
                             'advance_id': advance.id,
                             'date_to_pay': date_to_pay,
                             'name': _('Payment of Advance %s.') % (advance.date),
                             'code': 'ANTC',
                             'category_id': cat_id,
                             'condition_select': 'none',
                             'amount_select': 'fix',
                             'amount_fix': advance.amount_to_pay,
                             'account_debit':advance.employee_id.account_credit.id,
                             'account_credit':advance.employee_id.account_debit.id,
                             'use_partner_account': True,
                             }
                rule_obj.create(cr, uid, vals_rule, context)
            elif advance.payment_policy == 'many_payments':
                tot_lines = len(advance.line_ids)
                count = 1
                for line in advance.line_ids:
                    date_to_pay = None
                    name = None
                    if line.date_policy == 'date':
                        date_to_pay = line.date_to_pay
                        name = date_to_pay
                    elif line.date_policy == 'period':
                        date_to_pay = line.period_to_pay_id.date_stop
                        name = line.period_to_pay_id.name
                    vals_adv_line = {
                                     'name': _('Payment of Advance on %s.') % (name),
                                     'account_id':advance.employee_id.account_debit.id,
                                     'period_id':advance.period_id.id,
                                     }
                    adv_line_obj.write(cr, uid, [line.id] ,vals_adv_line, context)
                    cat_id = self.pool.get('hr.salary.rule.category').search(cr, uid, [('code','=','EGRE')])[0] or None
                    if not cat_id:
                        raise osv.except_osv(_('Configuration Error!'), _("There's not a category rule with code EGRE, please check System Configuration.") )
                    vals_rule = {
                                 'employee_id': advance.employee_id.id,
                                 'advance_id': advance.id,
                                 'date_to_pay': date_to_pay,
                                 'name': _('Payment of Advance %s of %s.') % (count, tot_lines),
                                 'code': 'ANTC',
                                 'category_id': cat_id,
                                 'condition_select': 'none',
                                 'amount_select': 'fix',
                                 'amount_fix': line.amount,
                                 'account_debit':advance.employee_id.account_credit.id,
                                 'account_credit':advance.employee_id.account_debit.id,
                                 'use_partner_account': True,
                                 }
                    count += 1
                    rule_obj.create(cr, uid, vals_rule, context)
        self.action_move_line_create(cr, uid, ids, context=context)
        return True

    def action_cancel_draft(self, cr, uid, ids, context=None):
        self.write(cr, uid, ids, {'state':'draft'})
        wf_service = netsvc.LocalService("workflow")
        for advance_id in ids:
            wf_service.trg_delete(uid, 'account.hr.advances', advance_id, cr)
            wf_service.trg_create(uid, 'account.hr.advances', advance_id, cr)
        return True    

    def cancel_advance(self, cr, uid, ids, context=None):
        '''
        Metodo de cancelacion de anticipo
        Rompe la conciliacion que existe en las lineas
        del anticipo
        '''
        reconcile_pool = self.pool.get('account.move.reconcile')
        move_pool = self.pool.get('account.move')

        for advance in self.browse(cr, uid, ids, context=context):
            rules = []
            for rule in advance.rule_ids:
                if rule.paid:
                    raise osv.except_osv(_('Configuration Error!'), _("You can't cancel advance, salary rules are paid."))
                rules.append(rule.id)
            self.pool.get('hr.extra.input.output').unlink(cr, uid, rules, context)
            recs = []
            for line in advance.move_ids:
                if line.reconcile_id:
                    recs += [line.reconcile_id.id]
                if line.reconcile_partial_id:
                    recs += [line.reconcile_partial_id.id]

            reconcile_pool.unlink(cr, uid, recs)

            if advance.move_id:
                move_pool.button_cancel(cr, uid, [advance.move_id.id])
                move_pool.unlink(cr, uid, [advance.move_id.id])
            line_ids = []
            if advance.payment_policy == 'one_payment':
                for line in advance.line_ids:
                    line_ids.append(line.id)
            self.pool.get('account.hr.advances.line').unlink(cr, uid, line_ids, context)
        res = {
            'state':'cancel',
            'move_id':False,
        }
        self.write(cr, uid, ids, res)
        return True

    def action_number(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        return True

    def action_move_line_create(self, cr, uid, ids, context=None):
        '''
        Metodo de creacion de asiento contable para registro
        de anticipos de clientes y proveedores
        La primera parte se toma la cuenta contables
        del diario, la contraparte por cada linea se toma
        del detalle del anticipo
        '''
        if context is None:
            context = {}
        move_pool = self.pool.get('account.move')
        move_line_pool = self.pool.get('account.move.line')
        currency_pool = self.pool.get('res.currency')
        seq_obj = self.pool.get('ir.sequence')
        advances = self.browse(cr, uid, ids, context=context)
        for inv in advances:
            if inv.move_id:
                continue
            context_multi_currency = context.copy()
            context_multi_currency.update({'date': inv.date})

            if inv.number:
                name = inv.number
            elif inv.journal_id.sequence_id:
                name = seq_obj.get_id(cr, uid, inv.journal_id.sequence_id.id)
            else:
                raise osv.except_osv(_('Error !'), _('Please define a sequence on the journal !'))
            if not inv.ref:
                ref = name.replace('/','')
            else:
                ref = inv.ref

            move = {
                'name': name,
                'journal_id': inv.journal_id.id,
                'narration': inv.note,
                'date': inv.date,
                'ref': ref,
                'period_id': inv.period_id and inv.period_id.id or False
            }
            move_id = move_pool.create(cr, uid, move)

            #create the first line manually
            company_currency = inv.journal_id.company_id.currency_id.id
            current_currency = inv.currency_id.id
            debit = 0.0
            credit = 0.0
            if inv.type == 'out_advance':
                credit = currency_pool.compute(cr, uid, current_currency, company_currency, inv.amount, context=context_multi_currency)
            else:
                debit = currency_pool.compute(cr, uid, current_currency, company_currency, inv.amount, context=context_multi_currency)
            if debit < 0:
                credit = -debit
                debit = 0.0
            if credit < 0:
                debit = -credit
                credit = 0.0
            sign = debit - credit < 0 and -1 or 1
            #create the first line of the advance
            move_line = {
                'name': inv.name or '/',
                'debit': debit,
                'credit': credit,
                'account_id': inv.account_id.id,
                'move_id': move_id,
                'journal_id': inv.journal_id.id,
                'period_id': inv.period_id.id,
                'partner_id': inv.partner_id.id,
                'currency_id': company_currency <> current_currency and  current_currency or False,
                'amount_currency': company_currency <> current_currency and sign * inv.amount or 0.0,
                'date': inv.date,
            }
            move_line_pool.create(cr, uid, move_line)
            rec_list_ids = []
            line_total = debit - credit
            for line in inv.line_ids:
                #create one move line per advance line where amount is not 0.0
                if not line.amount:
                    continue
                amount = currency_pool.compute(cr, uid, current_currency, company_currency, line.amount, context=context_multi_currency)                
                move_line = {
                    'journal_id': inv.journal_id.id,
                    'period_id': inv.period_id.id,
                    'name': line.name and line.name or '/',
                    'account_id': line.account_id.id,
                    'move_id': move_id,
                    'partner_id': inv.partner_id.id,
                    'currency_id': company_currency <> current_currency and current_currency or False,
                    'quantity': 1,
                    'credit': 0.0,
                    'debit': 0.0,
                    'date': inv.date
                }
                if amount < 0:
                    amount = -amount
                    if line.type == 'dr':
                        line.type = 'cr'
                    else:
                        line.type = 'dr'
                        
                if (line.type=='dr'):
                    line_total += amount
                    move_line['debit'] = amount
                else:
                    line_total -= amount
                    move_line['credit'] = amount
                sign = (move_line['debit'] - move_line['credit']) < 0 and -1 or 1
                move_line['amount_currency'] = company_currency <> current_currency and sign * line.amount or 0.0
                advance_line = move_line_pool.create(cr, uid, move_line)
                if line.move_line_id.id:
                    rec_ids = [advance_line, line.move_line_id.id]
                    rec_list_ids.append(rec_ids)

            self.write(cr, uid, [inv.id], {
                'move_id': move_id,
                'state': 'posted',
                'number': name,
            })
            move_pool.post(cr, uid, [move_id], context={})
        return True

account_advances()


class account_advances_line(osv.osv):

    _name = 'account.hr.advances.line'
    _description = 'Detalle de Anticipos'

    def onchange_account(self, cr, uid, ids, employee_id=None, context=None):
        if not context:
            context = {}
        if employee_id:
            employee = self.pool.get('hr.employee').browse(cr, uid, employee_id, context)
            account_id = employee.account_debit.id
            return {'value': {'account_id': account_id}, 'domain': {'account_id': [('id','=',account_id)]}}
        else:
            return {}

    def _compute_balance(self, cr, uid, ids, name, args, context=None):
        '''
        Metodo que calculo los totales sin y por conciliar de las lineas
        de anticipos en el documento
        '''
        currency_pool = self.pool.get('res.currency')
        rs_data = {}
        for line in self.browse(cr, uid, ids, context=context):
            ctx = context.copy()
            ctx.update({'date': line.advance_id.date})
            res = {}
            company = line.advance_id.journal_id.company_id
            company_currency = company.currency_id.id
            voucher_currency = line.advance_id.currency_id.id
            move_line = line.move_line_id or False

            if not move_line:
                res['amount_original'] = 0.0
                res['amount_unreconciled'] = 0.0

            elif move_line.currency_id:
                res['amount_original'] = currency_pool.compute(
                    cr, uid, move_line.currency_id.id, \
                    voucher_currency, move_line.amount_currency, context=ctx)
            elif move_line and move_line.credit > 0:
                res['amount_original'] = currency_pool.compute(
                    cr, uid, company_currency, voucher_currency,\
                    move_line.credit, context=ctx)
            else:
                res['amount_original'] = currency_pool.compute(
                    cr, uid, company_currency, voucher_currency,\
                    move_line.debit, context=ctx)

            if move_line:
                res['amount_unreconciled'] = currency_pool.compute(
                    cr, uid, move_line.currency_id and move_line.currency_id.id  \
                    or company_currency, voucher_currency, \
                    abs(move_line.amount_residual_currency), context=ctx)
            rs_data[line.id] = res
        return rs_data

    def _get_type(self, cr, uid, context=None):
        '''
        devuelve el tipo de documento segun el contexto
        '''
        if context is None:
            context = {}
        return context.get('type')=='out_advance' and 'dr' or 'cr'

    _columns = {
        'advance_id': fields.many2one('account.hr.advances', 'Advance'),
        'name': fields.char('Descripción', size=64, required=True),
        'date_to_pay': fields.date('Date to Pay'),
        'date_policy':fields.selection([
            ('date','By Date'),
            ('period','By Period'),
             ],    'Date Policy',),
        'period_to_pay_id': fields.many2one('account.period','Period to Pay',),
        'period_id': fields.many2one('account.period','Period',),
        'account_id': fields.many2one('account.account',
                                      'Advance Account',
                                      required=True),
        'partner_id':fields.related('advance_id',
                                    'partner_id',
                                    type='many2one',
                                    relation='res.partner',
                                    string='Partner'),
        'amount':fields.float('Amount',
                              digits_compute=dp.get_precision('Account')),
        'move_line_id': fields.many2one('account.move.line', 'Journal Item'),
        'date_original': fields.related('move_line_id','date',
                                        type='date',
                                        relation='account.move.line',
                                        string='Fecha', readonly=1),
        'date_due': fields.related('move_line_id','date_maturity',
                                   type='date',
                                   relation='account.move.line',
                                   string='Fecha Límite', readonly=1),
        'amount_original': fields.function(_compute_balance,
                                           method=True, multi='dc',
                                           type='float',
                                           string='Monto Inicial',
                                           store=True),
        'amount_unreconciled': fields.function(_compute_balance,
                                               method=True,
                                               multi='dc',
                                               type='float',
                                               string='Saldo Pendiente',
                                               store=True),        
        'type': fields.selection([
        ('dr', 'Débito'),
        ('cr', 'Crédito')
        ],'Tipo', required=True),
        }

    _defaults = {
        'type': _get_type,
        'date_policy':'period',
        'amount': 0.0,
        }
    
account_advances_line()
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
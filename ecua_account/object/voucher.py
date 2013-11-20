
# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Patricio Rangles                                                                           
# Copyright (C) 2013  Trescloud Cia. Ltda.                                 
#                                                                       
#This program is free software: you can redistribute it and/or modify   
#it under the terms of the GNU General Public License as published by   
#the Free Software Foundation, either version 3 of the License, or      
#(at your option) any later version.                                    
#
# This module is GPLv3 or newer and incompatible
# with OpenERP SA "AGPL + Private Use License"!
#                                                                       
#This program is distributed in the hope that it will be useful,        
#but WITHOUT ANY WARRANTY; without even the implied warranty of         
#MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the          
#GNU General Public License for more details.                           
#                                                                       
#You should have received a copy of the GNU General Public License      
#along with this program.  If not, see http://www.gnu.org/licenses.
########################################################################

from osv import fields, osv
from tools.translate import _

class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    _name = 'account.voucher'

    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        """        
        Modify the original function to return only the first 20 lines in debit or credit   
        """
        default = super(account_voucher, self).onchange_partner_id(cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=context)

        message = ""
        
        # check the number of items in each variable
        if 'value' in default: 
            if ('line_cr_ids' in default['value']) and (len(default['value']['line_cr_ids']) > 20):
                default['value']['line_cr_ids'] = default['value']['line_cr_ids'][0:19]
                message = 'There are more than 20 credit lines, select manually the credit lines\n'
                 
            if ('line_dr_ids' in default['value']) and (len(default['value']['line_dr_ids']) > 20):
                default['value']['line_dr_ids'] = default['value']['line_dr_ids'][0:19]
                message = message + 'There are more than 20 debit lines, select manually the debit lines\n'
                    
            if message != "":
                warning = {
                    'title': _('Too many lines !'),
                    'message': _(message)
                }
                default['warning'] = warning
        
        return default


# Works fine in supplier payment
#    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
#        """price
#        Returns a dict that contains new values and context
#
#        @param partner_id: latest value from user input for field partner_id
#        @param args: other arguments
#        @param context: context arguments, like lang, time zone
#
#        @return: Returns a dict which contains new values, and context
#        
#        Modify the original function to no return lines in case this   
#        """
#        if context is None:
#            context = {}
#        if not journal_id:
#            return {}
#        context_multi_currency = context.copy()
#        if date:
#            context_multi_currency.update({'date': date})
#
#        line_pool = self.pool.get('account.voucher.line')
#        line_ids = ids and line_pool.search(cr, uid, [('voucher_id', '=', ids[0])]) or False
#        if line_ids:
#            line_pool.unlink(cr, uid, line_ids)
#
#        currency_pool = self.pool.get('res.currency')
#        move_line_pool = self.pool.get('account.move.line')
#        partner_pool = self.pool.get('res.partner')
#        journal_pool = self.pool.get('account.journal')
#
#        vals = self.onchange_journal(cr, uid, ids, journal_id, [], False, partner_id, context)
#        vals = vals.get('value')
#        currency_id = vals.get('currency_id', currency_id)
#        default = {
#            'value':{'line_ids':[], 'line_dr_ids':[], 'line_cr_ids':[], 'pre_line': False, 'currency_id':currency_id},
#        }
#
#        if not partner_id:
#            return default
#
#        if not partner_id and ids:
#            line_ids = line_pool.search(cr, uid, [('voucher_id', '=', ids[0])])
#            if line_ids:
#                line_pool.unlink(cr, uid, line_ids)
#            return default
#
#        journal = journal_pool.browse(cr, uid, journal_id, context=context)
#        partner = partner_pool.browse(cr, uid, partner_id, context=context)
#        account_id = False
#        if journal.type in ('sale','sale_refund'):
#            account_id = partner.property_account_receivable.id
#        elif journal.type in ('purchase', 'purchase_refund','expense'):
#            account_id = partner.property_account_payable.id
#        else:
#            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id
#
#        default['value']['account_id'] = account_id
#
#        if journal.type not in ('cash', 'bank'):
#            return default
#
#        total_credit = 0.0
#        total_debit = 0.0
#        account_type = 'receivable'
#        if ttype == 'payment':
#            account_type = 'payable'
#            total_debit = price or 0.0
#        else:
#            total_credit = price or 0.0
#            account_type = 'receivable'
#
#        # Now, check the first 20 lines in debit or credit to avoid problems.
#        if not context.get('move_line_ids', False):
#            message = ""
#            # credit lines
#            domain = [('state','=','valid'), 
#                      ('account_id.type', '=', account_type), 
#                      ('reconcile_id', '=', False), 
#                      ('partner_id', '=', partner_id)]
#            
#            credit_ids = move_line_pool.search(cr, uid, domain + [('credit','!=','0.0')], context=context)
#
#            if len(credit_ids) > 20:
#                message = 'There are more than 20 credit lines to pay, select manually the credit lines\n'
#                credit_ids = credit_ids[0:19]
#
#            # debit lines
#            debit_ids = move_line_pool.search(cr, uid, domain + [('debit','!=','0.0')], context=context)
#            
#            if len(debit_ids) > 20:
#                message = message + 'There are more than 20 debit lines, select manually the debit lines\n'
#                debit_ids = debit_ids[0:19]
#
#            if message != "":
#                warning = {
#                    'title': _('Too many lines !'),
#                    'message': _(message)
#                }
#                default['warning'] = warning
#            
#            ids = credit_ids + debit_ids
#            
#        else:
#            ids = context['move_line_ids']
#            
#        ids.reverse()
#        moves = move_line_pool.browse(cr, uid, ids, context=context)
#        move_line_found = False
#        invoice_id = context.get('invoice_id', False)
#        company_currency = journal.company_id.currency_id.id
#        if company_currency != currency_id and ttype == 'payment':
#            total_debit = currency_pool.compute(cr, uid, currency_id, company_currency, total_debit, context=context_multi_currency)
#        elif company_currency != currency_id and ttype == 'receipt':
#            total_credit = currency_pool.compute(cr, uid, currency_id, company_currency, total_credit, context=context_multi_currency)
#
#        for line in moves:
#            if line.reconcile_partial_id and line.amount_residual_currency < 0:
#                # skip line that are totally used within partial reconcile
#                continue
#            if invoice_id:
#                if line.invoice.id == invoice_id:
#                    #if the invoice linked to the voucher line is equal to the invoice_id in context
#                    #then we assign the amount on that line, whatever the other voucher lines
#                    move_line_found = line.id
#                    break
#            elif currency_id == company_currency:
#                #otherwise treatments is the same but with other field names
#                if line.amount_residual == price:
#                    #if the amount residual is equal the amount voucher, we assign it to that voucher
#                    #line, whatever the other voucher lines
#                    move_line_found = line.id
#                    break
#                #otherwise we will split the voucher amount on each line (by most old first)
#                total_credit += line.credit or 0.0
#                total_debit += line.debit or 0.0
#            elif currency_id == line.currency_id.id:
#                if line.amount_residual_currency == price:
#                    move_line_found = line.id
#                    break
#                total_credit += line.credit and line.amount_currency or 0.0
#                total_debit += line.debit and line.amount_currency or 0.0
#        for line in moves:
#            if line.reconcile_partial_id and line.amount_residual_currency < 0:
#                # skip line that are totally used within partial reconcile
#                continue
#            original_amount = line.credit or line.debit or 0.0
#            amount_unreconciled = currency_pool.compute(cr, uid, line.currency_id and line.currency_id.id or company_currency, currency_id, abs(line.amount_residual_currency), context=context_multi_currency)
#            line_currency_id = line.currency_id and line.currency_id.id or company_currency
#            rs = {
#                'name':line.move_id.name,
#                'type': line.credit and 'dr' or 'cr',
#                'move_line_id':line.id,
#                'account_id':line.account_id.id,
#                'amount': (move_line_found == line.id) and min(price, amount_unreconciled) or 0.0,
#                'amount_original': currency_pool.compute(cr, uid, line.currency_id and line.currency_id.id or company_currency, currency_id, line.currency_id and abs(line.amount_currency) or original_amount, context=context_multi_currency),
#                'date_original':line.date,
#                'date_due':line.date_maturity,
#                'amount_unreconciled': amount_unreconciled,
#                'currency_id': line_currency_id,
#            }
#            if not move_line_found:
#                if currency_id == line_currency_id:
#                    if line.credit:
#                        amount = min(amount_unreconciled, abs(total_debit))
#                        rs['amount'] = amount
#                        total_debit -= amount
#                    else:
#                        amount = min(amount_unreconciled, abs(total_credit))
#                        rs['amount'] = amount
#                        total_credit -= amount
#
#            default['value']['line_ids'].append(rs)
#            if rs['type'] == 'cr':
#                default['value']['line_cr_ids'].append(rs)
#            else:
#                default['value']['line_dr_ids'].append(rs)
#
#            if ttype == 'payment' and len(default['value']['line_cr_ids']) > 0:
#                default['value']['pre_line'] = 1
#            elif ttype == 'receipt' and len(default['value']['line_dr_ids']) > 0:
#                default['value']['pre_line'] = 1
#            default['value']['writeoff_amount'] = self._compute_writeoff_amount(cr, uid, default['value']['line_dr_ids'], default['value']['line_cr_ids'], price)
#
#        return default


#    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
#        """
#        Modify the original on change to block the load of more than 20 lines of pay in account.voucher
#        """
#        if context is None:
#            context = {}
#        if not journal_id:
#            return {}
#        context_multi_currency = context.copy()
#        if date:
#            context_multi_currency.update({'date': date})
#
#        line_pool = self.pool.get('account.voucher.line')
#        line_ids = ids and line_pool.search(cr, uid, [('voucher_id', '=', ids[0])]) or False
#        if line_ids:
#            line_pool.unlink(cr, uid, line_ids)
#
#        currency_pool = self.pool.get('res.currency')
#        move_line_pool = self.pool.get('account.move.line')
#        partner_pool = self.pool.get('res.partner')
#        journal_pool = self.pool.get('account.journal')
#
#        vals = self.onchange_journal(cr, uid, ids, journal_id, [], False, partner_id, context)
#        vals = vals.get('value')
#        currency_id = vals.get('currency_id', currency_id)
#        default = {
#            'value':{'line_ids':[], 'line_dr_ids':[], 'line_cr_ids':[], 'pre_line': False, 'currency_id':currency_id},
#        }
#
#        if not partner_id:
#            return default
#
#        if not partner_id and ids:
#            line_ids = line_pool.search(cr, uid, [('voucher_id', '=', ids[0])])
#            if line_ids:
#                line_pool.unlink(cr, uid, line_ids)
#            return default
#
#        journal = journal_pool.browse(cr, uid, journal_id, context=context)
#        partner = partner_pool.browse(cr, uid, partner_id, context=context)
#        account_id = False
#        if journal.type in ('sale','sale_refund'):
#            account_id = partner.property_account_receivable.id
#        elif journal.type in ('purchase', 'purchase_refund','expense'):
#            account_id = partner.property_account_payable.id
#        else:
#            account_id = journal.default_credit_account_id.id or journal.default_debit_account_id.id
#
#        default['value']['account_id'] = account_id
#
#        if journal.type not in ('cash', 'bank'):
#            return default
#
#        total_credit = 0.0
#        total_debit = 0.0
#        account_type = 'receivable'
#        if ttype == 'payment':
#            account_type = 'payable'
#            total_debit = price or 0.0
#        else:
#            total_credit = price or 0.0
#            account_type = 'receivable'
#
#        if not context.get('move_line_ids', False):
#            domain = [('state','=','valid'), ('account_id.type', '=', account_type), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)]
#            ids = move_line_pool.search(cr, uid, domain, context=context)
#        else:
#            ids = context['move_line_ids']
#
#        if len(ids) > 20:
#            warning = {
#                'title': _('Too many lines !'),
#                'message': _('There are more than 20 lines to pay, select manually the lines to pay')
#            }
#            
#            default['warning'] = warning
#        else:
#            default = super(account_voucher, self).onchange_partner_id(cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=context)
#
#        return default

   
account_voucher()
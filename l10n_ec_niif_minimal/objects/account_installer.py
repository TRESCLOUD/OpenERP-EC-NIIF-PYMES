# -*- coding: utf-8 -*-
##############################################################################
#
#    Copyright (C) 2011 Christopher Ormaza, Ecuadorenlinea.net
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU Affero General Public License as
#    published by the Free Software Foundation, either version 3 of the
#    License, or (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
##############################################################################

import time
import datetime
from dateutil.relativedelta import relativedelta
from os.path import join as opj
from operator import itemgetter

from tools.translate import _
from osv import fields, osv
import netsvc
import tools

class wizard_multi_charts_accounts(osv.osv_memory):

    _inherit = 'wizard.multi.charts.accounts'
    
    def execute(self, cr, uid, ids, context=None):
        obj_multi = self.browse(cr, uid, ids[0])
        obj_acc = self.pool.get('account.account')
        obj_acc_tax = self.pool.get('account.tax')
        obj_journal = self.pool.get('account.journal')
        obj_sequence = self.pool.get('ir.sequence')
        obj_acc_template = self.pool.get('account.account.template')
        obj_fiscal_position_template = self.pool.get('account.fiscal.position.template')
        obj_fiscal_position = self.pool.get('account.fiscal.position')
        obj_data = self.pool.get('ir.model.data')
        analytic_journal_obj = self.pool.get('account.analytic.journal')
        obj_tax_code = self.pool.get('account.tax.code')
        # Creating Account
        obj_acc_root = obj_multi.chart_template_id.account_root_id
        tax_code_root_id = obj_multi.chart_template_id.tax_code_root_id.id
        company_id = obj_multi.company_id.id

        #new code
        acc_template_ref = {}
        tax_template_ref = {}
        tax_code_template_ref = {}
        todo_dict = {}

        #create all the tax code
        children_tax_code_template = self.pool.get('account.tax.code.template').search(cr, uid, [('parent_id','child_of',[tax_code_root_id])], order='id')
        children_tax_code_template.sort()
        for tax_code_template in self.pool.get('account.tax.code.template').browse(cr, uid, children_tax_code_template, context=context):
            vals={
                'name': (tax_code_root_id == tax_code_template.id) and obj_multi.company_id.name or tax_code_template.name,
                'code': tax_code_template.code,
                'info': tax_code_template.info,
                'parent_id': tax_code_template.parent_id and ((tax_code_template.parent_id.id in tax_code_template_ref) and tax_code_template_ref[tax_code_template.parent_id.id]) or False,
                'company_id': company_id,
                'sign': tax_code_template.sign,
            }
            new_tax_code = obj_tax_code.create(cr, uid, vals)
            #recording the new tax code to do the mapping
            tax_code_template_ref[tax_code_template.id] = new_tax_code

        #create all the tax
        tax_template_to_tax = {}
        for tax in obj_multi.chart_template_id.tax_template_ids:
            #create it
            vals_tax = {
                'name':tax.name,
                'sequence': tax.sequence,
                'amount':tax.amount,
                'type':tax.type,
                'applicable_type': tax.applicable_type,
                'domain':tax.domain,
                'parent_id': tax.parent_id and ((tax.parent_id.id in tax_template_ref) and tax_template_ref[tax.parent_id.id]) or False,
                'child_depend': tax.child_depend,
                'python_compute': tax.python_compute,
                'python_compute_inv': tax.python_compute_inv,
                'python_applicable': tax.python_applicable,
                'base_code_id': tax.base_code_id and ((tax.base_code_id.id in tax_code_template_ref) and tax_code_template_ref[tax.base_code_id.id]) or False,
                'tax_code_id': tax.tax_code_id and ((tax.tax_code_id.id in tax_code_template_ref) and tax_code_template_ref[tax.tax_code_id.id]) or False,
                'base_sign': tax.base_sign,
                'tax_sign': tax.tax_sign,
                'ref_base_code_id': tax.ref_base_code_id and ((tax.ref_base_code_id.id in tax_code_template_ref) and tax_code_template_ref[tax.ref_base_code_id.id]) or False,
                'ref_tax_code_id': tax.ref_tax_code_id and ((tax.ref_tax_code_id.id in tax_code_template_ref) and tax_code_template_ref[tax.ref_tax_code_id.id]) or False,
                'ref_base_sign': tax.ref_base_sign,
                'ref_tax_sign': tax.ref_tax_sign,
                'include_base_amount': tax.include_base_amount,
                'description':tax.description,
                'company_id': company_id,
                'type_tax_use': tax.type_tax_use,
                'price_include': tax.price_include,
                'type_ec': tax.type_ec or False,
                'assets': tax.assets,
                'imports': tax.imports,
                'exports': tax.exports,
            }
            new_tax = obj_acc_tax.create(cr, uid, vals_tax)
            tax_template_to_tax[tax.id] = new_tax
            #as the accounts have not been created yet, we have to wait before filling these fields
            todo_dict[new_tax] = {
                'account_collected_id': tax.account_collected_id and tax.account_collected_id.id or False,
                'account_paid_id': tax.account_paid_id and tax.account_paid_id.id or False,
            }
            tax_template_ref[tax.id] = new_tax

        #deactivate the parent_store functionnality on account_account for rapidity purpose
        ctx = context and context.copy() or {}
        ctx['defer_parent_store_computation'] = True

        children_acc_template = obj_acc_template.search(cr, uid, [('parent_id','child_of',[obj_acc_root.id]),('nocreate','!=',True)])
        children_acc_template.sort()
        for account_template in obj_acc_template.browse(cr, uid, children_acc_template,context=context):
            tax_ids = []
            for tax in account_template.tax_ids:
                tax_ids.append(tax_template_ref[tax.id])
            #create the account_account

            dig = obj_multi.code_digits
            code_main = account_template.code and len(account_template.code) or 0
            code_acc = account_template.code or ''
            if code_main>0 and code_main<=dig and account_template.type != 'view':
                code_acc=str(code_acc) + (str('0'*(dig-code_main)))
            vals={
                'name': (obj_acc_root.id == account_template.id) and obj_multi.company_id.name or account_template.name,
                'currency_id': account_template.currency_id and account_template.currency_id.id or False,
                'code': code_acc,
                'type': account_template.type,
                'user_type': account_template.user_type and account_template.user_type.id or False,
                'reconcile': account_template.reconcile,
                'shortcut': account_template.shortcut,
                'note': account_template.note,
                'parent_id': account_template.parent_id and ((account_template.parent_id.id in acc_template_ref) and acc_template_ref[account_template.parent_id.id]) or False,
                'tax_ids': [(6,0,tax_ids)],
                'company_id': company_id,
            }
            new_account = obj_acc.create(cr, uid, vals, context=ctx)
            acc_template_ref[account_template.id] = new_account
        #reactivate the parent_store functionnality on account_account
        self.pool.get('account.account')._parent_store_compute(cr)

        for key,value in todo_dict.items():
            if value['account_collected_id'] or value['account_paid_id']:
                obj_acc_tax.write(cr, uid, [key], {
                    'account_collected_id': acc_template_ref.get(value['account_collected_id'], False),
                    'account_paid_id': acc_template_ref.get(value['account_paid_id'], False),
                })

        # Creating Journals Sales and Purchase
        vals_journal={}
        data_id = obj_data.search(cr, uid, [('model','=','account.journal.view'), ('name','=','account_sp_journal_view')])
        data = obj_data.browse(cr, uid, data_id[0], context=context)
        view_id = data.res_id

        seq_id = obj_sequence.search(cr, uid, [('name','=','Account Journal')])[0]

        if obj_multi.seq_journal:
            seq_id_sale = obj_sequence.search(cr, uid, [('name','=','Sale Journal')])[0]
            seq_id_purchase = obj_sequence.search(cr, uid, [('name','=','Purchase Journal')])[0]
            seq_id_sale_refund = obj_sequence.search(cr, uid, [('name','=','Sales Refund Journal')])
            if seq_id_sale_refund:
                seq_id_sale_refund = seq_id_sale_refund[0]
            seq_id_purchase_refund = obj_sequence.search(cr, uid, [('name','=','Purchase Refund Journal')])
            if seq_id_purchase_refund:
                seq_id_purchase_refund = seq_id_purchase_refund[0]
        else:
            seq_id_sale = seq_id
            seq_id_purchase = seq_id
            seq_id_sale_refund = seq_id
            seq_id_purchase_refund = seq_id

        vals_journal['view_id'] = view_id

        #Sales Journal
        analitical_sale_ids = analytic_journal_obj.search(cr,uid,[('type','=','sale')])
        analitical_journal_sale = analitical_sale_ids and analitical_sale_ids[0] or False

        vals_journal['name'] = _('Sales Journal')
        vals_journal['type'] = 'sale'
        vals_journal['code'] = _('SAJ')
        vals_journal['sequence_id'] = seq_id_sale
        vals_journal['company_id'] =  company_id
        vals_journal['analytic_journal_id'] = analitical_journal_sale

        if obj_multi.chart_template_id.property_account_receivable:
            vals_journal['default_credit_account_id'] = acc_template_ref[obj_multi.chart_template_id.property_account_income_categ.id]
            vals_journal['default_debit_account_id'] = acc_template_ref[obj_multi.chart_template_id.property_account_income_categ.id]

        obj_journal.create(cr,uid,vals_journal)

        # Purchase Journal
        analitical_purchase_ids = analytic_journal_obj.search(cr,uid,[('type','=','purchase')])
        analitical_journal_purchase = analitical_purchase_ids and analitical_purchase_ids[0] or False

        vals_journal['name'] = _('Purchase Journal')
        vals_journal['type'] = 'purchase'
        vals_journal['code'] = _('EXJ')
        vals_journal['sequence_id'] = seq_id_purchase
        vals_journal['view_id'] = view_id
        vals_journal['company_id'] =  company_id
        vals_journal['analytic_journal_id'] = analitical_journal_purchase

        if obj_multi.chart_template_id.property_account_payable:
            vals_journal['default_credit_account_id'] = acc_template_ref[obj_multi.chart_template_id.property_account_expense_categ.id]
            vals_journal['default_debit_account_id'] = acc_template_ref[obj_multi.chart_template_id.property_account_expense_categ.id]

        obj_journal.create(cr,uid,vals_journal)

        # Creating Journals Sales Refund and Purchase Refund
        vals_journal = {}
        data_id = obj_data.search(cr, uid, [('model', '=', 'account.journal.view'), ('name', '=', 'account_sp_refund_journal_view')], context=context)
        data = obj_data.browse(cr, uid, data_id[0], context=context)
        view_id = data.res_id

        #Sales Refund Journal
        vals_journal = {
            'view_id': view_id,
            'name': _('Sales Refund Journal'),
            'type': 'sale_refund',
            'refund_journal': True,
            'code': _('SCNJ'),
            'sequence_id': seq_id_sale_refund,
            'analytic_journal_id': analitical_journal_sale,
            'company_id': company_id
        }

        if obj_multi.chart_template_id.property_account_receivable:
            vals_journal['default_credit_account_id'] = acc_template_ref[obj_multi.chart_template_id.property_account_income_categ.id]
            vals_journal['default_debit_account_id'] = acc_template_ref[obj_multi.chart_template_id.property_account_income_categ.id]


#        if obj_multi.property_account_receivable:
#            vals_journal.update({
#                'default_credit_account_id': acc_template_ref[obj_multi.chart_template_id.property_account_income_categ.id],
#                'default_debit_account_id': acc_template_ref[obj_multi.chart_template_id.property_account_income_categ.id]
#            })
        obj_journal.create(cr, uid, vals_journal, context=context)

        # Purchase Refund Journal
        vals_journal = {
            'view_id': view_id,
            'name': _('Purchase Refund Journal'),
            'type': 'purchase_refund',
            'refund_journal': True,
            'code': _('ECNJ'),
            'sequence_id': seq_id_purchase_refund,
            'analytic_journal_id': analitical_journal_purchase,
            'company_id': company_id
        }

        if obj_multi.chart_template_id.property_account_payable:
            vals_journal['default_credit_account_id'] = acc_template_ref[obj_multi.chart_template_id.property_account_expense_categ.id]
            vals_journal['default_debit_account_id'] = acc_template_ref[obj_multi.chart_template_id.property_account_expense_categ.id]


#        if obj_multi.property_account_payable:
#            vals_journal.update({
#                'default_credit_account_id': acc_template_ref[obj_multi.property_account_expense_categ.id],
#                'default_debit_account_id': acc_template_ref[obj_multi.property_account_expense_categ.id]
#            })
        obj_journal.create(cr, uid, vals_journal, context=context)

        # Bank Journals
        data_id = obj_data.search(cr, uid, [('model','=','account.journal.view'), ('name','=','account_journal_bank_view')])
        data = obj_data.browse(cr, uid, data_id[0], context=context)
        view_id_cash = data.res_id

        data_id = obj_data.search(cr, uid, [('model','=','account.journal.view'), ('name','=','account_journal_bank_view_multi')])
        data = obj_data.browse(cr, uid, data_id[0], context=context)
        view_id_cur = data.res_id
        ref_acc_bank = obj_multi.chart_template_id.bank_account_view_id

        current_num = 1
        for line in obj_multi.bank_accounts_id:
            #create the account_account for this bank journal
            tmp = line.acc_name
            dig = obj_multi.code_digits
            if ref_acc_bank.code:
                try:
                    new_code = str(int(ref_acc_bank.code.ljust(dig,'0')) + current_num)
                except:
                    new_code = str(ref_acc_bank.code.ljust(dig-len(str(current_num)),'0')) + str(current_num)
            vals = {
                'name': tmp,
                'currency_id': line.currency_id and line.currency_id.id or False,
                'code': new_code,
                'type': 'liquidity',
                'user_type': account_template.user_type and account_template.user_type.id or False,
                'reconcile': True,
                'parent_id': acc_template_ref[ref_acc_bank.id] or False,
                'company_id': company_id,
            }
            acc_cash_id  = obj_acc.create(cr,uid,vals)

            if obj_multi.seq_journal:
                vals_seq={
                    'name': _('Bank Journal ') + vals['name'],
                    'code': 'account.journal',
                }
                seq_id = obj_sequence.create(cr,uid,vals_seq)

            #create the bank journal
            analitical_bank_ids = analytic_journal_obj.search(cr,uid,[('type','=','situation')])
            analitical_journal_bank = analitical_bank_ids and analitical_bank_ids[0] or False

            vals_journal = {}
            vals_journal['name']= vals['name']
            vals_journal['code']= _('BNK') + str(current_num)
            vals_journal['sequence_id'] = seq_id
            vals_journal['type'] = line.account_type == 'cash' and 'cash' or 'bank'
            vals_journal['company_id'] =  company_id
            vals_journal['analytic_journal_id'] = analitical_journal_bank

            if line.currency_id:
                vals_journal['view_id'] = view_id_cur
                vals_journal['currency'] = line.currency_id.id
            else:
                vals_journal['view_id'] = view_id_cash
            vals_journal['default_credit_account_id'] = acc_cash_id
            vals_journal['default_debit_account_id'] = acc_cash_id
            obj_journal.create(cr, uid, vals_journal)
            current_num += 1

        #create the properties
        property_obj = self.pool.get('ir.property')
        fields_obj = self.pool.get('ir.model.fields')

        todo_list = [
            ('property_account_receivable','res.partner','account.account'),
            ('property_account_payable','res.partner','account.account'),
            ('property_account_expense_categ','product.category','account.account'),
            ('property_account_income_categ','product.category','account.account'),
            ('property_account_expense','product.template','account.account'),
            ('property_account_income','product.template','account.account'),
            ('property_reserve_and_surplus_account','res.company','account.account')
        ]
        for record in todo_list:
            r = []
            r = property_obj.search(cr, uid, [('name','=', record[0] ),('company_id','=',company_id)])
            account = getattr(obj_multi.chart_template_id, record[0])
            field = fields_obj.search(cr, uid, [('name','=',record[0]),('model','=',record[1]),('relation','=',record[2])])
            vals = {
                'name': record[0],
                'company_id': company_id,
                'fields_id': field[0],
                'value': account and 'account.account,'+str(acc_template_ref[account.id]) or False,
            }

            if r:
                #the property exist: modify it
                property_obj.write(cr, uid, r, vals)
            else:
                #create the property
                property_obj.create(cr, uid, vals)

        fp_ids = obj_fiscal_position_template.search(cr, uid, [('chart_template_id', '=', obj_multi.chart_template_id.id)])

        if fp_ids:

            obj_tax_fp = self.pool.get('account.fiscal.position.tax')
            obj_ac_fp = self.pool.get('account.fiscal.position.account')

            for position in obj_fiscal_position_template.browse(cr, uid, fp_ids, context=context):

                vals_fp = {
                    'company_id': company_id,
                    'name': position.name,
                }
                new_fp = obj_fiscal_position.create(cr, uid, vals_fp)

                for tax in position.tax_ids:
                    vals_tax = {
                        'tax_src_id': tax_template_ref[tax.tax_src_id.id],
                        'tax_dest_id': tax.tax_dest_id and tax_template_ref[tax.tax_dest_id.id] or False,
                        'position_id': new_fp,
                    }
                    obj_tax_fp.create(cr, uid, vals_tax)

                for acc in position.account_ids:
                    vals_acc = {
                        'account_src_id': acc_template_ref[acc.account_src_id.id],
                        'account_dest_id': acc_template_ref[acc.account_dest_id.id],
                        'position_id': new_fp,
                    }
                    obj_ac_fp.create(cr, uid, vals_acc)

        ir_values = self.pool.get('ir.values')
        if obj_multi.sale_tax:
            ir_values.set(cr, uid, key='default', key2=False, name="taxes_id", company=obj_multi.company_id.id,
                            models =[('product.product',False)], value=[tax_template_to_tax[obj_multi.sale_tax.id]])
        if obj_multi.purchase_tax:
            ir_values.set(cr, uid, key='default', key2=False, name="supplier_taxes_id", company=obj_multi.company_id.id,
                            models =[('product.product',False)], value=[tax_template_to_tax[obj_multi.purchase_tax.id]])

 
wizard_multi_charts_accounts()
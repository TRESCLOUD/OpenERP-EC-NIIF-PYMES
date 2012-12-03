# -*- coding: UTF-8 -*- #
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2011-2012 Christopher Ormaza (http://www.ecuadorenlinea.net>). 
#    All Rights Reserved
#    
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
import decimal_precision as dp
import time
import netsvc
from datetime import date, datetime, timedelta
import psycopg2
import re
from lxml import etree

from osv import fields, osv
from tools import config
from tools.translate import _ 

class account_invoice(osv.osv):
    
    def _check_number_credit_note(self,cr,uid,ids):
        cadena='(\d{3})+\-(\d{3})+\-(\d{9})'
        for invoice in self.browse(cr, uid, ids):
            if invoice['number_credit_note_out']:
                if re.match(cadena, invoice['number_credit_note_out']):
                    return True
                else:
                    return False
            if invoice['number_credit_note_in']:
                if re.match(cadena, invoice['number_credit_note_in']):
                    return True
                else:
                    return False
        return True
            
    _constraints = [(_check_number_credit_note,'The number of Credit Note is incorrect, it must be like 001-00X-000XXXXXX, X is a number',['number_credit_note_in', 'number_credit_note_out'])]

    _sql_constraints = [('number_credit_note_uniq','unique(number_credit_note_out)', _("There's another credit note with this number!"))]

    def copy(self, cr, uid, id, default={}, context=None):
        inv_obj = self.pool.get('account.invoice')
        doc_obj=self.pool.get('sri.type.document')
        original_credit_note = inv_obj.browse(cr, uid, id, context)
        new_number = False
        autorization_number = False
        authorization_id = False
        if original_credit_note:
            if original_credit_note.shop_id:
                if original_credit_note.printer_id:
                    if original_credit_note.company_id:
                        if original_credit_note.type == "out_refund":
                            new_number = doc_obj.get_next_value_secuence(cr, uid, 'credit_note', False, original_credit_note.company_id.id, original_credit_note.shop_id.id, original_credit_note.printer_id.id, 'account.invoice', 'number_credit_note_out', context)
                            authorization_id = original_credit_note.autorization_credit_note_id.id
                            autorization_number = original_credit_note.autorization_credit_note_id.number
        if context is None:
            context = {}
        default.update({
            'authorization_credit_note_purchase': False,
            'authorization_credit_note_id': authorization_id,
            'authorization': autorization_number,
            'number_credit_note_in':False,
            'number_credit_note_out':new_number,
            'credit_note_ids':[],
            'invoice_rectification_id':False,
        })
        return super(account_invoice, self).copy(cr, uid, id, default, context)
    
    def onchange_invoice_rectification(self, cr, uid, ids, invoice_rectification_id, context=None):
        inv_obj = self.pool.get('account.invoice')
        
        values = {}
        inv_browse = inv_obj.browse(cr, uid, invoice_rectification_id, context)
        if inv_browse:
            values['partner_id'] = inv_browse.partner_id.id
            values['address_invoice_id'] = inv_browse.address_invoice_id.id
            values['account_id'] = inv_browse.account_id.id
        return {'value':values}
    
    def _credit_note_cleanup_lines(self, cr, uid, lines):
        for line in lines:
            del line['id']
            del line['invoice_id']
            for field in ('company_id', 'partner_id', 'account_id', 'product_id',
                          'uos_id', 'account_analytic_id', 'tax_code_id', 'base_code_id'):
                line[field] = line.get(field, False) and line[field][0]
            if 'invoice_line_tax_id' in line:
                line['invoice_line_tax_id'] = [(6,0, line.get('invoice_line_tax_id', [])) ]
        return map(lambda x: (0,0,x), lines)
    
    def get_invoice_rectification_lines(self, cr, uid, ids, context):
        inv_obj = self.pool.get('account.invoice')
        inv_tax_obj = self.pool.get('account.invoice.tax')
        inv_line_obj = self.pool.get('account.invoice.line')      
        for inv in inv_obj.browse(cr, uid, ids, context):
            values = {}
            if not inv.invoice_rectification_id:
                raise osv.except_osv(_('Invalid action!'), _('Do not exist authorization for this number of secuence, please check!'))
            invoice = inv_obj.read(cr, uid, [inv.invoice_rectification_id.id],
                                        ['invoice_line', 'tax_line'], context=context)
            invoice = invoice[0]
            invoice_lines = inv_line_obj.read(cr, uid, invoice['invoice_line'], context=context)
            invoice_lines = self._credit_note_cleanup_lines(cr, uid, invoice_lines)
            tax_lines = inv_tax_obj.read(cr, uid, invoice['tax_line'], context=context)
            tax_lines = self._credit_note_cleanup_lines(cr, uid, tax_lines)
            values['invoice_line'] =  invoice_lines
            values['tax_line'] = tax_lines
            self.write(cr, uid, [inv.id], values, context)
            inv_obj.button_reset_taxes(cr, uid, [inv.id,], context)
        return True

    def onchange_number_credit_note(self, cr, uid, ids, number, automatic=False, company_id=None, shop_id=None, printer_id=None, context=None):
        result = {}
        if context is None:
            context = {}
        if shop_id==None:
            shop_id = self.pool.get('sale.shop_id').search(cr, uid,[])[0]
        if not number:
            return {'value': {}}
        else:
            auth = self.pool.get('sri.authorization').get_auth(cr, uid, 'credit_note', company_id, shop_id, number, printer_id, context)
        if not auth['authorization']:
            raise osv.except_osv(_('Invalid action!'), _('Do not exist authorization for this number of secuence, please check!'))
        result['autorization_credit_note_id'] = auth['authorization']
        res_final = {'value':result}
        return res_final

    def onchange_data_credit_note(self, cr, uid, ids, automatic, company_id=None, shop_id=None, type=None, liquidation=False, printer_id=None, date=None, context=None):
        printer_obj = self.pool.get('sri.printer.point')
        doc_obj=self.pool.get('sri.type.document')
        values = {}
        if context is None:
            context = {}
        if not company_id:
            company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=context)
        manual = context.get('manual',False)
        shop_ids = []
        curr_user = False
        curr_shop = False
        if shop_id:
            curr_shop = self.pool.get('sale.shop').browse(cr, uid, [shop_id,], context)[0]
        curr_user = self.pool.get('res.users').browse(cr, uid, [uid, ], context)[0]
        if curr_user:
            for s in curr_user.shop_ids:
                shop_ids.append(s.id)
        if curr_shop:
            if type:
                if type == 'out_refund':
                    values['journal_id'] = curr_shop.credit_note_sale_journal_id.id
                    if printer_id:
                        auth_line_id = doc_obj.search(cr, uid, [('name','=','credit_note'),('printer_id','=',printer_id),('shop_id','=',curr_shop.id),('state','=',True),])
                        if auth_line_id:
                            values['authorization'] = doc_obj.browse(cr, uid, auth_line_id[0],context).sri_authorization_id.number
                            values['autorization_credit_note_id'] = doc_obj.browse(cr, uid, auth_line_id[0],context).sri_authorization_id.id
                            if automatic:
                                values['automatic_number'] = doc_obj.get_next_value_secuence(cr, uid, 'credit_note', False, company_id, curr_shop.id, printer_id,'account.invoice', 'number_credit_note_out', context)
                                values['number_credit_note_out'] = values['automatic_number']
                                values['date_invoice'] = time.strftime('%Y-%m-%d')
                            else:
                                values['number_credit_note_out'] = curr_shop.number + "-" + printer_obj.browse(cr, uid, printer_id, context).number + "-"
                        else:
                            values['authorization'] = None
                            values['autorization_credit_note_id'] = None
                            values['automatic'] = False
                            values['date_invoice'] = None
        return {'value': values, 'domain':{'shop_id':[('id','in', shop_ids)]}}

    def default_get(self, cr, uid, fields_list, context=None):
        """
        Returns default values for fields
        @param fields_list: list of fields, for which default values are required to be read
        @param context: context arguments, like lang, time zone

        @return: Returns a dict that contains default values for fields
        """
        if context is None:
            context = {}
        printer_obj = self.pool.get('sri.printer.point')
        doc_obj=self.pool.get('sri.type.document')
        values = super(account_invoice, self).default_get(cr, uid, fields_list, context=context)
        if not values:
            values={}
        shop_id = values.get('shop_id', False)
        printer_id = values.get('printer_id', False)
        company_id = values.get('company_id', False)
        automatic = values.get('automatic', False)
        type = values.get('type', False)
        if not company_id:
            company_id = self.pool.get('res.company')._company_default_get(cr, uid, 'account.invoice', context=context)
        manual = context.get('manual',False)
        shop_ids = []
        curr_user = False
        curr_shop = False
        if shop_id:
            curr_shop = self.pool.get('sale.shop').browse(cr, uid, [shop_id,], context)[0]
        curr_user = self.pool.get('res.users').browse(cr, uid, [uid, ], context)[0]
        if curr_user:
            for s in curr_user.shop_ids:
                shop_ids.append(s.id)
        if curr_shop:
            if type:
                if type == 'out_refund' and ('number_credit_note_out', 'automatic_number') in fields_list:
                    values['journal_id'] = curr_shop.sales_journal_id.id
                    if printer_id:
                        auth_line_id = doc_obj.search(cr, uid, [('name','=','credit_note'), ('printer_id','=',printer_id), ('shop_id','=',curr_shop.id), ('state','=',True)])
                        if auth_line_id:
                            values['authorization'] = doc_obj.browse(cr, uid, auth_line_id[0],context).sri_authorization_id.number
                            values['autorization_credit_note_id'] = doc_obj.browse(cr, uid, auth_line_id[0],context).sri_authorization_id.id
                            if automatic:
                                values['automatic_number'] = doc_obj.get_next_value_secuence(cr, uid, 'credit_note', False, company_id, curr_shop.id, printer_id, 'account.invoice', 'number_credit_note_out', context)
                                values['number_credit_note_out'] = values['automatic_number']
                                values['date_invoice'] = time.strftime('%Y-%m-%d')
                        else:
                            values['authorization'] = None
                            values['autorization_credit_note_id'] = None
                            values['automatic'] = False
                            values['date_invoice'] = None
        return values

    def action_number(self, cr, uid, ids, context=None):
        if not context:
            context={}
        inv_obj = self.pool.get('account.invoice')
        auth_s_obj = self.pool.get('sri.authorization.supplier')
        document_obj = self.pool.get('sri.type.document')
        for credit_note in self.browse(cr, uid, ids, context):
            context['automatic'] = credit_note.automatic
            if credit_note.type=='out_refund':
                if credit_note.invoice_rectification_id:
                    if credit_note.invoice_rectification_id.partner_id.id != credit_note.partner_id.id:
                        raise osv.except_osv(_('Invalid action!'), _("You must create Credit Note to Partner %s, It must be same of the invoice!" % credit_note.invoice_rectification_id.partner_id.name))
                if not credit_note.autorization_credit_note_id:
                    raise osv.except_osv(_('Invalid action!'), _('Not exist authorization for the document, please check'))
                if not credit_note.automatic:
                    if not credit_note.number_credit_note_out:
                        raise osv.except_osv(_('Invalid action!'), _('Not exist number for the document, please check'))
                    shop = credit_note.shop_id.id
                    auth = self.pool.get('sri.authorization').get_auth(cr, uid, 'credit_note', credit_note.company_id.id, shop, credit_note.number_credit_note_out, credit_note.printer_id.id, context)
                    if not auth['authorization']:
                        raise osv.except_osv(_('Invalid action!'), _('Do not exist authorization for this number of secuence, please check'))
                    doc_id = document_obj.search(cr, uid, [('name','=','credit_note'),('printer_id','=',credit_note.printer_id.id),('shop_id','=',credit_note.shop_id.id),('sri_authorization_id','=',credit_note.autorization_credit_note_id.id)])
                    document_obj.add_document(cr, uid, doc_id, context)
                    self.write(cr, uid, [credit_note.id], {'invoice_number': credit_note.number_credit_note_out, 'flag': True, 'authorization':credit_note.autorization_credit_note_id.number}, context)
                else:
                    if not credit_note.number_credit_note_out:
                        b = True
                        vals_aut = self.pool.get('sri.authorization').get_auth_secuence(cr, uid, 'credit_note', credit_note.company_id.id, credit_note.shop_id.id, credit_note.printer_id.id)
                        while b :
                            number_out = self.pool.get('ir.sequence').get_id(cr, uid, vals_aut['sequence'])
                            if not self.pool.get('account.credit_note').search(cr, uid, [('type','=','out_refund'),('invoice_number','=',number_out), ('automatic','=',True),('id','not in',tuple(ids))],):
                                b=False
                    else:
                        number_out = credit_note.number_credit_note_out
                    doc_id = document_obj.search(cr, uid, [('name','=','credit_note'),('printer_id','=',credit_note.printer_id.id),('shop_id','=',credit_note.shop_id.id),('sri_authorization_id','=',credit_note.autorization_credit_note_id.id)])
                    document_obj.add_document(cr, uid, doc_id, context)
                    self.write(cr, uid, [credit_note.id], {'invoice_number': number_out,'number_credit_note_out': number_out, 'flag': True, 'authorization':credit_note.autorization_credit_note_id.number}, context)
            elif credit_note.type=='in_refund':
                auth_s_obj.check_number_document(cr, uid, credit_note.number_credit_note_in, credit_note.authorization_credit_note_purchase_id, credit_note.date_invoice, 'account.invoice', 'number_credit_note_in', _("Credit note"), context, id_model=credit_note.id)
                for inv in inv_obj.search(cr, uid, [('partner_id.id', '=', credit_note.partner_id.id), ('type','=','in_refund'), ('id','not in',tuple(ids))]):
                    if credit_note.number_credit_note_in:
                        if inv_obj.browse(cr, uid, [inv,], context)[0].number_credit_note_in == credit_note.number_credit_note_in:
                            raise osv.except_osv(_('Error!'), _("There is an credit_note with number %s for supplier %s") % (credit_note.number_credit_note_in, credit_note.partner_id.name))                        
                if credit_note.number_credit_note_in:
                    self.write(cr, uid, [credit_note.id], {'invoice_number': credit_note.number_credit_note_in,'authorization_credit_note_purchase' : credit_note.authorization_credit_note_purchase_id.number}, context)
        result = super(account_invoice, self).action_number(cr, uid, ids, context)
        self.write(cr, uid, ids, {'internal_number': False,}, context)
        return result

    def action_cancel_draft(self, cr, uid, ids, *args):
        document_obj = self.pool.get('sri.type.document')
        for credit_note in self.browse(cr, uid, ids):
            if credit_note.type=='out_refund':
                if credit_note.flag:
                    for doc in credit_note.autorization_credit_note_id.type_document_ids:
                        if doc.name=='credit_note':
                            document_obj.rest_document(cr, uid, [doc.id,])
                    self.write(cr, uid, [credit_note.id], {'flag': False}, context=None)
            return super(account_invoice, self).action_cancel_draft(cr, uid, ids)

    def action_date_assign(self, cr, uid, ids, *args):
        auth_obj = self.pool.get('sri.authorization')
        date=False
        res = super(account_invoice, self).action_date_assign(cr, uid, ids, args)
        for credit_note in self.browse(cr, uid, ids):
            if credit_note.type=='out_refund':
                if not credit_note.date_invoice:
                    date = time.strftime('%Y-%m-%d')
                else:
                    date = credit_note.date_invoice
                if not auth_obj.check_date_document(cr, uid, date, credit_note.autorization_credit_note_id.start_date, credit_note.autorization_credit_note_id.expiration_date):
                    raise osv.except_osv(_('Invalid action!'), _('The date entered is not valid for the authorization')) 
        return res
    
    def check_invoice_type(self, cr, uid, ids, *args):
        for o in self.browse(cr, uid, ids):
            if o.type == 'in_invoice':
                return True
            if o.type == 'out_invoice':
                return True
        return False

    def check_refund_with_invoice(self, cr, uid, ids, *args):
        for o in self.browse(cr, uid, ids):
            if o.type == 'in_refund' and o.invoice_rectification_id!=False:
                return True
            if o.type == 'out_refund' and o.invoice_rectification_id!=False:
                return True
        return False

    def check_refund_without_invoice(self, cr, uid, ids, *args):
        for o in self.browse(cr, uid, ids):
            if o.type == 'in_refund' and not o.invoice_rectification_id:
                return True
            if o.type == 'out_refund' and not o.invoice_rectification_id:
                return True
        return False
    
    def action_wait_invoice(self, cr, uid, ids, *args):
        for o in self.browse(cr, uid, ids):
            self.write(cr, uid, [o.id], {'state': 'wait_invoice',})
        return True

    def action_move_credit_note_create(self, cr, uid, ids, *args):
        """Creates invoice related analytics and financial move lines"""
        ait_obj = self.pool.get('account.invoice.tax')
        cur_obj = self.pool.get('res.currency')
        inv_obj = self.pool.get('account.invoice')
        context = {}
        for credit_note in self.browse(cr, uid, ids):
            if not credit_note.invoice_rectification_id:
                #Se crea el movimiento para que quede en libros el valor de la nota de credito
                inv_obj.action_move_create(cr, uid, ids, *args)
            else:
                #Si ya tiene movimiento, quiere decir que estuvo en espera y ahora se va a usar para conciliar otra factura
                if credit_note.move_id:
                    self._create_voucher(cr, uid, credit_note.invoice_rectification_id, credit_note, context)
                #Si no tiene movimiento se debera crear el movimiento y hacer la conciliacion
                else:
                    inv_obj.action_move_create(cr, uid, ids, *args)
                    self._create_voucher(cr, uid, credit_note.invoice_rectification_id, credit_note, context)
        self._log_event(cr, uid, ids)
        return True
                
    def _create_voucher(self, cr, uid, invoice, credit_note, context):
        self._validate_credit_note(cr, uid, invoice, credit_note, context)
        if context is None:
            context = {}
        acc_move_line_obj = self.pool.get('account.move.line')
        acc_vou_obj = self.pool.get('account.voucher')
        acc_vou_line_obj = self.pool.get('account.voucher.line')
        currency_obj = self.pool.get('res.currency')
        partner_id = credit_note.partner_id.id
        journal_id = credit_note.journal_id.id
        company_currency = credit_note.journal_id.company_id.currency_id.id
        currency_id = credit_note.currency_id.id
        line_cr_ids = []
        line_dr_ids = []
        line_ids = []
        total_credit = 0.0
        total_debit = 0.0
        ids = []
        period_id = credit_note.period_id and credit_note.period_id.id or False
        if not period_id:
            period_ids = self.pool.get('account.period').search(cr, uid, [('date_start','<=',credit_note.date_invoice or time.strftime('%Y-%m-%d')),('date_stop','>=',credit_note.date_invoice or time.strftime('%Y-%m-%d')), ('company_id', '=', credit_note.company_id.id)])
            if period_ids:
                period_id = period_ids[0]
        domain = [('state','=','valid'), ('account_id.type', 'in', ('payable', 'receivable')), ('reconcile_id', '=', False), ('partner_id', '=', partner_id)]
        domain.append(('invoice', 'in', (invoice.id, credit_note.id)))
        for id in acc_move_line_obj.search(cr, uid, domain, context=context):
            ids.append(id)
        ids.reverse()
        moves = acc_move_line_obj.browse(cr, uid, ids, context=context)
        for line in moves:
            total_credit += line.credit or 0.0
            total_debit += line.debit or 0.0
        for line in moves:
            original_amount = line.credit or line.debit or 0.0
            amount_unreconciled = currency_obj.compute(cr, uid, line.currency_id and line.currency_id.id or company_currency, currency_id, abs(line.amount_residual_currency), context=context)
            rs = {
                'name':line.move_id.name,
                'type': line.credit and 'dr' or 'cr',
                'move_line_id':line.id,
                'account_id':line.account_id.id,
                'amount_original': currency_obj.compute(cr, uid, line.currency_id and line.currency_id.id or company_currency, currency_id, line.currency_id and abs(line.amount_currency) or original_amount, context=context),
                'date_original':line.date,
                'date_due':line.date_maturity,
                'amount_unreconciled': amount_unreconciled,
            }
            if line.credit:
                amount = min(amount_unreconciled, currency_obj.compute(cr, uid, company_currency, currency_id, abs(total_debit), context=context))
                rs['amount'] = amount
                total_debit -= amount
            else:
                amount = min(amount_unreconciled, currency_obj.compute(cr, uid, company_currency, currency_id, abs(total_credit), context=context))
                rs['amount'] = amount
                total_credit -= amount

            if rs['type'] == 'cr':
                line_cr_ids.append((0,0,rs))
            else:
                line_dr_ids.append((0,0,rs))
                        
        type_voucher = "receipt"
        if credit_note.type == "in_refund":
            type_voucher = "payment"
        
        vals_vou = {
                    'type':type_voucher,
                    'period_id': period_id,
                    'journal_id': journal_id,
                    'account_id': credit_note.journal_id.default_debit_account_id.id,
                    'company_id' : self.pool.get('res.users').browse(cr, uid, uid, context=context).company_id.id,
                    'amount': 0.0,
                    'currency_id': currency_id,
                    'partner_id': partner_id,
                    'line_dr_ids':line_dr_ids,
                    'line_cr_ids':line_cr_ids,
                    'line_ids':line_ids,
        }
        voucher_id = acc_vou_obj.create(cr, uid, vals_vou, context)
        acc_vou_obj.action_move_line_create(cr, uid, [voucher_id,], context=context)
        return True

    def _validate_credit_note(self, cr, uid, invoice, credit_note, context):
        inv_obj = self.pool.get('account.invoice')
        #La nota de credito no puede ser superior al total de la factura
        if credit_note.amount_total > invoice.amount_total:
            raise osv.except_osv(_('Warning!'), _("The amount total of credit note %s %s, can't be bigger than amount total of invoice %s %s!, Can't Validate" %(credit_note.number, credit_note.amount_total, invoice.number, invoice.amount_total)))
        #Si ya se encuentra parcialmente conciliada y es mayor al residual debe lanzar un error
        if invoice.state == open:
            if credit_note.amount_total > invoice.residual:
                raise osv.except_osv(_('Warning!'), _("The amount total of credit note %s is %s, can't be bigger than residual of invoice %s %s! Can't Validate" %(credit_note.number, credit_note.amount_total, invoice.number, invoice.residual)))
        else:
            #Se verifica que no se emita notas de credit para devolucion que superen el valor total de la nota de credito
            credit_notes_ids = inv_obj.search(cr, uid, [('invoice_rectification_id','=', invoice.id), ('id', '!=', credit_note.id), ('state', '=', 'open')])
            if credit_notes_ids:
                total = 0
                for cn in inv_obj.browse(cr, uid, credit_notes_ids):
                    total += cn.amount_total
                total += credit_note.amount_total
                if total > invoice.amount_total:
                    raise osv.except_osv(_('Warning!'), _("The sum of total amounts of Credit Notes in Invoice %s %s, can't be bigger than total %s! Can't Validate" %(invoice.number, total, invoice.amount_total)))                    
        return True

    def button_reset_taxes(self, cr, uid, ids, context=None):
        for inv in self.browse(cr, uid, ids, context):
            vals = {}
            if inv.automatic:
                if inv.type == "out_refund":
                    vals['automatic_number'] = inv.number_credit_note_out
                if inv.autorization_credit_note_id:
                    vals['authorization'] = inv.autorization_credit_note_id.number
            self.write(cr, uid, [inv.id], vals)
        return super(account_invoice, self).button_reset_taxes(cr, uid, ids, context)

    def fields_view_get(self, cr, uid, view_id=None, view_type=False, context=None, toolbar=False, submenu=False):
        user = self.pool.get('res.users').browse(cr, uid, uid, context=context)
        res = super(account_invoice,self).fields_view_get(cr, uid, view_id=view_id, view_type=view_type, context=context, toolbar=toolbar, submenu=submenu)
        type = context.get('type', 'out_invoice')
        client = context.get('client','gtk')
        liquidation = context.get('liquidation',False)
        if view_type == 'search':
            doc = etree.XML(res['arch'])
            for field in res['fields']:
                if field == 'number':
                    nodes = doc.xpath("//field[@name='number']")
                    for node in nodes:
                        node.set('invisible', type and not liquidation and "1" or "0")
                        if type and client == 'web' and not liquidation:
                            node.getparent().remove(node)
                if field == 'invoice_number_out':
                    nodes = doc.xpath("//field[@name='invoice_number_out']")
                    for node in nodes:
                        node.set('invisible', type == 'out_invoice' and "0" or "1")
                        if type != 'out_invoice' and client == 'web':
                            node.getparent().remove(node)
                if field == 'invoice_number_in':
                    nodes = doc.xpath("//field[@name='invoice_number_in']")
                    for node in nodes:
                        node.set('invisible', type == 'in_invoice' and not liquidation and "0" or "1")
                        if type != 'in_invoice' and client == 'web' and not liquidation:
                            node.getparent().remove(node)
                if field == 'number_credit_note_out':
                    nodes = doc.xpath("//field[@name='number_credit_note_out']")
                    for node in nodes:
                        node.set('invisible', type == 'out_refund' and "0" or "1")
                        if type != 'out_refund' and client == 'web':
                            node.getparent().remove(node)
                if field == 'number_credit_note_in':
                    nodes = doc.xpath("//field[@name='number_credit_note_in']")
                    for node in nodes:
                        node.set('invisible', type == 'in_refund' and "0" or "1")
                        if type != 'in_refund' and client == 'web':
                            node.getparent().remove(node)
            res['arch'] = etree.tostring(doc)
        if view_type == 'form':
            for field in res['fields']:
                if user.company_id.generate_automatic:
                    if field == 'automatic_number':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='automatic_number']")
                        for node in nodes:
                            node.set('invisible', "0")
                        res['arch'] = etree.tostring(doc)
                    if field == 'number_credit_note_out':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='number_credit_note_out']")
                        for node in nodes:
                            node.set('invisible', "1")
                        res['arch'] = etree.tostring(doc)
                else:
                    if field == 'automatic_number':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='automatic_number']")
                        for node in nodes:
                            node.set('invisible', "1")
                        res['arch'] = etree.tostring(doc)
                    if field == 'number_credit_note_out':
                        doc = etree.XML(res['arch'])
                        nodes = doc.xpath("//field[@name='number_credit_note_out']")
                        for node in nodes:
                            node.set('invisible', "0")
                        res['arch'] = etree.tostring(doc)
        return res

    def create(self, cr, uid, vals, context=None):
        auth_obj = self.pool.get('sri.authorization')
        if not context:
            context = {}
        if vals.get('number_credit_note_out', False):
            if context.get('type', False) == 'out_refund':
                vals['automatic_number'] = vals.get('number_credit_note_out', False)
                if vals.get('autorization_credit_note_id', False):
                    vals['authorization'] = auth_obj.browse(cr, uid, vals['autorization_credit_note_id'], context).number
        res = super(account_invoice, self).create(cr, uid, vals, context)
        return res


    _inherit = 'account.invoice' 
    _columns = {
            'invoice_rectification_id':fields.many2one('account.invoice', 'Canceled Invoice', readonly=True, states={'draft':[('readonly', False)]}),
            'number_credit_note_in':fields.char('Number', size=17, readonly=True, states={'draft':[('readonly', False)]}),
            'number_credit_note_out':fields.char('Number', size=17, readonly=True, states={'draft':[('readonly', False)]}),
            'autorization_credit_note_id':fields.many2one('sri.authorization', 'Autorization', required=False, states={'draft':[('readonly', False)]}),
            'authorization_credit_note_purchase':fields.char('Authorization', size=10, required=False, readonly=True, states={'draft':[('readonly', False)]}, help='This Number is necesary for SRI reports'),
            'authorization_credit_note_purchase_id':fields.many2one('sri.authorization.supplier', 'Authorization', readonly=True, states={'draft':[('readonly',False)]}), 
            'credit_note_ids':fields.one2many('account.invoice', 'invoice_rectification_id', 'Credit Notes', required=False),
            'state': fields.selection([
            ('draft','Draft'),
            ('proforma','Pro-forma'),
            ('proforma2','Pro-forma'),
            ('open','Open'),
            ('paid','Paid'),
            ('wait_invoice','Waiting Invoice'),
            ('cancel','Cancelled')
            ],'State', select=True, readonly=True,
            help=' * The \'Draft\' state is used when a user is encoding a new and unconfirmed Invoice. \
            \n* The \'Pro-forma\' when invoice is in Pro-forma state,invoice does not have an invoice number. \
            \n* The \'Open\' state is used when user create invoice,a invoice number is generated.Its in open state till user does not pay invoice. \
            \n* The \'Paid\' state is set automatically when invoice is paid.\
            \n* The \'Cancelled\' state is used when user cancel invoice.'),                    
                }

account_invoice()

# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Carlos Yumbillo                                                                           
# Copyright (C) 2013  TRESCLOUD Cia Ltda.                                 
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

from osv import osv, fields

class document_invoice_type(osv.osv):
    """ Type document """
    _name = 'account.invoice.document.type'
    _order = 'priority'
    
    _columns = {
         'report_id':fields.many2one('ir.actions.report.xml','Name report', change_default=1, domain="[('model','=','account.invoice')]", help='Report format to use when printing.', ),
         'code':fields.char('Code', size=4, required=True, help='Used to generate the ats',),
         'name':fields.char('Name', size=255, required=True,),
         'use':fields.boolean('Activo', help='Indicates whether the document is to be active.',),
         'number_format_validation':fields.boolean('Number format', help='Indicates if the number of this document will go through a validation process format.',),
         'sri_authorization_validation':fields.boolean('SRI authorization', help='Indicates if the number of this document will be linked to an authorization number.',),          
         'sri_authorization_validation_owner':fields.boolean('SRI authorization owner', help='Indicates if the number of this document will be linked to an authorization number assigned by the company.',),
         'priority':fields.integer('Priority', required=True, help='Indicates the priority of the document.',),
         'type': fields.selection([
            ('out_invoice','Customer Document'),
            ('in_invoice','Supplier Document'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
            ],'Type', select=True, change_default=True, required=True, help='Indicates whether the document is of supplier or customer.',),         
     } 
    
    _defaults = {
        'use': False,
        'number_format_validation': False,
        'sri_authorization_validation': False,       
     }
    
document_invoice_type()

class account_invoice(osv.osv):
    
    _inherit = "account.invoice"
     
    _columns = {
        'document_invoice_type_id': fields.many2one('account.invoice.document.type', 'Document type', required=True, help='Indicates the type of accounting document authorized to issue when making a purchase or sale.',)
    }
    
    def onchange_partner2_id(self, cr, uid, ids, document_invoice_type_id, type, partner_id, date_invoice=False, payment_term=False, partner_bank_id=False, company_id=False):
        partner_obj = self.pool.get('res.partner')
        res = super(account_invoice, self).onchange_partner_id(cr, uid, ids, type, partner_id, date_invoice, payment_term, partner_bank_id, company_id)
        obj_auth=self.pool.get('sri.authorization')
        if document_invoice_type_id:
            obj_document=self.pool.get('account.invoice.document.type')
            document_invoice=obj_document.browse(cr,uid,document_invoice_type_id)
            if document_invoice.sri_authorization_validation_owner==True:
                res['value']['aut_flag']=True
                line_auth_obj = self.pool.get('sri.type.document')
                lines=line_auth_obj.search(cr, uid, [('name2','=',document_invoice_type_id)])
                auth_ids=obj_auth.search(cr,uid,[('type_document_ids','=',lines)])
                res['value']['authorization_sales']=auth_ids
                document=line_auth_obj.browse(cr,uid,lines[0])
                res['value']['invoice_number_in'] = document.shop_id.number + "-"+document.printer_id.number+"-"
                
            else:    
                if document_invoice.sri_authorization_validation==False:
                    if type=='out_invoice':
                        obj_auth=self.pool.get('sri.authorization')
                        auth_id=obj_auth.search(cr,uid,[('number','=','9999999999')])
                        res['value']['authorization'] = obj_auth.browse(cr,uid,auth_id[0]).number
                        res['value']['authorization_sales']=obj_auth.browse(cr,uid,auth_id[0]).id
                    else:
                        obj_auth=self.pool.get('sri.authorization.supplier')
                        auth_id=obj_auth.search(cr,uid,[('number','=','9999999999')])
                        res['value']['authorization_supplier_purchase_id']=obj_auth.browse(cr,uid,auth_id[0]).id
        return res
    
    def _doc_type(self, cr, uid, context=None):

       doc_type_id = 0
       if context and 'type' in context:
          invoice_type = context['type']
       else:
          invoice_type = 'out_invoice'
                        
       cr.execute('''select min(ai.priority) as priority, ai.id as id
                 from account_invoice_document_type ai
                 where ai.type='%s'
                 group by id
                 order by priority''' %(invoice_type))
       res = cr.dictfetchone()
   
       if res:
          doc_type_id = res['id']
   
       return doc_type_id      
   
    def print_document_type(self, cr, uid, ids, context=None):
        invoice_obj = self.pool.get('account.invoice')
        invoice_list = invoice_obj.search(cr, uid, [('id','=',ids[0])])[0]
        
        invoice = invoice_obj.browse(cr,uid,invoice_list)
        invoice_type = invoice.type
        
        if invoice.document_invoice_type_id: 
            service_name = invoice.document_invoice_type_id.report_id.report_name
        else:
            cr.execute('''select min(ai.priority) as priority, ai.report_id as report_id, r.report_name as report_name 
                        from account_invoice_document_type ai, ir_act_report_xml r
                        where ai.report_id=r.id and ai.type='%s'
                        group by report_id, report_name
                        order by priority''' %(invoice_type))
            res = cr.dictfetchone()
            service_name = res['report_name']
                    
        if service_name:
            return {
                 'type': 'ir.actions.report.xml',
                 'report_name': service_name,    # the 'Service Name' from the report
                 'datas' : {
                         'model' : 'account.invoice',    # Report Model
                         'res_ids' : ids
                           }        
                  }
        else:
            raise osv.except_osv('Warning!', "You do not have established a document format for printing.")
        
    _defaults = {
       'document_invoice_type_id': _doc_type,        
    }  
    
account_invoice()

class sri_type_document(osv.osv):  
    _inherit = 'sri.type.document'
    _columns = {
                'name2':fields.many2one('account.invoice.document.type', 'Name', required=True),
                }
sri_type_document()
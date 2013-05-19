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

class documet_type(osv.osv):
    """ Type document """
    _name = 'account.invoice.document.type'
    _order = 'priority'
    
    _columns = {
         'report_id':fields.many2one('ir.actions.report.xml','Name report', change_default=1, domain="[('model','=','account.invoice')]" ),
         'code':fields.char('Code', size=4, required=True,),
         'name':fields.char('Name', size=255, required=True,),
         'use':fields.boolean('Activo'),
         'validate':fields.boolean('Validate'),          
         'priority':fields.integer('Priority', required=True,),
         'type': fields.selection([
            ('out_invoice','Customer Document'),
            ('in_invoice','Supplier Document'),
            ('out_refund','Customer Refund'),
            ('in_refund','Supplier Refund'),
            ],'Type', select=True, change_default=True, required=True,),         
     } 
    
    _defaults = {
        'use': False,
        'validate': False,        
     }
    
documet_type()

class account_invoice(osv.osv):
    
     _inherit = "account.invoice"
     
     _columns = {
        'document_type_id': fields.many2one('account.invoice.document.type', 'Document type', required=True)
     }
    
     def _doc_type(self, cr, uid, context=None):

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

        doc_type_id = res['id']
    
        return doc_type_id      
    
     def print_document_type(self, cr, uid, ids, context=None):

        invoice_obj = self.pool.get('account.invoice')
        invoice_list = invoice_obj.search(cr, uid, [('id','=',ids[0])])[0]
        
        invoice = invoice_obj.browse(cr,uid,invoice_list)
        invoice_type = invoice.type
        
        if invoice.document_type_id: 
            service_name = invoice.document_type_id.report_id.report_name
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
        'document_type_id': _doc_type,        
     }  
    
account_invoice()
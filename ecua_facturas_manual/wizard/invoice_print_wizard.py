# -*- coding: UTF-8 -*- #
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2012-2013 Christopher Ormaza (http://www.ecuadorenlinea.net>). 
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

import time

from osv import fields, osv
from tools.translate import _
import netsvc
from lxml import etree
import re

class print_wizard(osv.osv_memory):
    _name = 'account.invoice.print.wizard'
    
    _columns = {
                'number':fields.char('Number', size=17, readonly=True), 
                    }

    def default_get(self, cr, uid, fields, context=None):
        if context is None:
            context = {}
        values = {}
        res = []
        objs = self.pool.get(context['active_model']).browse(cr , uid, context['active_ids'])
        if 'value' not in context.keys():
            for obj in objs:
                if obj.type == 'out_invoice':
                    values = {
                             'number': obj.invoice_number_out,
                            }
        else:
            values = context['value']
        return values
    
    def print_action(self, cr, uid, ids, context=None):
        if context is None:
            context = {}
        data = {}
        data['model'] = 'account.invoice'
        data['ids'] = context.get('active_ids', False)
        return {
               'type': 'ir.actions.report.xml',
               'report_name': 'invoice',    # the 'Service Name' from the report
               'datas' : data,
               'context': context,
           }
        
print_wizard()
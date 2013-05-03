#-*- coding:utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution    
#    Copyright (C) 2013- Carlos Lopez Mite(celm1990@outlook.com) - Ecuadorenlinea.net 
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

from report import report_sxw
from lxml import etree
from osv import osv
class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        if not context: context={}
        super(Parser, self).__init__(cr, uid, name, context)
        ids= context.get('active_ids',[])
        vacation_list=[]
        for vacation in self.pool.get('hr.vacation').browse(cr, uid, ids, context):
            if vacation.state=='confirm':
                date_ingreso= self.pool.get('hr.employee').get_date_last_contract_continuo( cr, uid, vacation.employee_id.id, days_free=7)
                vacation_list.append({'vacation': vacation, 'date_ingreso':date_ingreso})
        self.localcontext.update({
                                  'vacations': vacation_list,
        })

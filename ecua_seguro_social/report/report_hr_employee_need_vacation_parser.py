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
from datetime import datetime
class Parser(report_sxw.rml_parse):
    def __init__(self, cr, uid, name, context):
        if not context: context={}
        super(Parser, self).__init__(cr, uid, name, context)
        ids= context.get('active_ids',[])
        employee_obj= self.pool.get('hr.employee')
        vacation_obj= self.pool.get('hr.vacation')
        employee_list=[]
        for employee in employee_obj.browse(cr, uid, ids, context):
            date_ingreso= employee_obj.get_date_last_contract_continuo( cr, uid, employee.id, days_free=7)
            date_next_vacation=False
            date_last_vacation=''
            days_accumulated=0
            days_now=0
            days_max=0
            if employee.last_vacation_id:
                
                year_str= employee.date_next_vacation[0:4]
                date_start= employee.date_next_vacation
                date_end= employee.date_next_vacation
                days_current_year= employee.last_vacation_id.days_current_year
                date_last_vacation=employee.last_vacation_id.date_start
                years= vacation_obj.get_year_start_end(cr, uid, employee.last_vacation_id.id, employee.id, year_str ,date_start , date_end, context)
                year_start, year_end = years.get('year_start'), years.get('year_end')
                days_accumulated= vacation_obj.get_days_acumulated(cr, uid, employee.last_vacation_id.id, employee.id, year_str, date_end, year_start, year_end, context)
                #Dias que debe tomar el año actual
                days_now=vacation_obj.get_days_now(cr, uid, days_current_year, employee.id, year_str, date_start, date_end, employee.last_vacation_id, context)
                #Dias Maximos permitidos.
                days_max= vacation_obj.get_days_max(days_current_year , days_accumulated, days_now, employee.last_vacation_id, context)
            else:
                #pasar las fechas actuales para calcular los años que tiene acumulado
                new_context= context.copy()
                new_context.update({'extern':True})
                date_end= datetime.now().strftime('%Y-%m-%d')
                date_start= datetime.now().strftime('%Y-%m-%d')
                year_str=date_start[0:4]
                years= vacation_obj.get_year_start_end(cr, uid, None, employee.id, year_str, date_start, date_end, new_context)
                year_start, year_end = years.get('year_start'), years.get('year_end')
                diff_year= year_end - year_start
                days_accumulated= vacation_obj.get_days_acumulated(cr, uid, None, employee.id, year_str, date_end, year_start, year_end, new_context)
                #Dias que debe tomar el año actual
                days_now=vacation_obj.get_days_now(cr, uid, 0, employee.id, year_str, date_start, date_end, None, new_context)
                #Dias Maximos permitidos.
                days_max= vacation_obj.get_days_max(0, days_accumulated, days_now, None, new_context)
            employee_list.append({'employee': employee,
                                  'date_ingreso': date_ingreso,
                                  'date_last_vacation': date_last_vacation,
                                  'date_next_vacation': employee.date_next_vacation,
                                  'days_vacation_acumulated': int(days_accumulated),
                                  'days_now': int(days_now),
                                  'days_max': int(days_max)})
        self.localcontext.update({
                                  'employee_list': employee_list,
        })

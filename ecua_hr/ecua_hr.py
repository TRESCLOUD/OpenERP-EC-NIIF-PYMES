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
from datetime import datetime
import calendar
from dateutil.relativedelta import relativedelta

class hr_payslip(osv.osv):
    '''
    Pay Slip
    '''
    _inherit = 'hr.payslip'

    def get_inputs(self, cr, uid, contract_ids, date_from, date_to, context=None):
        res = super(hr_payslip, self).get_inputs(cr, uid, contract_ids, date_from, date_to, context=context)
        contract_obj = self.pool.get('hr.contract')

        for contract in contract_obj.browse(cr, uid, contract_ids, context=context):

            input1 = {
                 'name': 'Bono',
                 'code': 'BONIFICACIÓN',
                 'amount': 0.0,
                 'contract_id': contract.id,
            }
            input2 = {
                 'name': 'Comisión',
                 'code': 'COMISIÓN',
                 'amount': 0.0,
                 'contract_id': contract.id,
            }
            input3 = {
                 'name': 'Transporte',
                 'code': 'TRANSPORTE',
                 'amount': 0.0,
                 'contract_id': contract.id,
            }
            input4 = {
                 'name': 'Alimentación',
                 'code': 'ALIMENTACIÓN',
                 'amount': 0.0,
                 'contract_id': contract.id,
            }
            res += [input1,input2,input3,input4]

        return res
    
    def get_worked_day_lines(self, cr, uid, contract_ids, date_from, date_to, context=None):
        res = super(hr_payslip, self).get_worked_day_lines(cr, uid, contract_ids, date_from, date_to, context=context)
        contract_obj = self.pool.get('hr.contract')
        
        if date_from:
            DATETIME_FORMAT = "%Y-%m-%d"
            date_from = datetime.strptime(date_from, DATETIME_FORMAT)
            year = date_from.year
            mes = date_from.month
            
            if mes==1 or mes==3 or mes==5 or mes==7 or mes==8 or mes==10 or mes==12:
               days = 31.0
            elif mes==4 or mes==6 or mes==9 or mes==11:
                 days = 30.0
                    
            if mes==2:
                if calendar.isleap(year):
                    days = 29.0
                else: 
                    days = 28.0
        else:
            days = 30.0
        
        for contract in contract_obj.browse(cr, uid, contract_ids, context=context):

            attendances1 = {
                 'name': 'Horas extras regulares',
                 'code': 'HORA_EXTRA_REGULAR',
                 'number_of_days': 0.0,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }
            attendances2 = {
                 'name': 'Horas extras extraordinarias',
                 'code': 'HORA_EXTRA_EXTRAORDINARIA',
                 'number_of_days': 0.0,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }
            attendances3 = {
                 'name': 'Dias Calendario del Mes',
                 'code': 'DIAS_DEL_MES',
                 'number_of_days': days,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }
            attendances4 = {
                 'name': 'Dias Calendario Laborados',
                 'code': 'DIAS_TRABAJADOS',
                 'number_of_days': days,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }  
            res += [attendances1,attendances2,attendances3,attendances4]

        return res  
            
hr_payslip()

class hr_contract(osv.osv):
    _inherit = 'hr.contract'
    _name = 'hr.contract' 
      
    def _compute_year(self, cr, uid, ids, field, arg, context=None):
        ''' Función que calcula el número de años de servicio de un empleado trabajando para la empresa.'''
        
        res = {}
        DATETIME_FORMAT = "%Y-%m-%d"
        today = datetime.now()

        for contract in self.browse(cr, uid, ids, context=context):
            if contract.date_start:
                date_start = datetime.strptime(contract.date_start, DATETIME_FORMAT)
                diffyears = today.year - date_start.year
                difference = today - date_start.replace(today.year)
                days_in_year = calendar.isleap(today.year) and 366 or 365
                difference_in_years = diffyears + (difference.days + difference.seconds / 86400.0) / days_in_year
                total_years = relativedelta(today, date_start).years
                total_months = relativedelta(today, date_start).months
                months_equiv_in_year = ((float(total_months)*1)/12)
                year_month = float(total_months) / 100 + total_years
                year = float(months_equiv_in_year) + total_years
                res[contract.id] = year
            else:
                res[contract.id] = 0.0
        return res
    
    _columns = {
       'number_of_year': fields.function(_compute_year, string='No. of years of service', type='float', store=False, method=True, help='Total years of work experience'),
        }

hr_contract()    
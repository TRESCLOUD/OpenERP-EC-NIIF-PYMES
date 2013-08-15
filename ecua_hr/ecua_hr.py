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
from tools.translate import _

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
                 'code': 'BONO',
                 'amount': 0.0,
                 'contract_id': contract.id,
            }
            input2 = {
                 'name': 'Comision',
                 'code': 'COMISION',
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
                 'name': 'Alimentacion',
                 'code': 'ALIMENTACION',
                 'amount': 0.0,
                 'contract_id': contract.id,
            }
            res += [input1,input2,input3,input4]

        return res
    
    def get_worked_day_lines(self, cr, uid, contract_ids, date_from, date_to, context=None):
        res = super(hr_payslip, self).get_worked_day_lines(cr, uid, contract_ids, date_from, date_to, context=context)
        contract_obj = self.pool.get('hr.contract')
        
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
                 'number_of_days': 30.0,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }
            attendances4 = {
                 'name': 'Dias Calendario Laborados',
                 'code': 'DIAS_TRABAJADOS',
                 'number_of_days': 30.0,
                 'number_of_hours': 0.0,
                 'contract_id': contract.id,
            }  
            res += [attendances1,attendances2,attendances3,attendances4]

        return res
    
    def unlink(self, cr, uid, ids, context=None):
        if not context:
            context = {}
        unlink_ids = []
        for payslips_line in self.browse(cr, uid, ids, context):
            if payslips_line.state != 'draft':
                raise osv.except_osv(_('Invalid action !'), _('Cannot delete delivery payslip(s) that are already Done. Change its to draft state !'))
            else:
                cr.execute('''delete from hr_payslip_input where payslip_id=%s''' %(payslips_line.id))
                
        return super(hr_payslip, self).unlink(cr, uid, ids)
    
    def _compute_year(self, cr, uid, ids, field, arg, context=None):
        ''' Función que calcula el número de años de servicio de un empleado trabajando para la empresa.'''
        
        res = {}
        DATETIME_FORMAT = "%Y-%m-%d"
        #today = datetime.now()

        for payslip in self.browse(cr, uid, ids, context=context):
            if payslip.date_to and payslip.contract_id.date_start:               
                date_start = datetime.strptime(payslip.contract_id.date_start, DATETIME_FORMAT)
                today=datetime.strptime(payslip.date_to, DATETIME_FORMAT)
                diffyears = today.year - date_start.year
                difference = today - date_start.replace(today.year)
                days_in_year = calendar.isleap(today.year) and 366 or 365
                difference_in_years = diffyears + (difference.days + difference.seconds / 86400.0) / days_in_year
                total_years = relativedelta(today, date_start).years
                total_months = relativedelta(today, date_start).months
                months_in_years = total_months*0.083333333
                year_month = float(total_months) / 100 + total_years
                number_of_year = total_years + months_in_years  
                res[payslip.id] = number_of_year
            else:
                res[payslip.id] = 0.0
        return res
    _columns={
              'number_of_year': fields.function(_compute_year, string='No. of years of service', type='float', store=False, method=True, help='Total years of work experience'),
              }
         
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
                months_in_years = total_months*0.083333333
                year_month = float(total_months) / 100 + total_years
                number_of_year = total_years + months_in_years  
                res[contract.id] = number_of_year
            else:
                res[contract.id] = 0.0
        return res
    
    def _compute_day_pay(self, cr, uid, ids, field, arg, context=None):
        """Funcion que me ayuda para calcular los fondos de reserva del empleado"""
        res = {}
        DATETIME_FORMAT = "%Y-%m-%d"
        today = datetime.now()
        last_day=30
        for contract in self.browse(cr, uid, ids, context=context):
            date_start = datetime.strptime(contract.date_start, DATETIME_FORMAT)
            if date_start.day<last_day and date_start.day>1:
                res[contract.id]=last_day-date_start.day
            else:
                res[contract.id] = last_day
        return res    
    
    _columns = {
       'number_of_year': fields.function(_compute_year, string='No. of years of service', type='float', store=False, method=True, help='Total years of work experience'),
       'type_id': fields.many2one('hr.contract.type', "Contract Type", required=False),
       'day_pay':fields.function(_compute_day_pay,string="Day Pay",type='float',store=False,method=True),
        }
    
    _defaults = {
       'method_payment': 'payment_employee',         
        }

hr_contract()

class resource_calendar(osv.osv):
    _inherit = 'resource.calendar'
    _name = 'resource.calendar' 
      
    def _compute_hours(self, cr, uid, ids, field, arg, context=None):
        ''' Función que calcula el número de horas trabajadas a la semana.'''
        
        res = {}
        hours_per_day = 0 
        hours_per_week = 0

        calendar_obj = self.pool.get('resource.calendar')
        calendar = calendar_obj.browse(cr, uid, ids, context=context)[0]

        for hours in calendar.attendance_ids:
            hours_per_day = hours.hour_to - hours.hour_from 
            hours_per_week = hours_per_week + hours_per_day      
            
        res[calendar.id] = hours_per_week
        
        return res
    
    _columns = {
       'hours_work_per_week': fields.function(_compute_hours, string='Hours per week', type='float', store=False, method=True, help='Number of hours of work per week.'),
        }

resource_calendar()
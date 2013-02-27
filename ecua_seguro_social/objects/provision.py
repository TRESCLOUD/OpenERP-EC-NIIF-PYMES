
# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Carlos Lopez Mite                                                                           
# Copyright (C) 2012  Ecuadorenlinea.net                                 
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
import time
from datetime import date, datetime
from dateutil import relativedelta
from osv import osv
from osv import fields
import decimal_precision as dp
from tools.translate import _

class provisiones(osv.osv):
    def _calculate_total(self, cr, uid, ids, field_name, arg, context=None):
        res={}
        for provision in self.browse(cr, uid, ids, context=context):
            total=0.0
            for line in provision.line_ids:
                total+=line.total
            res[provision.id] = total
        return res
    '''
    Open ERP Model
    '''
    _name = 'hr.provision'
    _description = 'hr.provision'

    _columns = {
            'date_start': fields.date('Fecha Inicio' , readonly=True ,states={'draft': [('readonly', False)]}), 
            'date_end': fields.date('Fecha Final',readonly=True ,states={'draft': [('readonly', False)]}), 
            'date_move': fields.date('Fecha de Asiento Contable',required=True ,readonly=True ,states={'draft': [('readonly', False)]}), 
            'period_id':fields.many2one('account.period', 'Periodo', required=True, readonly=True ,states={'draft': [('readonly', False)]}), 
            'account_move_id':fields.many2one('account.move', 'Asiento Contable',readonly=True, required=False ),
            'rule_id':fields.many2one('hr.salary.rule', 'Provision a Pagar', domain=[('pay_to_other','=',True),('partner_id','!=',False)], required=True,readonly=True ,states={'draft': [('readonly', False)]}),
            'journal_id':fields.many2one('account.journal', 'Forma de Pago',domain=[('type','in',('cash','bank',))], required=True,readonly=True ,states={'draft': [('readonly', False)]}), 
            'line_ids':fields.one2many('hr.provision.line', 'provision_id', 'Provisiones Salariales', required=False,readonly=True),
            'total': fields.function(_calculate_total, method=True, type='float', string='Total'),
            'state':fields.selection([
                ('draft','Borrador'),
                ('open','Abierto'),
                ('done','Realizado'),
                ('cancel','Cancelado'),
                 ],    'Estado', select=True, readonly=True), 
        }
    _defaults = {
        'date_move': lambda *a: time.strftime('%Y-%m-%d'),  
        'date_start': lambda *a: time.strftime('%Y-%m-01'),
        'date_end': lambda *a: str(datetime.now() + relativedelta.relativedelta(months=+1, day=1, days=-1))[:10],
        'state': 'draft',  
        }
    _sql_constraints = [     ('period_rule_unique', 'unique (period_id,rule_id)', _('Ya existe un pago de la provision seleccionada en el periodo indicado. No puede pagar en el mismo periodo la misma provision. Verifique!!!!')),      ]
    def action_open(self,cr,uid,ids,context=None):
        self.compute(cr, uid, ids, context)
        self.write(cr, uid, ids, {'state':'open'})
        return True
    
    def action_cancel(self,cr,uid,ids,context=None):
        #Borramos las lineas anteriores
        provision=self.browse(cr,uid,ids[0],context) or None
        provision_line_obj=self.pool.get('hr.provision.line')
        old_lines=provision_line_obj.search(cr,uid,[('provision_id','=',provision.id)])
        move_id=provision.account_move_id and provision.account_move_id.id or None
        if move_id:
            self.pool.get('account.move').unlink(cr,uid,[move_id])
        if old_lines:
            provision_line_obj.unlink(cr,uid,old_lines,context)
        self.write(cr, uid, ids, {'state':'cancel'})
        return True
    def unlink(self, cr, uid, ids, context=None):
        if not context:
            context={}
        provision=self.browse(cr,uid,ids[0],context) or None
        move_id=provision.account_move_id and provision.account_move_id.id or None
        if move_id:
            self.pool.get('account.move').unlink(cr,uid,[move_id])
        #TODO: process before delete resource
        res = super(provisiones, self).unlink(cr, uid, ids, context)
        return res 
    
    def action_cancel_to_draft(self,cr,uid,ids,context=None):
        self.write(cr, uid, ids, {'state':'draft'})
        return True
    
    def compute(self, cr, uid, ids, context=None):
        if not context: context={}
        res={}
        employee_obj=self.pool.get('hr.employee')
        payslip_line_obj=self.pool.get('hr.payslip.line2')
        provision_line_obj=self.pool.get('hr.provision.line')
        employe_ids=employee_obj.search(cr,uid,[])
        for provision in self.browse(cr,uid,ids,context):
            #Borramos las lineas anteriores
            old_lines=provision_line_obj.search(cr,uid,[('provision_id','=',provision.id)])
            if old_lines:
                provision_line_obj.unlink(cr,uid,old_lines,context)
            for employee in employee_obj.browse(cr,uid,employe_ids):
                payslip_line_ids=payslip_line_obj.search(cr,uid,[('slip_id.date_from','>=',provision.date_start),('slip_id.date_to','<=',provision.date_end),('salary_rule_id','=',provision.rule_id.id),('employee_id','=',employee.id)])
                if payslip_line_ids:
                    vals_provision_line={
                                         'employee_id':employee.id,
                                         'payslip_line2_ids':[(6,0,payslip_line_ids)],
                                         'provision_id':provision.id
                                         }
                    provision_line_obj.create(cr,uid,vals_provision_line)           
        return True
    
    def pay_provision(self, cr, uid, ids, context=None):
        if not context: context={}
        res={}
        self.compute(cr, uid, ids, context)
        account_move_obj=self.pool.get('account.move')
        for provision in self.browse(cr,uid,ids,context):
            move_id=provision.account_move_id and provision.account_move_id.id or []
            if move_id:
                account_move_obj.unlink(cr,uid,[move_id])
            line_ids=[]
            if not provision.rule_id.account_debit or not provision.rule_id.account_credit:
                raise osv.except_osv(_('Accounting Error!'),_(u"No tiene configurada las cuentas de débito y crédito para la regla salarial '%s' !") % (provision.rule_id.name))
            name = _('Pago de %s') % (provision.rule_id.name)
            debit_line = (0, 0, {
                    'name': name,
                    'date': provision.date_move,
                    'account_id': provision.journal_id.default_debit_account_id.id,
                    'journal_id': provision.journal_id.id,
                    'period_id': provision.period_id.id,
                    'debit': provision.total,
                    'credit': 0,
                })
            credit_line = (0, 0, {
                    'name': name,
                    'date': provision.date_move,
                    'account_id': provision.rule_id.account_credit.id,
                    'journal_id': provision.journal_id.id,
                    'period_id': provision.period_id.id,
                    'debit': 0,
                    'credit': provision.total,
                })
            line_ids.append(debit_line)
            line_ids.append(credit_line)
            vals_move = {
                        'narration': name,
                        'date': provision.date_move,
                        'ref': "%s (%s) " %(name,provision.period_id.name),
                        'journal_id':provision.journal_id.id,
                        'period_id':provision.period_id.id,
                        'line_id': line_ids
                        }
            move_id = account_move_obj.create(cr, uid, vals_move, context=context)
            self.write(cr, uid, [provision.id], {
                                                 'account_move_id': move_id,
                                                 'state':'done'
                                                 })
        return True
provisiones()

class provision_line(osv.osv):
    
    '''
    Open ERP Model
    '''
    _name = 'hr.provision.line'
    _description = 'hr.provision.line'
    def _calculate_total(self, cr, uid, ids, field_name, arg, context=None):
        res={}
        for provision_line in self.browse(cr, uid, ids, context=context):
            total=0.0
            for line in provision_line.payslip_line2_ids:
                total+=abs(line.total)
            res[provision_line.id] = total
        return res
    _columns = {
            'employee_id':fields.many2one('hr.employee', 'Empleado', required=True), 
            'total': fields.function(_calculate_total, method=True, type='float', string='Total'),
            'payslip_line2_ids':fields.many2many('hr.payslip.line2', 'payslip_line2_provision_line_rel', 'provision_line_id', 'payslip_line2_id', 'Nominas'),
            'provision_id':fields.many2one('hr.provision', 'Provision', required=True,ondelete="cascade"),             
        }
    
provision_line()


# -*- encoding: utf-8 -*-
########################################################################
#                                                                       
# @authors: Christopher Ormaza                                                                           
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

from osv import osv
from osv import fields
import decimal_precision as dp
from tools.translate import _

class account_petty_cash_replenishment(osv.osv):
    '''
    Open ERP Model
    '''
    _name = 'account.petty.cash.replenishment'

    _columns = {
            'name':fields.char('Number', size=255, required=True),   
            'petty_cash_journal_id':fields.many2one('account.journal', 'Petty Cash Journal', required=True),         
            'bank_journal_id':fields.many2one('account.journal', 'Bank Cash Journal', required=True),
            'move_id':fields.many2one('account.move', 'Account Move', required=False),
            'move_ids':fields.many2many('account.move', 'cash_move_rel', 'petty_cash_id', 'move_id', 'Moves'),
            'create_date': fields.date('Date', readonly=True),
            'start_date': fields.date('Start Date', required=True), 
            'end_date': fields.date('End Date', required=True),
            'state':fields.selection([
                ('draft','Draft'),
                ('done','Done'),
                 ],    'State', select=True, readonly=True),
            'note': fields.text('Note'),
        }
    
    _defaults = {  
        'state': 'draft',
        }
    
    def onchange_data(self, cr, uid, ids, petty_cash_journal_id, start_date, end_date, context=None):
        if not context:
            context={}
        value = {}
        domain = {}
        if not petty_cash_journal_id or not start_date or not end_date:
            return {'value': value, 'domain': domain }
        domain['move_ids'] = [('journal_id','=',petty_cash_journal_id)]
        return {'value': value, 'domain': domain }
    
    def action_aprove(self, cr, uid, ids, context=None):
        return True

    def action_cance(self, cr, uid, ids, context=None):
        return True
    
account_petty_cash_replenishment()
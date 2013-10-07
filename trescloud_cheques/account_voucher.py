# -*- coding: utf-8 -*-
from osv import osv, fields
from tools.amount_to_text_en import amount_to_text
from tools.translate import _

class account_voucher(osv.osv):
    _inherit = 'account.voucher'
    
    def _get_journal(self, cr, uid, context=None):
        """
        Function to initialise the variable journal_id
        """
        if context is None:
            context = {}
        journal_obj = self.pool.get('account.journal')
        if 'invoice_id' in context:
            currency_id = self.pool.get('account.invoice').browse(cr, uid, context['invoice_id'], context=context).currency_id.id
            journal_id = journal_obj.search(cr, uid, [('currency', '=', currency_id)], limit=1, context=context)
            return journal_id and journal_id[0] or False
        if 'journal_id' in context:
            return context['journal_id']
        if not 'journal_id' in context and 'search_default_journal_id' in context:
            return context.get('search_default_journal_id')
        ttype = context.get('type', 'bank')
        if ttype in ('payment', 'receipt'):
            ttype = 'bank'
        if 'write_check' in context:
            res = journal_obj.search(cr, uid, [('allow_check_writing', '=', True)], limit=1, context=context)
        else:
            res = journal_obj.search(cr, uid, [('type', '=', ttype)], limit=1, context=context)
        return res and res[0] or False
    
    def _check_get(self, cr, uid, context=None):
        rs={}
        lista_check=[]
        if context:
            rs = {
                'mount':context['price'],
                'payee_name':context['partner_id'],
                'daily':"",
                'check_number':2,
                'current_date':context['current_date'],
                }   
            lista_check.append(rs)
        return lista_check

    
    def onchange_partner_id(self, cr, uid, ids, partner_id, journal_id, price, currency_id, ttype, date, context=None):
        """ Inherited - add amount_in_word in return value dictionary
            cr: cursor
            uid: user id
            ids: ids of account voucher
            partner_id: partner's id
            journal_id: journal's id
            price: price
            currency_id: id of currency using
            date: date
            context: context
        """
        rs={}
        lines={}
        lista_check=[]
        tres_check_obj=self.pool.get('check.check')
        
        default = super(account_voucher, self).onchange_partner_id(cr, uid, ids, partner_id, journal_id, price,
                                                                   currency_id, ttype, date, context=context)
        if 'value' in default:
            if journal_id:
               allow_check_writing = self.pool.get('account.journal').browse(cr, uid, journal_id, context=context).allow_check_writing
               default['value'].update({'allow_check': allow_check_writing})
               journal_obj = self.pool.get('account.journal')
               journal = journal_obj.browse(cr, uid, journal_id).type
               if journal == 'bank' :            
                  default['value'].update({'reference': "Cheque"})
               else:
                  default['value'].update({'reference': "Efectivo"})

        return default    
    
    _columns = {
        'amount_in_word': fields.char("Amount in word", size=128, readonly=True, states={'draft': [('readonly', False)]}),
        'allow_check': fields.boolean('Allow Check Writing'), # attrs does not support '.' format and fields.relates get the value when v save the record
        'chk_seq': fields.char("Check Number", size=64, readonly=True),
        'chk_status': fields.boolean("Check Status"),
        'check_ids': fields.one2many('check.check','check_id','Check lines',readonly=True, states={'draft':[('readonly',False)]})
        }
    
    _defaults = {
        'journal_id': _get_journal,
        'chk_status': False,
       # 'check_ids':_check_get,
        }
    
    def unlink(self, cr, uid, ids, context=None):
        """
        Función que impide la eliminación de vouchers que tengan cheques asociados.
        """
        
        check_obj = self.pool.get('check.check')
        id_check = check_obj.search(cr,uid,[('check_id','=',ids[0])])
        if id_check:
            check = check_obj.browse(cr,uid,id_check[0])       
            if check.check_id:
               raise osv.except_osv(_('Invalid action !'), _('Cannot delete Voucher(s) because there is a associated check. !'))
        return super(account_voucher, self).unlink(cr, uid, ids, context=context)    
    
    def action_move_line_create(self, cr, uid, ids, context=None):
        res=super(account_voucher, self).action_move_line_create( cr, uid, ids, context=context)
        i=0

        for obj_voucher in self.browse(cr, uid, ids, context=context):
            if len(obj_voucher.check_ids)>1:
                raise osv.except_osv(_('Warning'),
                _("Error while processing 'account.voucher' you can have only one check. !"))
            if obj_voucher.check_ids:
                if obj_voucher.check_ids[0].state not in ('printed','charged'):                    
                    raise osv.except_osv(_('Warning'),
                    _("Error while processing 'account.voucher'. You can only validate the payment with check in state printed or charged. !"))
                            
        return True 
    
account_voucher()
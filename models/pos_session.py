# -*- encoding: utf-8 -*-

from odoo import models, fields, api, _
import logging
from odoo.exceptions import UserError, ValidationError
import ast

class PosSession(models.Model):
    _inherit = 'pos.session'


    saldo_apartura = fields.Float('Saldo apertura', compute='_calcular_apertura_retiro_efectivo', store=True)
    total_efectivo_caja = fields.Float('Total efectivo caja', store=True)
    pagos_efectivo = fields.Float('Pagos efectivo',  compute='_calcular_pagos_efectivo', store=True)
    retiros_efectivo = fields.Float('Retiros efectivo', compute='_calcular_apertura_retiro_efectivo')

    @api.depends('cash_register_total_entry_encoding', 'cash_register_id.line_ids')
    def _calcular_apertura_retiro_efectivo(self):
        for sesion in self:
            total_saldo_apertura = 0
            efectivo_caja = 0
            retiros = 0
            if len(sesion.cash_register_id.line_ids):
                for linea in sesion.cash_register_id.line_ids:
                    if linea.amount < 0:
                        retiros += (linea.amount*-1)
                    if "Opening" in linea.payment_ref:
                        total_saldo_apertura += linea.amount
            sesion.saldo_apartura = total_saldo_apertura
            sesion.total_efectivo_caja = efectivo_caja
            sesion.retiros_efectivo = retiros

    @api.depends('order_ids','cash_register_total_entry_encoding')
    def _calcular_pagos_efectivo(self):
        for sesion in self:
            pago_ids = self.env['pos.payment'].search([('session_id','=',sesion.id)])
            efectivo = 0
            if pago_ids:
                for pago in pago_ids:
                    if pago.payment_method_id.name == "Efectivo":
                        efectivo += pago.amount

            sesion.pagos_efectivo = efectivo
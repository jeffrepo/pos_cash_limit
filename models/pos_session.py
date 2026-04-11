from odoo import models, fields, api


class PosSession(models.Model):
    _inherit = 'pos.session'

    saldo_apartura = fields.Float(
        'Saldo apertura',
        compute='_compute_cash_totals',
        store=True,
    )
    total_efectivo_caja = fields.Float(
        'Total efectivo caja',
        compute='_compute_cash_totals',
        store=True,
    )
    pagos_efectivo = fields.Float(
        'Pagos efectivo',
        compute='_compute_pagos_efectivo',
        store=True,
    )
    retiros_efectivo = fields.Float(
        'Retiros efectivo',
        compute='_compute_cash_totals',
        store=True,
    )

    @api.depends(
        'order_ids.payment_ids.amount',
        'order_ids.payment_ids.payment_method_id',
        'order_ids.payment_ids.payment_method_id.type',
    )
    def _compute_pagos_efectivo(self):
        for sesion in self:
            efectivo = 0.0
            for order in sesion.order_ids:
                for pago in order.payment_ids:
                    if pago.payment_method_id and pago.payment_method_id.type == 'cash':
                        efectivo += pago.amount or 0.0
            sesion.pagos_efectivo = efectivo

    @api.depends(
        'cash_register_balance_start',
        'statement_line_ids.amount',
        'pagos_efectivo',
    )
    def _compute_cash_totals(self):
        for sesion in self:
            retiros = 0.0
            for linea in sesion.statement_line_ids:
                if (linea.amount or 0.0) < 0:
                    retiros += abs(linea.amount)

            saldo_apertura = sesion.cash_register_balance_start or 0.0
            pagos_efectivo = sesion.pagos_efectivo or 0.0

            sesion.saldo_apartura = saldo_apertura
            sesion.retiros_efectivo = retiros
            sesion.total_efectivo_caja = saldo_apertura + pagos_efectivo - retiros

    def _load_pos_data_fields(self, config_id):
        fields = super()._load_pos_data_fields(config_id)
        fields += ['pagos_efectivo', 'retiros_efectivo', 'total_efectivo_caja', 'saldo_apartura','cash_register_balance_end']
        return fields

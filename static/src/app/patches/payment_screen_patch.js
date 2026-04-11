/** @odoo-module **/

import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { AlertDialog } from "@web/core/confirmation_dialog/confirmation_dialog";
import { PaymentScreen } from "@point_of_sale/app/screens/payment_screen/payment_screen";

patch(PaymentScreen.prototype, {
    async validateOrder(isForceValidate = false) {
        const order = this.currentOrder;
        const efectivoMaximo = Number(this.pos.config.efectivo_maximo || 0);
        const sesionId =
            order?.session_id?.id ||
            order?.session_id ||
            this.pos?.session?.id ||
            this.pos?.pos_session?.id;

        let pagoEfectivo = false;
        let ventaEfectivoActual = 0;
        const cambio = Math.abs(Number(order.change || 0));

        for (const line of order.payment_ids || []) {
            const method = line.payment_method_id;
            if (!method) {
                continue;
            }
            if (method.type === "cash") {
                pagoEfectivo = true;
                ventaEfectivoActual += Number(line.amount || 0);
            }
        }

        if (!pagoEfectivo && (order.payment_ids?.length || 0) >= 1 && cambio > 0) {
            this.dialog.add(AlertDialog, {
                title: _t("Error en pago"),
                body: _t("Monto de pago incorrecto"),
            });
            return;
        }

        if (!sesionId || !efectivoMaximo) {
            return await super.validateOrder(isForceValidate);
        }

        let sesion = [];
        try {
            sesion = await this.pos.data.call(
                "pos.session",
                "search_read",
                [[["id", "=", sesionId]], ["pagos_efectivo", "retiros_efectivo"]]
            );
        } catch (error) {
            this.dialog.add(AlertDialog, {
                title: _t("Error"),
                body: _t("No se pudo consultar la sesión actual."),
            });
            return;
        }

        if (!sesion || !sesion.length) {
            return await super.validateOrder(isForceValidate);
        }

        const pagosEfectivo = Number(sesion[0].pagos_efectivo || 0);
        const retirosEfectivo = Number(sesion[0].retiros_efectivo || 0);

        const efectivoActualSesion = pagosEfectivo - retirosEfectivo;
        const efectivoDespuesVenta = efectivoActualSesion + ventaEfectivoActual;

        // Si ya estaba en el límite antes de esta venta, bloquear
        if (efectivoActualSesion >= efectivoMaximo) {
            this.dialog.add(AlertDialog, {
                title: _t("Límite de efectivo"),
                body: _t("Ya se alcanzó el efectivo máximo permitido en caja. Debe realizar un retiro para continuar."),
            });
            return;
        }

        // Si con esta venta llega o supera el límite, avisar pero dejar continuar
        if (ventaEfectivoActual > 0 && efectivoDespuesVenta >= efectivoMaximo) {
            this.dialog.add(AlertDialog, {
                title: _t("Límite de efectivo alcanzado"),
                body: _t("Con esta venta se alcanzó el efectivo máximo permitido en caja. Después de confirmar, deberá realizar un retiro."),
            });
        }

        return await super.validateOrder(isForceValidate);
    },
});